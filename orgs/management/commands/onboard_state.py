# orgs/management/commands/onboard_state.py
# python manage.py onboard_state MN --lat 46.3 --lng -94.3 --zoom 6 --activate
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from orgs.models import State, Region

# abbr: (lat, lng, zoom)
STATE_VIEWS = {
    "AL": (32.81, -86.79, 7), "AK": (61.37, -152.40, 4), "AZ": (33.73, -111.43, 6),
    "AR": (34.97, -92.37, 7), "CA": (36.12, -119.68, 6), "CO": (39.06, -105.31, 7),
    "CT": (41.60, -72.76, 9), "DE": (39.32, -75.51, 9), "DC": (38.91, -77.04, 11),
    "FL": (27.77, -81.69, 6), "GA": (33.04, -83.64, 7), "HI": (21.09, -157.50, 7),
    "ID": (44.24, -114.48, 6), "IL": (40.35, -88.99, 6), "IN": (39.85, -86.26, 7),
    "IA": (42.01, -93.21, 7), "KS": (38.53, -96.73, 7), "KY": (37.67, -84.67, 7),
    "LA": (31.17, -91.87, 7), "ME": (44.69, -69.38, 7), "MD": (39.06, -76.80, 8),
    "MA": (42.23, -71.53, 8), "MI": (43.33, -84.54, 6), "MN": (45.69, -93.90, 6),
    "MS": (32.74, -89.68, 7), "MO": (38.46, -92.29, 7), "MT": (46.92, -110.45, 6),
    "NE": (41.13, -98.27, 7), "NV": (38.31, -117.06, 6), "NH": (43.45, -71.56, 8),
    "NJ": (40.30, -74.52, 8), "NM": (34.84, -106.25, 6), "NY": (42.17, -74.95, 7),
    "NC": (35.63, -79.81, 7), "ND": (47.53, -99.78, 7), "OH": (40.39, -82.76, 7),
    "OK": (35.57, -96.93, 7), "OR": (44.57, -122.07, 7), "PA": (40.59, -77.21, 7),
    "RI": (41.68, -71.51, 10), "SC": (33.86, -80.95, 7), "SD": (44.30, -99.44, 7),
    "TN": (35.75, -86.69, 7), "TX": (31.05, -97.56, 6), "UT": (40.15, -111.86, 6),
    "VT": (44.05, -72.71, 8), "VA": (37.77, -78.17, 7), "WA": (47.40, -121.49, 7),
    "WV": (38.49, -80.95, 7), "WI": (44.27, -89.62, 7), "WY": (42.76, -107.30, 7),
}

class Command(BaseCommand):
    help = "Load a state's regions, counties, and zip data. Safe to re-run."

    def add_arguments(self, parser):
        parser.add_argument("abbr")
        parser.add_argument("--lat", type=float)
        parser.add_argument("--lng", type=float)
        parser.add_argument("--zoom", type=int)
        parser.add_argument("--activate", action="store_true")

    def handle(self, *args, **o):
        try:
            state = State.objects.get(abbr=o["abbr"].upper())
        except State.DoesNotExist:
            raise CommandError(f"No State with abbr {o['abbr']}")
        
        abbr = o["abbr"].upper()
        default_lat, default_lng, default_zoom = STATE_VIEWS.get(abbr, (None, None, None))

        # Priority: command-line value > value already saved on the state > built-in default
        if o["lat"] is not None:
            state.map_center_lat = o["lat"]
        elif state.map_center_lat is None:
            state.map_center_lat = default_lat

        if o["lng"] is not None:
            state.map_center_lng = o["lng"]
        elif state.map_center_lng is None:
            state.map_center_lng = default_lng

        if o["zoom"] is not None:
            state.map_zoom = o["zoom"]
        elif state.map_zoom is None:
            state.map_zoom = default_zoom

        state.save()

        Region.objects.get_or_create(
            state=state, code="St",
            defaults={"name": "Statewide", "map_filename": ""},
        )
        call_command("load_county_fips", state.abbr, apply=True, create_missing=True)
        call_command("load_zip_county", state.abbr, apply=True, query_all=True)

        if o["activate"]:
            state.is_active = True
            state.save()

        self.stdout.write(
            f"{state.name}: {state.regions.count()} regions, "
            f"{state.counties.count()} counties, active={state.is_active}"
        )