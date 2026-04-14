from django.core.management.base import BaseCommand
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from django.db.models import Q
from orgs.models import Location


class Command(BaseCommand):
    help = "Geocode Location records that are missing latitude/longitude."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Update all locations, even if they already have latitude/longitude.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Only process this many locations.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be updated without saving.",
        )

    def handle(self, *args, **options):
        update_all = options["all"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        geolocator = Nominatim(user_agent="volunteer_map_app")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

        if update_all:
            qs = Location.objects.all()
        else:
            qs=Location.objects.filter(Q(latitude__isnull=True) | Q(longitude__isnull=True))

        if limit:
            qs = qs[:limit]

        total = qs.count() if hasattr(qs, "count") else len(qs)
        self.stdout.write(f"Processing {total} location(s)...")

        updated = 0
        skipped = 0
        failed = 0

        for loc in qs:
            parts = []

            if loc.loc_name:
                parts.append(loc.loc_name)
            if loc.city_name:
                parts.append(loc.city_name)
            if loc.county_id and loc.county_id.county_name:
                parts.append(f"{loc.county_id.county_name} County")
            if loc.state:
                parts.append(loc.state)
            else:
                parts.append("WI")

            parts.append("USA")
            query = ", ".join(parts)

            try:
                geo = geocode(query)

                if geo:
                    self.stdout.write(
                        f"FOUND: {loc.loc_name} -> {geo.latitude}, {geo.longitude}"
                    )

                    if not dry_run:
                        loc.latitude = geo.latitude
                        loc.longitude = geo.longitude
                        loc.save(update_fields=["latitude", "longitude"])

                    updated += 1
                else:
                    self.stdout.write(
                        self.style.WARNING(f"NO MATCH: {loc.loc_name} ({query})")
                    )
                    failed += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"ERROR: {loc.loc_name} ({query}) -> {e}")
                )
                failed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated: {updated}, Failed: {failed}, Skipped: {skipped}"
            )
        )