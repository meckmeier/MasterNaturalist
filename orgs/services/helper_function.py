import re
ADDRESS_MAP = {
    "street": "st",
    "st.": "st",
    "road": "rd",
    "avenue": "ave",
    "drive": "dr",
    "lane": "ln",
    "boulevard": "blvd",
    "court": "ct",
}

def normalize_text(val):
    if not val:
        return ""
    val = val.lower().strip()
    val = re.sub(r"\s+", " ", val)
    return (val or "").strip().lower()
    

def normalize_address(addr):
    if not addr:
        return ""

    addr = addr.lower().strip()
    addr = re.sub(r"[.,]", "", addr)

    for k, v in ADDRESS_MAP.items():
        addr = addr.replace(k, v)

    # remove unit info
    addr = re.sub(r"(apt|suite|ste|#)\s*\w+", "", addr)

    addr = re.sub(r"\s+", " ", addr)
   
    return (addr or "").strip().lower()

def normalize_url(url):
        if url:
            url = url.strip()
            if not url.startswith(("http://", "https://")):
                return "https://" + url
        return url

def build_location_fingerprint(*, org_id, loc_name, address=None, city_name=None, state="WI"):
    name = normalize_text(loc_name)
    address = normalize_address(address)
    city = normalize_text(city_name)
    state = normalize_text(state)

    if address:
        return f"addr|{name}|{address}|{city}|{state}"

    return f"org|{org_id}|{name}|{city}|{state}"
