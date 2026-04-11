# myapp/utils/zip_county.py
import csv
from pathlib import Path
from orgs.models import County

# Load ZIP → county name
ZIP_TO_COUNTY_NAME = {}
CSV_FILE = Path(__file__).parent / "zip_to_county.csv"
with CSV_FILE.open() as f:
    reader = csv.DictReader(f)
    for row in reader:
        ZIP_TO_COUNTY_NAME[row['ZIP']] = row['COUNTY']

# Load county name → county ID and county ID → region name
COUNTY_NAME_TO_ID = {}
COUNTY_ID_TO_REGION = {}
for county in County.objects.all():
    COUNTY_NAME_TO_ID[county.county_name] = county.id
    COUNTY_ID_TO_REGION[county.id] = county.region_name

# Lookup functions
def get_county_id_from_zip(zip_code):
    county_name = ZIP_TO_COUNTY_NAME.get(zip_code)
    
    if county_name:
        county_name = county_name.upper()
    else:
        county_name= None

    return county_name

def get_region_from_county_id(county_id):
    if county_id:
        region=COUNTY_ID_TO_REGION.get(county_id)
    else:
        region = None
    return region