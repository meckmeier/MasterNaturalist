import csv
import os
from decimal import Decimal
import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from orgs.models import State, County, ZipToCounty

HUD_URL = "https://www.huduser.gov/hudapi/public/usps"


class Command(BaseCommand):
    help = "Load ZIP -> county defaults from the HUD USPS crosswalk (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("states", nargs="+", help="State abbreviations, e.g. WI")
        parser.add_argument("--apply", action="store_true", help="Save changes")
        parser.add_argument("--all", action="store_true", dest="query_all",
                            help="Download HUD's full national file once and keep rows for the given states "
                                 "(catches border ZIPs whose mailing city is in a neighboring state)")

    def fetch(self, query, token):
        r = requests.get(
            HUD_URL, params={"type": 2, "query": query},
            headers={"Authorization": f"Bearer {token}"}, timeout=300,
        )
        if r.status_code != 200:
            raise CommandError(f"HUD request failed ({r.status_code}): {r.text[:200]}")
        data = r.json()["data"]
        return data["results"], f'{data["year"]} Q{data["quarter"]}'

    def handle(self, *args, **opts):
        token = os.environ.get("HUD_API_TOKEN")
        if not token:
            raise CommandError("HUD_API_TOKEN is not set. In this window run: set HUD_API_TOKEN=your-token")

        targets = {}
        for abbr in opts["states"]:
            st = State.objects.filter(abbr=abbr.upper()).first()
            if not st:
                raise CommandError(f"Unknown state: {abbr}")
            targets[st.fips] = st

        if opts["query_all"]:
            results, label = self.fetch("All", token)
        else:
            results, label = [], ""
            for st in targets.values():
                rows, label = self.fetch(st.abbr, token)
                results.extend(rows)

        # best county per (zip, state of the county)
        best, seen = {}, set()
        for row in results:
            geoid = str(row["geoid"]).zfill(5)
            zip5 = str(row["zip"]).zfill(5)
            if geoid[:2] not in targets or (zip5, geoid) in seen:
                continue
            seen.add((zip5, geoid))
            ratio = float(row["tot_ratio"] or 0)
            key = (zip5, geoid[:2])
            if key not in best or ratio > best[key][0]:
                best[key] = (ratio, geoid)

        counties = {
            c.fips: c
            for c in County.objects.filter(state__in=targets.values())
            .exclude(fips__isnull=True).exclude(fips="")
        }
        existing = {
            (z.zip, z.state_id): z
            for z in ZipToCounty.objects.filter(state__in=targets.values()).select_related("county")
        }

        to_create, to_update, same, ambiguous = [], [], 0, 0
        report, missing_fips, hud_keys = [], set(), set()

        for (zip5, sfips), (ratio, geoid) in sorted(best.items()):
            st = targets[sfips]
            hud_keys.add((zip5, st.pk))
            county = counties.get(geoid)
            if not county:
                missing_fips.add(geoid)
                continue
            share = Decimal(str(round(ratio, 4)))
            if ratio < 0.8:
                ambiguous += 1
            cur = existing.get((zip5, st.pk))
            if cur is None:
                to_create.append(ZipToCounty(zip=zip5, county=county, state=st, share=share))
            elif cur.county_id == county.pk:
                same += 1
                if cur.share is None:
                    cur.share = share
                    to_update.append(cur)
            else:
                report.append(("different", zip5, st.abbr, cur.county.county_name, county.county_name, share))

        for (zip5, st_pk), cur in existing.items():
            if (zip5, st_pk) not in hud_keys:
                report.append(("not_in_hud", zip5, cur.state.abbr, cur.county.county_name, "", ""))

        with open("zip_county_report.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["type", "zip", "state", "your_county", "hud_county", "hud_share"])
            w.writerows(report)

        self.stdout.write(f"\nHUD data: {label}")
        self.stdout.write(f"  ZIP/state combinations in HUD: {len(best)}")
        self.stdout.write(f"  Already match your table: {same}")
        self.stdout.write(f"  New ZIPs to add: {len(to_create)}")
        self.stdout.write(f"  Shares to fill in on existing rows: {len(to_update)}")
        self.stdout.write(f"  Differ from your table (not changed): {sum(1 for r in report if r[0] == 'different')}")
        self.stdout.write(f"  In your table but not in HUD: {sum(1 for r in report if r[0] == 'not_in_hud')}")
        self.stdout.write(f"  Ambiguous ZIPs (best county under 80%): {ambiguous}")
        if missing_fips:
            self.stdout.write(self.style.WARNING(
                f"  {len(missing_fips)} county FIPS codes not in your County table "
                f"(run load_county_fips first): {sorted(missing_fips)[:10]}"))
        self.stdout.write("  Details saved to zip_county_report.csv")

        if opts["apply"]:
            with transaction.atomic():
                ZipToCounty.objects.bulk_create(to_create, batch_size=1000)
                ZipToCounty.objects.bulk_update(to_update, ["share"], batch_size=1000)
            self.stdout.write(self.style.SUCCESS("  Saved."))
        else:
            self.stdout.write("  Dry run: nothing saved. Re-run with --apply.")