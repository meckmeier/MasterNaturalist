import re
import pandas as pd

FIELD_ALIASES = {
    "location_name": [
        "location",
        "site",
        "venue",
        "location_name",
    ],
    "start_date": [
        "date",
        "start",
        "start_date",
    ],
    "contact_email": [
        "email",
        "contact email",
        "contact_email",
    ],
    "activity_url": [
        "information_url",
    ],
    "time_description": [
        "times",
        "time"]
}


def field_normalize(value):
    if value is None:
        return ""

    value = str(value).strip().lower()

    # replace spaces and hyphens with underscores
    value = re.sub(r"[\s\-]+", "_", value)

    # remove anything not alphanumeric or underscore
    value = re.sub(r"[^a-z0-9_]", "", value)

    # collapse repeated underscores
    value = re.sub(r"_+", "_", value)

    return value.strip("_")

ALIAS_LOOKUP = {}

for model_field, aliases in FIELD_ALIASES.items():
    for alias in aliases:
        ALIAS_LOOKUP[field_normalize(alias)] = model_field

def build_mapping(post_data, columns):
    mapping = {}
    for col in columns:
        field = post_data.get(f"mapping_{col}")
        if field:
            mapping[field] = col
    return mapping


def build_dropdown_options(columns, field_names):
    IMPORT_ONLY_FIELDS = [ "online",]
    
    normalized_field_map = {field_normalize(f): f for f in field_names}

    dropdown_options = {}

    for col in columns:
        normalized_col = field_normalize(col)

        # First try an exact match
        preselected = normalized_field_map.get(normalized_col)

        # If not found, try aliases
        if preselected is None:
            preselected = ALIAS_LOOKUP.get(normalized_col)

        choices = field_names.copy()
        if preselected is None:
            choices = [""] + choices

        dropdown_options[col] = {
            "choices": choices,
            "preselected": preselected
        }

    return dropdown_options

def validate_mapping(mapping):
    errors = []

    required_fields = [
        "title",
        "activity_type",
    ]

    for field in required_fields:
        if not mapping.get(field):
            errors.append(f"Required field '{field}' was not mapped.")

    return errors

def build_default_mapping(columns, field_names):
    mapping = {}

    normalized_fields = {
        field_normalize(field): field
        for field in field_names
    }

    for col in columns:
        col = str(col).strip()

        if not col or col.lower().startswith("unnamed:"):
            continue

        normalized_col = field_normalize(col)

        # Exact match first
        field_name = normalized_fields.get(normalized_col)

        # Then alias match
        if field_name is None:
            field_name = ALIAS_LOOKUP.get(normalized_col)

        if field_name:
            mapping[field_name] = col

    return mapping