# utils.py
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from orgs.models import Location

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