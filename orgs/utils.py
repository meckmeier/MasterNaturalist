# utils.py
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

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