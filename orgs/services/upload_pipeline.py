# =========================
# 1. IMPORTS
# =========================
import pandas as pd
from orgs.models import RawLoadData, Pending_Location, Pending_Activity, Pending_Session
from orgs.services.zip_to_county import get_county_id_from_zip, get_region_from_county_id
from orgs.services.mapping import *


# =========================
# 2. NORMALIZATION HELPERS
# =========================

def normalize_bool(val):
    if val in [True, False]:
        return val
    if val is None:
        return None

    val = str(val).strip().lower()
    if val in ["y", "yes", "true", "1", "x"]:
        return True
    if val in ["n", "no", "false", "0"]:
        return False
    return None


def safe_str(val):
    if val is None:
        return None
    if isinstance(val, float):
        return None
    return str(val).strip()





# =========================
# 3. DOMAIN PROCESSING
# =========================

def process_row(row):
    has_url = bool(row.get("activity_url"))
    has_location = bool(row.get("location_name") or row.get("address"))

    if has_url and has_location:
        session_type = "b"
    elif has_url:
        session_type = "o"
    elif has_location:
        session_type = "i"
    else:
        session_type = None

    return {
        **row,
        "session_type": session_type,
        "county_id": get_county_id_from_zip(row.get("zip")),
    }


# =========================
# 4. VALIDATION
# =========================

def validate_row(row):
    errors = []

    if not row.get("title"):
        errors.append("Missing title")

    if row.get("state") and len(str(row["state"])) != 2:
        errors.append("Invalid state")

    return errors


# =========================
# 5. MAIN PIPELINE
# =========================

def run_upload_pipeline(upload, mapping):

    file = upload.file

    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file, engine="openpyxl")

    rows = df.to_dict(orient="records")
    results=[]
   
    for i, row in enumerate(rows):

        
        # 2a. COLUMN MAPPING
        clean = {}

        for field, col in mapping.items():
            clean[field] = row.get(col)

        # -------------------
        # 2. PROCESS
        # -------------------    
        processed = process_row(clean)

        # ----------------------------
        # 3. NORMALIZE
        # ----------------------------
        processed["no_cost"] = normalize_bool(processed.get("no_cost"))
        processed["online"] = normalize_bool(processed.get("online"))
        processed["ongoing"] = normalize_bool(processed.get("ongoing"))

        
        print("processed", processed)
        # ----------------------------
        # 4. VALIDATE
        # ----------------------------
        errors = validate_row(processed)
        print("error", errors)
        results.append({
                "row": i,
                "data": processed,
                "errors": errors,
                "is_valid": len(errors) == 0
            })

    return results
    
    