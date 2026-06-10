# orgs/services/location_matcher.py

from difflib import SequenceMatcher
from orgs.models import Location


def norm(value):
    return (value or "").strip().lower()


def similarity(a, b):
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def find_best_location_match(raw_row, org):
    raw_name = norm(raw_row.location_name)
    raw_address = norm(raw_row.address)
    raw_city = norm(raw_row.city)

    

    candidates = Location.objects.filter(
        deleted=False,
    )


    best_match = None
    best_score = 0
    best_reason = ""
  
    for loc in candidates:
        score = 0
        reason = []

        print(repr(raw_row.location_name))
        print(repr(loc.loc_name))

        # Strongest: address match
        if raw_address and norm(loc.address) == raw_address:
            score += 100
            reason.append("address match")

        # Exact name match
        if raw_name and norm(loc.loc_name) == raw_name:
            score += 80
            reason.append("exact name match")

        # Fuzzy name match
        name_score = similarity(raw_name, loc.loc_name)
        if name_score >= 0.90:
            score += 60
            reason.append(f"close name match ({name_score:.0%})")
        elif name_score >= 0.80:
            score += 40
            reason.append(f"possible name match ({name_score:.0%})")

        # City match helps, but should not decide alone
        if raw_city and norm(loc.city_name) == raw_city:
            score += 10
            reason.append("city match")

        if score > best_score:
            best_score = score
            best_match = loc
            best_reason = ", ".join(reason)

    # confidence threshold
    if best_score >= 50:
        return best_match, best_score, best_reason

    print("BEST MATCH:",best_match,"SCORE:",best_score,"REASON:",best_reason
)
    return None, best_score, best_reason