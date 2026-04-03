# utils.py
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from orgs.models import Location, Organization, Activity, Session, Profile
from datetime import datetime

geolocator = Nominatim(user_agent="volunteer_map_app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

def get_lat_lng(city, county=None, state="WI"):
    parts = [city]
    if county:
        parts.append(f"{county} County")
    parts.extend([state, "USA"])
    
    query = ", ".join(parts)
    location = geocode(query)
    
    if location:
        return location.latitude, location.longitude
    
    return None, None


"""
Temporary utility to update latitude/longitude for Locations
Call manually from Django shell:

>>> from yourapp.utils import update_latlng
>>> update_latlng()
"""

def update_latlng():
    # to call from the:  python manage.py shell
    # >>> from orgs.utils import update_latlng
    # >>> update_latlng()

    geolocator = Nominatim(user_agent="my_django_app")
    for loc in Location.objects.filter(latitude__isnull=True, longitude__isnull=True):
        address = f"{loc.loc_name}, {loc.city}, {loc.state}"
        geo = geolocator.geocode(address)
        if geo:
            loc.latitude = geo.latitude
            loc.longitude = geo.longitude
            loc.save()
            print(f"Updated {loc.loc_name}: {loc.latitude}, {loc.longitude}")
        else:
            print(f"Could not geocode {loc.loc_name}")

def update_new_fields():
    # to call from the:  python manage.py shell
    # >>> from orgs.utils import update_new_fields
    # >>> update_new_fields()
    default_date = datetime(2026, 3, 1)
    default_owner = Profile.objects.first()  # or some default profile
    for loc in Location.objects.all():
        if not loc.created_by:
            if not loc.owner:
                loc.created_by = default_owner
            else:
                loc.created_by = loc.owner
            loc.create_at = default_date
        if not loc.updated_by:
            loc.updated_by = loc.created_by
            loc.updated_at = default_date
        loc.save()
    for org in Organization.objects.all():
        if not org.created_by:
            if not org.owner:
                org.created_by = default_owner
            else:
                org.created_by = org.owner
            org.create_at = default_date
        if not org.updated_by:
            org.updated_by = org.created_by
            org.updated_at = default_date
        org.save()    
    for act in Activity.objects.all():
        if not act.created_by:
            if not act.owner:
                act.created_by = default_owner
            else:
                act.created_by = act.owner
            act.create_at = default_date
        if not act.updated_by:
            act.updated_by = act.created_by
            act.updated_at = default_date
        act.save()
    for sess in Session.objects.all():
        if not sess.created_by:
            sess.created_by = default_owner
            sess.create_at = default_date
        if not sess.updated_by:
            sess.updated_by = sess.created_by   
            sess.updated_at = default_date
        sess.save()