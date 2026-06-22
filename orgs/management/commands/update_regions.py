from django.core.management.base import BaseCommand
from orgs.models import Region, Location, Organization


class Command(BaseCommand):
    help = "Update region foreign keys"

    def handle(self, *args, **options):

        statewide = Region.objects.get(code="St")

        #
        # Update locations
        #
        loc_updates = 0

        for loc in Location.objects.select_related("county_id__region"):
            if loc.county_id and loc.county_id.region:
                if loc.region_id != loc.county_id.region_id:
                    loc.region = loc.county_id.region
                    loc.save(update_fields=["region"])
                    loc_updates += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{loc_updates} locations updated"
            )
        )

        #
        # Update organizations
        #
        org_updates = 0

        for org in Organization.objects.prefetch_related("locations__region"):

            region_ids = set(
                org.locations
                   .exclude(region__isnull=True)
                   .values_list("region_id", flat=True)
            )

            if len(region_ids) == 1:
                org.region_id = next(iter(region_ids))

            elif len(region_ids) > 1:
                org.region = statewide

            else:
                continue

            org.save(update_fields=["region"])
            org_updates += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{org_updates} organizations updated"
            )
        )