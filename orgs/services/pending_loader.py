from .validation.engine import ValidationEngine
from .validation.schemas import ACTIVITY_SCHEMA
from orgs.models import Pending_Activity

def load_to_pending(raw_rows):
    engine = ValidationEngine(ACTIVITY_SCHEMA)
    

    for row in raw_rows:
        cleaned, errors, warnings = engine.validate_row(row)
        
        PendingActivity.objects.create(
                raw_data=row,
                **cleaned,
                validation_errors=errors,
                validation_warnings=warnings,
                processing_status="pending"
            )

    
def old_load_logic()    
    rows = RawLoadData.objects.filter(upload_id=upload_id , status="valid")
    for row in rows:
        with transaction.atomic():       
            #print(f"Processing row {row.id}")
            # -----------------------------
            # Normalize
            # -----------------------------
            lkp_loc_name = normalize(row.location_name)
            lkp_city = normalize(row.city)
            lkp_address = normalize(row.address)
            lkp_title = normalize(row.title)
            
            
            # -----------------------------
            # 1. Try to find existing Pending_Location
            pending_location = Pending_Location.objects.filter(
                loc_name__iexact=lkp_loc_name,
                city_name__iexact=lkp_city,
                address__iexact=lkp_address
            ).first()

            if not pending_location:
                # 2. Try to match a real Location
                matched_location = Location.objects.filter(
                    loc_name__iexact=lkp_loc_name,
                    city_name__iexact=lkp_city
                ).first()

                # 3. Create Pending_Location
                if matched_location:
                    
                    pending_location = Pending_Location.objects.create(
                        loc_name=matched_location.loc_name,
                        city_name=matched_location.city_name,
                        address=matched_location.address,
                        zip_code=matched_location.zip_code,
                        state=matched_location.state,
                        real_location=matched_location,
                        processing_status="matched",
                        source_upload=upload_info,
                        org=upload_info.organization,
                        county_id=matched_location.county_id,
                        region_name = region_name
                    )
                else:
                    zip = row.zip  # or row.zip_code if that's what you have
                    county_id = get_county_id_from_zip(zip)
                    region_name = get_region_from_county_id(county_id)
                    pending_location = Pending_Location.objects.create(
                        loc_name=row.location_name,
                        city_name=row.city,
                        address=row.address,
                        zip_code=row.zip,
                        state=row.state,
                        processing_status="new",
                        source_upload=upload_info,
                        org=upload_info.organization,
                        county_id_id=county_id,
                        region_name = region_name
                    )
            
                  
            # 1. Try to find existing Pending_Activities
            pending_activity = Pending_Activity.objects.filter(
                title__iexact=lkp_title
            ).first()
            if pending_activity:
                pass
            else:
                if row.activity_type and row.activity_type[0].lower() == "v":
                    act_type="v"
                else:
                    act_type="t"
                pending_activity=Pending_Activity.objects.create(
                    title=row.title,
                    description=row.description,
                    activity_type=act_type,
                    date_description = row.date_description,
                    activity_url = row.activity_url,
                    no_cost = row.no_cost,
                    contact_email = row.contact_email,
                    created_by = request.user.profile,
                    updated_by = request.user.profile,
                    processing_status = "new",
                    org = upload_info.organization,
                    source_upload=upload_info,
                    time_commitment_id=None
                )     
            # 1. Try to find existing Pending Sessions
            date_val = row.date

            # Step 1: Check if it exists and is not NaN
            if pd.isna(date_val):
                date_val = None
            else:
                # Step 2: If string, parse to date
                if isinstance(date_val, str):
                    try:
                        date_val = datetime.strptime(date_val, "%Y-%m-%d").date()
                    except ValueError:
                        # fallback: try pandas parsing
                        date_val = pd.to_datetime(date_val).date()
                elif isinstance(date_val, pd.Timestamp):
                    date_val = date_val.date()
           

            pending_session=Pending_Session.objects.create(
                    session_format="b",
                    session_url=row.activity_url,
                    ongoing=,
                    start = date_val,
                    end = date_val,
                    activity = pending_activity,
                    location = pending_location,
                    created_by = request.user.profile,
                    updated_by = request.user.profile,
                    processing_status = "new",
              
                )  