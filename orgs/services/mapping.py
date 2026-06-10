import re
import pandas as pd

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


def build_mapping(post_data, columns):
    mapping = {}
    for col in columns:
        field = post_data.get(f"mapping_{col}")
        if field:
            mapping[field] = col
    return mapping


def build_dropdown_options(columns, field_names):
    normalized_field_map = {field_normalize(f): f for f in field_names}

    dropdown_options = {}

    for col in columns:
        normalized_col = field_normalize(col)
        preselected = normalized_field_map.get(normalized_col)

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
        field.lower().strip(): field
        for field in field_names
    }

    for col in columns:
        col = str(col).strip()

        # ignore blank / unnamed spreadsheet columns
        if not col or col.lower().startswith("unnamed:"):
            continue

        normalized_col = col.lower().strip()

        if normalized_col in normalized_fields:
            field_name = normalized_fields[normalized_col]
            mapping[field_name] = col

    return mapping