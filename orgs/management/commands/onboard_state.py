# orgs/management/commands/onboard_state.py
# python manage.py onboard_state MN --lat 46.3 --lng -94.3 --zoom 6 --activate
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from orgs.models import State, Region

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

        if o["lat"] is not None:
            state.map_center_lat = o["lat"]
        if o["lng"] is not None:
            state.map_center_lng = o["lng"]
        if o["zoom"] is not None:
            state.map_zoom = o["zoom"]
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