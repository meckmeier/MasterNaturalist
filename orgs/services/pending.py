

from unittest import result

from django.db import transaction
from django.utils import timezone
from orgs.models import (RawLoadData, Pending_Location, Pending_Activity, Pending_Session, Location, ZipToCounty)
from orgs.services.helper_function import get_county_region_from_zip

class PendingBuildResult:
    def __init__(self):
        self.created_locations = 0
        self.matched_locations = 0
        self.created_activities = 0
        self.created_sessions = 0
        self.errors = []
        self.warnings = []

def clean(value):
    return (value or "").strip()

#Main coordinator - RawLoadData rows -> pending locations/activities/sessions

def build_pending_for_upload(upload):
   
    result = PendingBuildResult()
    raw_rows = RawLoadData.objects.filter(upload=upload).exclude(status__in=["error", "skipped"]).order_by("row_number")
    print(f"Found {raw_rows.count()} raw rows for upload {upload.id}")

    if not raw_rows.exists():
        result.errors.append("No data rows found for this upload.")
        return result
    
    with transaction.atomic():
        for raw in raw_rows:
            print(f"Processing row {raw.row_number}...")
            try:
                build_pending_row(raw, upload, result)
            except Exception as e:
                print(f"Error processing row {raw.row_number}: {str(e)}")
                result.errors.append(
                    f"Row {raw.row_number}: Unexpected error: {str(e)}"
                )

    # rollback entire transaction if any row failed
    if result.errors:
        raise Exception("; ".join(result.errors))

    upload.status = "review_pending"
    upload.save()

    return result

#Process one row of RawLoadData: find or create pending location, build pending activity, build pending session.
def build_pending_row(raw_row, upload, result):
    org = upload.organization

    pending_location, done = get_or_create_pending_location(raw_row, org, upload)
        
    if pending_location and done=="matched":
        result.matched_locations += 1
    elif pending_location and done=="created":
        result.created_locations += 1
    
    
    pending_activity = build_pending_activity(raw_row, org, upload)
    if pending_activity:
        result.created_activities += 1
   

    build_pending_session(
        raw=raw_row,
        upload=upload,
        pending_activity=pending_activity,
        pending_location=pending_location,
        
    )
    result.created_sessions += 1
    

from orgs.services.helper_function import build_location_fingerprint

#Creates Pending_Location only if no real Location matched.
def get_or_create_pending_location(raw, org, upload):
    
    rawfingerprint = build_location_fingerprint(org_id=org.id,
        loc_name=clean(raw.location_name),
        address=clean(raw.address),
        city_name=clean(raw.city),
        state=clean(raw.state),)
    print (f"Built fingerprint: {rawfingerprint} for location: {raw.location_name}, {raw.address}, {raw.city}, {raw.state}")
    

    # 1. already created in this upload?
    pending_location = Pending_Location.objects.filter(
            source_upload=upload,
            fingerprint=rawfingerprint,
        ).first()
    print(f"Existing pending location for this row: {pending_location}")

    if pending_location:
        done="none"
        return pending_location, done
    
     # 2. exists in production?
    real_location = Location.objects.filter(
        fingerprint=rawfingerprint,
        deleted=False,
    ).first()

    if real_location:
        done="matched"
    else:
        done="created"

    try:
     # 3. always create at least ONE Pending_Location for this upload
        county, region = get_county_region_from_zip(raw.zip)

        if raw.session_format == "o":
            default_status = "skip"
        elif real_location is not None:
            default_status = "confirmed"
        else:
            default_status = "create"
        loc_name = str(raw.location_name or "")[:255]
        address = str(raw.address or "")[:255]
        city_name = str(raw.city or "")[:255]
        state = str(raw.state or "WI").strip().upper()
        pending_location = Pending_Location.objects.create(
            source_upload=upload,
            processing_status = default_status,
            org=org,
        
            loc_name=loc_name, #make sure only 255 characters
            address=address,
            city_name=city_name,
            state=state, #if blank just use WI
            zip_code=str(raw.zip or "")[:5], #only use the first 5 digits of zip code
            county_id = county ,
            region_name=region,
            fingerprint=build_location_fingerprint(org_id=org, loc_name=loc_name, address=address, city_name=city_name, state=state),
            created_at=timezone.now(),
            
            physical_location=True,

            # filled only if matched
            real_location=real_location,
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("FAILED ROW:", raw.row_number)
        raise
            
    return pending_location, done

    
# put in the real activities fields.
#check into this thing about the best way to handle existing locations in the process (add them to pending and mark them as real?)
#pending activity add
def build_pending_activity(raw, org, upload):
    try:

        pending_activity = Pending_Activity.objects.create(
            source_upload=upload,
            org=org,
            processing_status="valid",
            title=raw.title,
            description=raw.description,
            activity_type=raw.activity_type,
            activity_url=raw.activity_url,
            date_description=raw.date_description,
            time_description=raw.time_description,
            #time_commitment=raw.time_commitment,  
            has_cost=raw.has_cost,     
            contact_email=raw.contact_email,
            created_at=timezone.now(),
        )
    except Exception as e:
        raise Exception(f"Error creating pending activity: {str(e)}")
    return pending_activity

#Pending session
def build_pending_session(raw, pending_activity, pending_location,  upload):

    try:
        pending_session = Pending_Session.objects.create(
            source_upload=upload,

            activity=pending_activity,
            location=pending_location,
            session_format=raw.session_format[:1] if raw.session_format else "",
            
            ongoing=raw.ongoing,
            start=raw.start_date,
            end=raw.end_date,
            processing_status="valid",

            created_at=timezone.now(),
        )
    except Exception as e:
        raise Exception(f"Error creating pending session: {str(e)}")
    return pending_session