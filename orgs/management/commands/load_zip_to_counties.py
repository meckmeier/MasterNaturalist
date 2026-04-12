# orgs/management/commands/load_zip_counties.py
import csv
from django.core.management.base import BaseCommand
from orgs.models import ZipToCounty, County

class Command(BaseCommand):
    help = "Load zip-to-county mappings from CSV"

    def handle(self, *args, **options):
        path = "orgs/zip_to_county.csv"

        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            for row in reader:
                zip_code = str(row["ZIP"]).strip().zfill(5)
                county_name = row["COUNTY"].strip()
                county_name=county_name.upper()
                
                county = County.objects.filter(county_name__iexact=county_name).first()
                if not county:
                    self.stdout.write(self.style.WARNING(
                        f"No county match for {county_name} (zip {zip_code})"
                    ))
                    continue

                ZipToCounty.objects.update_or_create(
                    zip=zip_code,
                    defaults={"county": county}
                )

        self.stdout.write(self.style.SUCCESS("Zip data load complete"))