# orgs/services/validator.py

def validate_row(row):
    """
    Takes a CLEAN mapped row (dict)
    returns errors + warnings
    """

    errors = []
    warnings = []

    # ----------------------------
    # REQUIRED FIELDS
    # ----------------------------
    if not row.get("title"):
        errors.append("Missing title")

    if not row.get("city"):
        errors.append("Missing city")

    if not row.get("state"):
        errors.append("Missing state")

    # ----------------------------
    # STATE VALIDATION
    # ----------------------------
    state = row.get("state")
    if state and isinstance(state, str):
        if len(state) != 2:
            errors.append("State must be 2-letter code")

    # ----------------------------
    # ZIP VALIDATION
    # ----------------------------
    zip_code = row.get("zip")
    if zip_code:
        zip_str = str(zip_code).strip()
        if not zip_str.isdigit() or len(zip_str) not in [5, 9]:
            errors.append("Invalid zip code format")

    # ----------------------------
    # DATE VALIDATION (basic safe)
    # ----------------------------
    if row.get("date") is None:
        warnings.append("No date provided")

    # ----------------------------
    # BOOLEAN CLEANUP CHECKS
    # ----------------------------
    for field in ["no_cost", "online", "ongoing"]:
        val = row.get(field)
        if val is not None and not isinstance(val, (bool, int)):
            warnings.append(f"{field} is not boolean")

    # ----------------------------
    # RESULT
    # ----------------------------
    return {
        "errors": errors,
        "warnings": warnings,
        "is_valid": len(errors) == 0
    }