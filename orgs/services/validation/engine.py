from .validators import *
from .schemas import ACTIVITY_SCHEMA

VALIDATOR_MAP = {
    "required": validate_required,
    "date": validate_date,
    "boolean": validate_boolean,
    # add more here
}


class ValidationEngine:
    def __init__(self, schema):
        self.schema = schema

    def validate_row(self, row_dict):
        cleaned = {}
        errors = {}
        warnings = {}

        for field, rules in self.schema.items():
            value = row_dict.get(field)
            field_errors = []
            parsed_value = value

            for rule in rules:
                if isinstance(rule, tuple):
                    rule_name, *args = rule
                else:
                    rule_name, args = rule, []

                validator = VALIDATOR_MAP.get(rule_name)
                if not validator:
                    continue

                parsed_value, err = validator(parsed_value, *args)

                if err:
                    field_errors.append(err)

            if field_errors:
                errors[field] = field_errors
            else:
                cleaned[field] = parsed_value

        return cleaned, errors, warnings