
from django.db import transaction
from django.utils import timezone
from orgs.models import (RawLoadData, Pending_Location, Pending_Activity, Pending_Session, Location, ZipToCounty, EventCategory)
from orgs.services.helper_function import get_county_from_zip

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
    Pending_Session.objects.filter(source_upload=upload).delete()
    Pending_Activity.objects.filter(source_upload=upload).delete()
    Pending_Location.objects.filter(source_upload=upload).delete()
    
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


    return result

#Process one row of RawLoadData: find or create pending location, build pending activity, build pending session.
def build_pending_row(raw_row, upload, result):
    org = upload.organization
    
    if raw_row.session_format in ("o", "s"):
        pending_location= None
    else:

        pending_location, status = get_or_create_pending_location(
            raw=raw_row,
            org=upload.organization,
            upload=upload,
            result=result,
        )
            
        if status == "matched":
            result.matched_locations += 1
        elif status == "create":
            result.created_locations += 1
        elif status == "existing_pending":
            pass
    
    
    pending_activity = build_pending_activity(raw_row, org, upload)
    if pending_activity:
        build_pending_categories(pending_activity, raw_row)
        result.created_activities += 1
   

    build_pending_session(
        raw=raw_row,
        upload=upload,
        pending_activity=pending_activity,
        pending_location=pending_location,
        
    )
    result.created_sessions += 1
    

from orgs.services.helper_function import build_location_fingerprint
from orgs.services.location_matcher import find_best_location_match

#Creates Pending_Location only if no real Location matched.
def get_or_create_pending_location(raw, org, upload, result=None):
    matched_location = None
    score = 0
    reason = ""
    done = "created"

    loc_name = str(raw.location_name or "")[:255]
    address = str(raw.address or "")[:255]
    city_name = str(raw.city or "")[:255]
    state = str(raw.state or "WI").strip().upper()[:2]
    zip_code = str(raw.zip or "")[:5]

    fingerprint = build_location_fingerprint(
        org_id=org.id,
        loc_name=clean(loc_name),
        address=clean(address),
        city_name=clean(city_name),
        state=clean(state),
    )

    pending_location = Pending_Location.objects.filter(
        source_upload=upload,
        fingerprint=fingerprint,
    ).first()

    if pending_location:
        return pending_location, "existing_pending"

    # Online sessions do not need a real physical location match
    if raw.session_format in ("o", "s"):
        default_status = "skip"
        matched_location = None
        score = 0
        reason = "Location not required"
    else:
        matched_location, score, reason = find_best_location_match(raw, org)

        if matched_location:
            default_status = "matched"
        else:
            default_status = "create"

    try:
        county = get_county_from_zip(zip_code)

        pending_location = Pending_Location.objects.create(
            source_upload=upload,
            processing_status=default_status,
            org=org,

            loc_name=loc_name,
            address=address,
            city_name=city_name,
            state=state,
            zip_code=zip_code,
            county_id=county,
            region=county.region if county else None,
            fingerprint=fingerprint,

            real_location=matched_location,

            # if you added these fields:
            match_score=score,
            match_reason=reason,
        )

        return pending_location, done

    except Exception as e:
        if result is not None:
            result.errors.append(
                f"Row {raw.row_number}: Error creating pending location: {e}"
            )

        raise

    
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
            prerequisites=raw.prerequisites,
            raw_category_text=raw.categories,
            created_at=timezone.now(),
        )
        if raw.expire_date:
            pending_activity.expire_date = raw.expire_date
            pending_activity.save()

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

CATEGORY_SEPARATOR = ","

def build_pending_categories(pending_activity, raw_row):
    if not raw_row.categories:
        return
    category_text = (raw_row.categories or "").strip()
    category_text = (
            category_text
            .replace("“", "")
            .replace("”", "")
            .replace('"', "")
        )
    category_names = [
        c.strip()
        for c in category_text.split(CATEGORY_SEPARATOR)
        if c.strip()
    ]
    print("category_name", category_names)
    categories = EventCategory.objects.filter(
        cat_code__in=category_names
    )
    print("categories", categories)

    pending_activity.categories.set(categories)