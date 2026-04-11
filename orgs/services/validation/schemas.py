ACTIVITY_SCHEMA = {
    "activity_name": ["required"],
    "start_date": ["required", "date"],
    "ongoing": ["boolean"],
    "time_commitment": [("fuzzy_choice", ["Full Time", "Part Time"])],
}