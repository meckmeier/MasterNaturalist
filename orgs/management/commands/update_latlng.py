
from django.core.management.base import BaseCommand
from django.db.models import Q

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import (
    GeocoderRateLimited,
    GeocoderServiceError,
    GeocoderTimedOut,
    GeocoderUnavailable,
)

import logging

from orgs.models import Location


logger = logging.getLogger(__name__)


# Results at this level are too broad to be useful as a
# location for an activity.
BROAD_TYPES = {
    "country",
    "state",
    "county",
    "city",
    "town",
    "village",
    "municipality",
    "postcode",
}




class Command(BaseCommand):
    help = "Find coordinates for Location records."
    def add_arguments(self, parser):

        parser.add_argument(
            "--all",
            action="store_true",
            help="Process all locations, including those that already have coordinates.",
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
            help="Show results without saving coordinates.",
        )

    def handle(self, *args, **options):

        update_all = options["all"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        # ---------------------------------------------------------
        # Nominatim
        # ---------------------------------------------------------

        geolocator = Nominatim(
            user_agent="volunteer_map_app mary@eckmeier.com",
            timeout=10,
        )

        geocode = RateLimiter(
            geolocator.geocode,
            min_delay_seconds=2,
            max_retries=0,
            swallow_exceptions=False,
        )

        # ---------------------------------------------------------
        # Locations to process
        # ---------------------------------------------------------

        if update_all:
            locations = Location.objects.all()
        else:
            locations = Location.objects.filter(
                Q(latitude__isnull=True)
                | Q(longitude__isnull=True)
            )

        locations = locations.order_by("id")

        if limit:
            locations = locations[:limit]

        total = locations.count()

        self.stdout.write(
            f"Processing {total} location(s)..."
        )

        found = 0
        manual_review = 0
        skipped = 0

        # ---------------------------------------------------------
        # Process locations
        # ---------------------------------------------------------

        for loc in locations:

            name = (loc.loc_name or "").strip()
            address = (loc.address or "").strip()
            city = (loc.city_name or "").strip()
            state = (loc.state or "").strip() or "WI"
            county = (loc.county_id.county_name or "").strip() if loc.county_id else ""
            zip_code = (loc.zip_code or "").strip()

            self.stdout.write("")
            self.stdout.write("=" * 50)
            self.stdout.write(f"Location {loc.id}: {name}")

            # Need a name or address to search
            if not name and not address:
                self.stdout.write(
                    self.style.WARNING("  No name or address. Skipping.")
                )
                skipped += 1
                continue

            accepted = None
            accepted_method = None
            accepted_query = None

            # ---------------------------------------------------------
            # NAME SEARCH
            # ---------------------------------------------------------

            if name:

                if county:
                    query = f"{name}, {county} County, {state}, USA"
                else:
                    query = f"{name}, {state}, USA"

                self.stdout.write("  Trying name search:")
                self.stdout.write(f"    {query}")

                logger.info(
                    "GEOCODE NAME | loc_id=%s | query=%r",
                    loc.id,
                    query,
                )

                try:
                    candidates = geocode(
                        query,
                        exactly_one=False,
                        limit=5,
                    )

                    if not candidates:
                        self.stdout.write("  No name results.")

                    else:
                        self.stdout.write(
                            f"  Found {len(candidates)} candidate(s)."
                        )

                        for candidate in candidates:

                            raw = getattr(candidate, "raw", {}) or {}

                            result_class = raw.get("class")
                            result_type = raw.get("type")
                            display_name = raw.get("display_name", "")

                            self.stdout.write(
                                f"    Candidate: {display_name}"
                            )
                            self.stdout.write(
                                f"      Type: {result_class}/{result_type}"
                            )

                            # Ignore broad geographic results
                            if result_type in BROAD_TYPES:
                                continue

                            accepted = candidate
                            accepted_method = "name"
                            accepted_query = query
                            break

                        if accepted:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    "  Name result accepted."
                                )
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(
                                    "  No usable name result."
                                )
                            )

                except GeocoderRateLimited:

                    self.stdout.write(
                        self.style.ERROR(
                            "  Nominatim rate limit reached. Stopping."
                        )
                    )

                    manual_review += 1
                    continue

                except (
                    GeocoderTimedOut,
                    GeocoderServiceError,
                    GeocoderUnavailable,
                ) as e:

                    self.stdout.write(
                        self.style.ERROR(
                            f"  Geocoder error: {type(e).__name__}"
                        )
                    )

                    logger.warning(
                        "GEOCODE NAME ERROR | loc_id=%s | error=%s",
                        loc.id,
                        e,
                    )

            # =====================================================
            # 2. ADDRESS SEARCH
            #
            # Address + city + state + ZIP.
            #
            # NO COUNTY CHECK.
            #
            # The address is considered authoritative even if
            # its county differs from the stored county.
            # =====================================================

            if accepted is None and address:

                address_parts = [address]

                if city:
                    address_parts.append(city)

                address_parts.append(state)

                if zip_code:
                    address_parts.append(zip_code)

                address_parts.append("USA")

                query = ", ".join(address_parts)

                self.stdout.write(
                    "  Trying address search:"
                )
                self.stdout.write(
                    f"    {query}"
                )

                logger.info(
                    "GEOCODE ADDRESS | loc_id=%s | query=%r",
                    loc.id,
                    query,
                )

                try:

                    candidate = geocode(query)

                    if not candidate:

                        self.stdout.write(
                            "  No address result."
                        )

                    else:

                        raw = getattr(
                            candidate,
                            "raw",
                            {},
                        ) or {}

                        result_class = raw.get("class")
                        result_type = raw.get("type")
                        display_name = raw.get(
                            "display_name",
                            "",
                        )

                        self.stdout.write(
                            f"    Candidate: {display_name}"
                        )

                        self.stdout.write(
                            f"      Type: "
                            f"{result_class}/{result_type}"
                        )

                        # -------------------------------------------------
                        # NO COUNTY CHECK HERE.
                        # -------------------------------------------------

                        if result_type in BROAD_TYPES:

                            self.stdout.write(
                                self.style.WARNING(
                                    "  Address result is too broad."
                                )
                            )

                        else:

                            accepted = candidate
                            accepted_method = "address"
                            accepted_query = query

                            self.stdout.write(
                                self.style.SUCCESS(
                                    "  Address result accepted."
                                )
                            )

                except GeocoderRateLimited:

                    self.stdout.write(
                        self.style.ERROR(
                            "  Nominatim rate limit reached. "
                            "Stopping."
                        )
                    )

                    manual_review += 1
                    continue

                except (
                    GeocoderTimedOut,
                    GeocoderServiceError,
                    GeocoderUnavailable,
                ) as e:

                    self.stdout.write(
                        self.style.ERROR(
                            f"  Geocoder error: "
                            f"{type(e).__name__}"
                        )
                    )

                    logger.warning(
                        "GEOCODE ADDRESS ERROR | "
                        "loc_id=%s | error=%s",
                        loc.id,
                        e,
                    )

            # =====================================================
            # 3. SAVE RESULT
            # =====================================================

            if accepted:

                self.stdout.write(
                    self.style.SUCCESS(
                        f"FOUND: {name}\n"
                        f"  Method:  {accepted_method}\n"
                        f"  Query:   {accepted_query}\n"
                        f"  Match:   {accepted.address}\n"
                        f"  Coords:  "
                        f"{accepted.latitude}, "
                        f"{accepted.longitude}"
                    )
                )

                if not dry_run:

                    loc.latitude = accepted.latitude
                    loc.longitude = accepted.longitude

                    loc.save(
                        update_fields=[
                            "latitude",
                            "longitude",
                        ]
                    )

                found += 1

            # =====================================================
            # 4. MANUAL REVIEW
            # =====================================================

            else:

                self.stdout.write(
                    self.style.WARNING(
                        f"NO USABLE MATCH: {name}"
                    )
                )

                self.stdout.write(
                    "  --> Manual review required."
                )

                logger.warning(
                    "GEOCODE MANUAL REVIEW | "
                    "loc_id=%s | loc_name=%r",
                    loc.id,
                    name,
                )

                manual_review += 1

        # ---------------------------------------------------------
        # Summary
        # ---------------------------------------------------------

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Found: {found}, "
                f"Manual review: {manual_review}, "
                f"Skipped: {skipped}"
            )
        )
