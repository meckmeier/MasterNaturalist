
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

        geolocator = Nominatim(
            user_agent="volunteer_map_app mary@eckmeier.com"
        )

        geocode = RateLimiter(
            geolocator.geocode,
            min_delay_seconds=1,
            swallow_exceptions=False,
        )

        if update_all:
            qs = Location.objects.all()
        else:
            qs = Location.objects.filter(
                Q(latitude__isnull=True) | Q(longitude__isnull=True)
            )

        if limit:
            qs = qs[:limit]

        total = qs.count() if hasattr(qs, "count") else len(qs)

        self.stdout.write(f"Processing {total} location(s)...")

        logger.warning(
            "Starting geocode run. total=%s dry_run=%s update_all=%s",
            total,
            dry_run,
            update_all,
        )

        updated = 0
        skipped = 0
        failed = 0

        for loc in qs:

            loc_name = (loc.loc_name or "").strip()
            address = (loc.address or "").strip()
            city_name = (loc.city_name or "").strip()
            zip_code = (loc.zip_code or "").strip()
            state = (loc.state or "").strip() or "WI"

            # ---------------------------------------------------------
            # We need at least some identifying information.
            # ---------------------------------------------------------

            if not loc_name and not address and not city_name and not zip_code:
                self.stdout.write(
                    self.style.WARNING(
                        f"SKIP: {loc.id} has no location information."
                    )
                )
                skipped += 1
                continue

            # ---------------------------------------------------------
            # Build several possible queries.
            #
            # Name is first because nature locations often appear in
            # OpenStreetMap under their place name rather than their
            # mailing/street address.
            # ---------------------------------------------------------

            queries = []

            if loc_name:
                queries.append(
                    ("name + state", f"{loc_name}, {state}, USA")
                )

                if city_name:
                    queries.append(
                        (
                            "name + city + state",
                            f"{loc_name}, {city_name}, {state}, USA",
                        )
                    )

            if address:
                address_parts = [address]

                if city_name:
                    address_parts.append(city_name)

                address_parts.append(state)

                if zip_code:
                    address_parts.append(zip_code)

                address_parts.append("USA")

                queries.append(
                    ("address + city + state", ", ".join(address_parts))
                )

            # ---------------------------------------------------------
            # Try each query until we get a useful result.
            # ---------------------------------------------------------

            geo = None
            successful_method = None
            successful_query = None

            for method, query in queries:

                self.stdout.write(
                    f"Trying: {loc.id} | {loc_name}"
                )
                self.stdout.write(
                    f"  Method: {method}"
                )
                self.stdout.write(
                    f"  Query:  {query}"
                )

                logger.warning(
                    "GEOCODE QUERY | loc_id=%s | loc_name=%r | "
                    "city=%r | zip_code=%r | state=%r | "
                    "method=%r | query=%r",
                    loc.id,
                    loc_name,
                    city_name,
                    zip_code,
                    state,
                    method,
                    query,
                )

                try:
                    candidate = geocode(query)

                    if not candidate:
                        self.stdout.write("  No result.")
                        continue

                    # -------------------------------------------------
                    # Inspect the result.
                    # -------------------------------------------------

                    raw = getattr(candidate, "raw", {}) or {}

                    result_class = raw.get("class")
                    result_type = raw.get("type")
                    display_name = raw.get("display_name", "")

                    self.stdout.write(
                        f"  Candidate: {display_name}"
                    )
                    self.stdout.write(
                        f"  Type: {result_class}/{result_type}"
                    )

                    logger.warning(
                        "GEOCODE CANDIDATE | loc_id=%s | method=%r | "
                        "query=%r | class=%r | type=%r | "
                        "returned_address=%r | lat=%s | lng=%s",
                        loc.id,
                        method,
                        query,
                        result_class,
                        result_type,
                        display_name,
                        candidate.latitude,
                        candidate.longitude,
                    )

                    # -------------------------------------------------
                    # Reject results that are obviously too broad.
                    #
                    # We don't want a city, county, state, etc. becoming
                    # the coordinate for an actual location.
                    # -------------------------------------------------

                    broad_types = {
                        "country",
                        "state",
                        "county",
                        "city",
                        "town",
                        "village",
                        "municipality",
                        "postcode",
                    }

                    if result_type in broad_types:
                        self.stdout.write(
                            self.style.WARNING(
                                f"  Rejected broad result: "
                                f"{result_class}/{result_type}"
                            )
                        )
                        continue

                    # Good enough to use.
                    geo = candidate
                    successful_method = method
                    successful_query = query
                    break

                except (
                    GeocoderTimedOut,
                    GeocoderServiceError,
                    GeocoderUnavailable,
                ) as e:

                    self.stdout.write(
                        self.style.ERROR(
                            f"  GEOCODER ERROR: "
                            f"{type(e).__name__}: {e}"
                        )
                    )

                    logger.exception(
                        "GEOCODER ERROR | loc_id=%s | "
                        "method=%r | query=%r | "
                        "error_type=%s | error=%s",
                        loc.id,
                        method,
                        query,
                        type(e).__name__,
                        e,
                    )

                    # Try the next query.
                    continue

                except Exception as e:

                    self.stdout.write(
                        self.style.ERROR(
                            f"  UNEXPECTED ERROR: "
                            f"{type(e).__name__}: {e}"
                        )
                    )

                    logger.exception(
                        "UNEXPECTED GEOCODE ERROR | loc_id=%s | "
                        "method=%r | query=%r | "
                        "error_type=%s | error=%s",
                        loc.id,
                        method,
                        query,
                        type(e).__name__,
                        e,
                    )

                    # Try the next query.
                    continue

            # ---------------------------------------------------------
            # We found a usable result.
            # ---------------------------------------------------------

            if geo:

                self.stdout.write(
                    self.style.SUCCESS(
                        f"FOUND: {loc.loc_name}\n"
                        f"  Method:  {successful_method}\n"
                        f"  Query:   {successful_query}\n"
                        f"  Match:   {geo.address}\n"
                        f"  Coords:  {geo.latitude}, {geo.longitude}"
                    )
                )

                logger.warning(
                    "GEOCODE MATCH | loc_id=%s | method=%r | "
                    "query=%r | lat=%s | lng=%s | "
                    "returned_address=%r",
                    loc.id,
                    successful_method,
                    successful_query,
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
                    self.style.WARNING(
                        f"NO USABLE MATCH: {loc.loc_name}"
                    )
                )

                logger.warning(
                    "GEOCODE NO USABLE MATCH | loc_id=%s | "
                    "loc_name=%r",
                    loc.id,
                    loc_name,
                )

                failed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated: {updated}, "
                f"Failed: {failed}, "
                f"Skipped: {skipped}"
            )
        )

        logger.warning(
            "Finished geocode run. updated=%s failed=%s skipped=%s",
            updated,
            failed,
            skipped,
        )
