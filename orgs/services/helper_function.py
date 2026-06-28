from datetime import date, timedelta
import re
from difflib import SequenceMatcher


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

def default_expire_date():
    return date.today() + timedelta(days=365)

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

def normalize_zip_code(value):
    """
    Convert raw zip input into a clean 5-digit ZIP string.
    Returns None if the value cannot be normalized.
    """

    if value is None:
        return None

    value = str(value).strip()

    if not value:
        return None

    # Handle Excel/pandas-style values like 53217.0
    if value.endswith(".0"):
        value = value[:-2]

    # Handle ZIP+4
    if "-" in value:
        value = value.split("-")[0].strip()

    # Keep only digits
    value = "".join(ch for ch in value if ch.isdigit())

    if not value:
        return None

    # Pad leading zero ZIPs if needed
    if len(value) < 5:
        value = value.zfill(5)

    # Use only the first 5 digits
    value = value[:5]

    if len(value) != 5:
        return None

    return value


def get_county_from_zip(zip_code):
    from orgs.models import ZipToCounty

    zip_code = normalize_zip_code(zip_code)

    if not zip_code:
        return None

    try:
        zip_row = (
            ZipToCounty.objects
            .select_related("county__region")
            .get(zip=zip_code)
        )
    except ZipToCounty.DoesNotExist:
        return None

    return zip_row.county


def normalize_location_name(name):
    if not name:
        return ""

    name = name.lower().strip()

    replacements = {
        "&": "and",
        " ctr": " center",
        " ctr.": " center",
        " natl": " national",
        " natl.": " national",
        " nature ctr": " nature center",
        " inc": "",
        " inc.": "",
        ",": "",
        ".": "",
        "-": " ",
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    return " ".join(name.split())


def similarity(a, b):
    return SequenceMatcher(
        None,
        normalize_location_name(a),
        normalize_location_name(b)
    ).ratio()

def normalize_address_key(loc):
    parts = [
        loc.address,
        loc.city_name,
        loc.state,
        loc.zip_code,
    ]

    return "|".join(
        str(part).lower().strip()
        for part in parts
        if part
    )