from django.core.management.base import BaseCommand
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from django.db.models import Q
import logging
from geopy.exc import GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable
from orgs.models import Location

logger = logging.getLogger(__name__)

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

        geolocator = Nominatim(user_agent="volunteer_map_app mary@eckmeier.com")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, swallow_exceptions=False)

        if update_all:
            qs = Location.objects.all()
        else:
            qs=Location.objects.filter(Q(latitude__isnull=True) | Q(longitude__isnull=True))

        if limit:
            qs = qs[:limit]

        total = qs.count() if hasattr(qs, "count") else len(qs)
        self.stdout.write(f"Processing {total} location(s)...")
        logger.warning("Starting geocode run. total=%s dry_run=%s update_all=%s", total, dry_run, update_all)

        updated = 0
        skipped = 0
        failed = 0

        for loc in qs:
            loc_name = (loc.loc_name or "").strip()
            city_name = (loc.city_name or "").strip()
            zip_code = (loc.zip_code or "").strip()
            state = (loc.state or "").strip()

            parts = []

            if loc.city_name:
                parts.append(city_name)
            if loc.zip_code:
                parts.append(zip_code)
            if loc.state:
                parts.append(state)
            else:
                parts.append("WI")

            parts.append("USA")
            query = ", ".join(parts)
            self.stdout.write(f"Trying: {loc.id} | {query}")
            logger.warning(
                "GEOCODE QUERY | loc_id=%s | loc_name=%r | city=%r | zip_code=%r | state=%r | query=%r",
                loc.id,
                city_name,
                zip_code,
                state,
                query,
            )

            try:
                geo = geocode(query)

                if geo:
                    self.stdout.write(
                        f"FOUND: {loc.loc_name} -> {geo.latitude}, {geo.longitude}"
                    )
                    logger.warning(
                        "GEOCODE MATCH | loc_id=%s | query=%r | lat=%s | lng=%s | returned_address=%r",
                        loc.id,
                        query,
                        geo.latitude,
                        geo.longitude,
                        getattr(geo, "address", None),
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
                    logger.warning(
                        "GEOCODE NO MATCH | loc_id=%s | query=%r",
                        loc.id,
                        query,
                    )
                    failed += 1

            except (GeocoderTimedOut, GeocoderServiceError, GeocoderUnavailable) as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"GEOCODER ERROR: {loc_name or '[no name]'} ({query}) -> {type(e).__name__}: {e}"
                    )
                )
                logger.exception(
                    "GEOCODER ERROR | loc_id=%s | query=%r | error_type=%s | error=%s",
                    loc.id,
                    query,
                    type(e).__name__,
                    e,
                )
                failed += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"UNEXPECTED ERROR: {loc_name or '[no name]'} ({query}) -> {type(e).__name__}: {e}"
                    )
                )
                logger.exception(
                    "UNEXPECTED GEOCODE ERROR | loc_id=%s | query=%r | error_type=%s | error=%s",
                    loc.id,
                    query,
                    type(e).__name__,
                    e,
                )
                failed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated: {updated}, Failed: {failed}, Skipped: {skipped}"
            )
        )
        logger.warning(
            "Finished geocode run. updated=%s failed=%s skipped=%s",
            updated,
            failed,
            skipped,
        )