import csv
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from orgs.models import Location, Organization, County, normalize_text


class Command(BaseCommand):
    help = "Load locations from a CSV file into the Location table"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to the CSV file")
        parser.add_argument("org_name", type=str, help="Exact Organization name to attach locations to")
    

    
    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        org_name = options["org_name"]

        try:
            org = Organization.objects.get(org_name=org_name)
        except Organization.DoesNotExist:
            raise CommandError(f'Organization "{org_name}" does not exist.')

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            required_cols = [
                "name", "address", "city", "state", "zip",
                "county", "lat", "lng", "url", "description"
            ]
            missing = [col for col in required_cols if col not in reader.fieldnames]
            if missing:
                raise CommandError(f"CSV is missing required columns: {missing}")

            for row_num, row in enumerate(reader, start=2):
                name = (row.get("name") or "").strip()
                address = (row.get("address") or "").strip()
                city = (row.get("city") or "").strip()
                state = (row.get("state") or "").strip()
                zip_code = (row.get("zip") or "").strip()[:5]
                county_name = (row.get("county") or "").strip()
                description = (row.get("description") or "").strip()
                url = (row.get("url") or "").strip()
                lat_raw = (row.get("lat") or "").strip()
                lng_raw = (row.get("lng") or "").strip()

                if not name:
                    self.stdout.write(self.style.WARNING(f"Row {row_num}: skipped, missing name"))
                    skipped_count += 1
                    continue

                try:
                    county = County.objects.get(county_name__iexact=county_name)
                except County.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Row {row_num}: skipped, county "{county_name}" not found for "{name}"'
                        )
                    )
                    skipped_count += 1
                    continue

                try:
                    lat = Decimal(lat_raw) if lat_raw else None
                    lng = Decimal(lng_raw) if lng_raw else None
                except Exception:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Row {row_num}: skipped, bad lat/lng for "{name}" ({lat_raw}, {lng_raw})'
                        )
                    )
                    skipped_count += 1
                    continue

                defaults = {
                    "org": org,
                    "location_about": description,
                    "loc_name": name,
                    "address":address,
                    "city_name":city,
                    "state":state,
                    "county_id": county,
                    "region_name": county.region_name,
                    "zip_code": zip_code,
                    "latitude": lat,
                    "longitude": lng,
                    "org_loc_url": url,
                }

                fingerprint = "|".join([
                            normalize_text(name),
                            normalize_text(address),
                            normalize_text(city),
                            normalize_text(state),
                        ])
                
                self.stdout.write(self.style.WARNING(
                        f"Fingerprint for {fingerprint})"))
                # Adjust lookup fields if you want a different uniqueness rule
                with transaction.atomic():
                    location, created = Location.objects.update_or_create(
                        fingerprint=fingerprint,
                        defaults=defaults,
                    )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}"
        ))