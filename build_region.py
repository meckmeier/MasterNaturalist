import json
import os
import django

from shapely.geometry import shape, mapping
from shapely.ops import unary_union

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MasterNaturalist.settings")
django.setup()

from orgs.models import County


# ---------------------------------------------------
# Load county -> region mapping from Django
# ---------------------------------------------------

county_regions = {
    c.county_name.upper(): c.region.code
    for c in County.objects.select_related("region")
    if c.region
}

print(f"Loaded {len(county_regions)} county mappings")


# ---------------------------------------------------
# Load county geojson
# ---------------------------------------------------

with open(
    "orgs/static/orgs/geo/gz_2010_us_050_00_500k.json",
    encoding="latin-1"
) as f:
    data = json.load(f)

print(f"Loaded {len(data['features'])} features")


# ---------------------------------------------------
# Collect county geometries by region
# ---------------------------------------------------

region_geoms = {}

for feature in data["features"]:

    props = feature["properties"]

    if props.get("STATE") != "55":
        continue

    county_name = props["NAME"].upper()

    region = county_regions.get(county_name)

    if not region:
        print(f"Missing region for {county_name}")
        continue

    geom = shape(feature["geometry"])

    region_geoms.setdefault(region, []).append(geom)


# ---------------------------------------------------
# Merge counties into region polygons
# ---------------------------------------------------

features = []

for region_code, geoms in region_geoms.items():

    merged = unary_union(geoms)

    features.append({
        "type": "Feature",
        "properties": {
            "region": region_code
        },
        "geometry": mapping(merged)
    })

    print(
        f"Built region {region_code} "
        f"from {len(geoms)} counties"
    )


# ---------------------------------------------------
# Save output
# ---------------------------------------------------

region_geojson = {
    "type": "FeatureCollection",
    "features": features
}

outfile = "orgs/static/orgs/geo/wi_regions.geojson"

with open(outfile, "w", encoding="utf-8") as f:
    json.dump(region_geojson, f)

print(f"\nSaved {outfile}")