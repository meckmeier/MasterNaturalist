import os
import re
import requests
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from orgs.models import State, County

CENSUS_URL = "https://api.census.gov/data/2020/dec/pl"


def norm(name):
    n = name.lower().replace(".", "").replace("'", "").replace("’", "")
    n = re.sub(r"\bsaint\b", "st", n)
    n = re.sub(r"\b(city and borough|census area|municipality|borough|parish|county)\b", "", n)
    return re.sub(r"[^a-z0-9]", "", n)


class Command(BaseCommand):
    help = "Fill County.fips from the Census Bureau's county list (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("states", nargs="+", help="State abbreviations, e.g. WI")
        parser.add_argument("--apply", action="store_true", help="Save changes")
        parser.add_argument("--create-missing", action="store_true",
                            help="Create County rows for Census counties with no match (for onboarding a new state)")

    def handle(self, *args, **opts):
        for abbr in opts["states"]:
            st = State.objects.filter(abbr=abbr.upper()).first()
            if not st:
                raise CommandError(f"Unknown state: {abbr}")

            params = {"get": "NAME", "for": "county:*", "in": f"state:{st.fips}"}
            key = os.environ.get("CENSUS_API_KEY")
            if not key:
                raise CommandError("CENSUS_API_KEY is not set. In this window run: set CENSUS_API_KEY=your-key")
            params["key"] = key
            r = requests.get(CENSUS_URL, params=params, timeout=60)
            
            if r.status_code != 200:
                raise CommandError(f"Census request failed ({r.status_code}): {r.text[:200]}")

            try:
                rows = r.json()[1:]  # first row is the header
            except ValueError:
                raise CommandError(
                    f"Census did not return JSON. Status {r.status_code}, "
                    f"type {r.headers.get('content-type')}, body starts: {r.text[:300]!r}"
                )
            
            census = {sfp + cfp: name.rsplit(",", 1)[0] for name, sfp, cfp in rows}

            existing = list(County.objects.filter(state=st))
            by_norm = {}
            for c in existing:
                by_norm.setdefault(norm(c.county_name), []).append(c)

            to_set, matched_pks, unmatched_census = [], set(), []
            for fips, short in sorted(census.items()):
                hits = by_norm.get(norm(short), [])
                if len(hits) == 1:
                    matched_pks.add(hits[0].pk)
                    if hits[0].fips != fips:
                        to_set.append((hits[0], fips))
                else:
                    unmatched_census.append((fips, short))
            unmatched_db = [c for c in existing if c.pk not in matched_pks]

            self.stdout.write(f"\n{st.name}: {len(census)} Census counties, {len(existing)} in your table")
            self.stdout.write(f"  FIPS to fill in: {len(to_set)}")
            self.stdout.write(f"  Census counties with no match in your table: {len(unmatched_census)}")
            for fips, short in unmatched_census:
                self.stdout.write(f"    {fips} {short}")
            self.stdout.write(f"  Your counties with no match in Census: {len(unmatched_db)}")
            for c in unmatched_db:
                self.stdout.write(f"    {c.county_name}")

            if opts["apply"]:
                with transaction.atomic():
                    for c, fips in to_set:
                        c.fips = fips
                        c.save(update_fields=["fips"])
                    if opts["create_missing"]:
                        for fips, short in unmatched_census:
                            County.objects.create(
                                state=st, fips=fips,
                                county_name=re.sub(r"\s+County$", "", short),
                            )
                self.stdout.write(self.style.SUCCESS("  Saved."))
            else:
                self.stdout.write("  Dry run: nothing saved. Re-run with --apply.")