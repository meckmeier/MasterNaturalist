from django.db import transaction
from django.utils import timezone

from orgs.models import (
    ActivityUpload,
    Pending_Location,
    Pending_Activity,
    Pending_Session,
    Location,
    Activity,
    RawLoadData,
    Session,
)


@transaction.atomic
def publish_pending_upload(upload_id, user):
    upload = ActivityUpload.objects.select_for_update().get(id=upload_id)
    print("publish pending upload", upload)
    

    # 1. Resolve/create locations first
    pending_locations = Pending_Location.objects.filter(
        source_upload_id=upload.id
    ).exclude(
        processing_status__in=["skip", "merged"]
    )
    print("pending count", pending_locations.count())

    for pending_loc in pending_locations:
        if pending_loc.real_location:
            # Already matched to existing location
            pending_loc.processing_status = "matched"
            pending_loc.save(update_fields=[ "processing_status"])

            continue

        real_location = Location.objects.create(
            org=pending_loc.org,
            loc_name=pending_loc.loc_name,
            physical_location=pending_loc.physical_location,
            address=pending_loc.address,
            city_name=pending_loc.city_name,
            state=pending_loc.state,
            zip_code=pending_loc.zip_code,
            county_id=pending_loc.county_id,
            region_name=pending_loc.region_name,
            org_loc_url=pending_loc.org_loc_url,
            location_about=pending_loc.location_about,
            contact_email=pending_loc.contact_email,
            latitude=pending_loc.latitude,
            longitude=pending_loc.longitude,
            created_by=user,
            updated_by=user,
            source_upload=upload,
        )
        
        pending_loc.real_location = real_location
        pending_loc.processing_status = "created"
        pending_loc.save(update_fields=["real_location", "processing_status"])

    # 2. Create activities
    pending_activities = Pending_Activity.objects.filter(
        source_upload_id=upload.id
    ).exclude(
        processing_status="skip"
    )

    pending_to_real_activity = {}

    for pending_activity in pending_activities:
        real_activity = Activity.objects.create(
            org=pending_activity.org,
            title=pending_activity.title,
            description=pending_activity.description,
            activity_type=pending_activity.activity_type,
            date_description=pending_activity.date_description,
            time_description=pending_activity.time_description,
            activity_url=pending_activity.activity_url,
            contact_email=pending_activity.contact_email,
            has_cost=pending_activity.has_cost,
            owner=user,
            created_by=user,
            updated_by=user,
            source_upload=upload,
        )

        # If categories are many-to-many
        real_activity.categories.set(pending_activity.categories.all())

        #pending_activity.real_activity = real_activity  # only if you have this field
        
        

        pending_to_real_activity[pending_activity.id] = real_activity

    # 3. Create sessions
    pending_sessions = Pending_Session.objects.select_related(
        "location",
        "activity",
    ).filter(
        source_upload_id=upload.id
    ).exclude(
        processing_status="skip"
    )

    for pending_session in pending_sessions:
        real_activity = pending_to_real_activity.get(pending_session.activity_id)

        if not real_activity:
            continue

        real_location = None

        if pending_session.location:
            real_location = pending_session.location.real_location

        
        Session.objects.create(
            activity=real_activity,
            location=real_location,
            session_format=pending_session.session_format,
            start=pending_session.start,
            end=pending_session.end,
            ongoing=pending_session.ongoing,
            created_by=user,
            updated_by=user,
            source_upload=upload,
        )

        
        
    # 4. Mark upload complete
  
    upload.published_at = timezone.now()
    upload.published_by = user
    upload.locations_created = Location.objects.filter(source_upload=upload).count()
    upload.activities_created = Activity.objects.filter(source_upload=upload).count()
    upload.sessions_created = Session.objects.filter(source_upload = upload).count()
    upload.locations_matched = Pending_Location.objects.filter(source_upload=upload, processing_status="matched").count()
    upload.locations_skipped = Pending_Location.objects.filter(source_upload=upload, processing_status="skip").count()
    upload.locations_merged = Pending_Location.objects.filter(source_upload=upload, processing_status="merged").count()
    upload.activities_skipped = Pending_Activity.objects.filter(source_upload=upload, processing_status="skip").count()
    upload.sessions_skipped = Pending_Session.objects.filter(source_upload=upload, processing_status="skip").count()
    upload.sessions_created = Session.objects.filter(source_upload=upload).count()
    upload.status="published"
    upload.save(update_fields=[ "status", "published_at", "published_by"
                               , "locations_created", "locations_merged","locations_skipped", "locations_matched"
                               ,"activities_created","activities_skipped" 
                               , "sessions_created", "sessions_skipped"])

    # cleanup staging tables
    #Pending_Session.objects.filter(source_upload_id=upload_id).delete()
    #Pending_Activity.objects.filter(source_upload_id=upload_id).delete()
    #Pending_Location.objects.filter(source_upload_id=upload_id).delete()
    #RawLoadData.objects.filter(upload_id=upload_id).delete()
    
    return upload