# services/csv_importer.py
import re
import pandas as pd
from datetime import datetime, date
from orgs.models import RawLoadData
import traceback
import io

class CSVImporter:
    def __init__(self, upload, mapping=None):
        self.upload = upload
        self.mapping = mapping or {}  # e.g., {"Event Title": "title"}
        self.errors = []
        self.warnings =[]
        self.df = None
    
    # Step 1: read file
    def read(self):
        
        try:
            file = self.upload.file
            file.open()
            file.seek(0)

            # only allow CSV files
            if not self.upload.file.name.lower().endswith(".csv"):
                self.errors.append("Only CSV files are supported.")
                self.df = pd.DataFrame()
                return

            raw = file.read()
            last_error = None

            for encoding in ["utf-8", "cp1252"]:
                try:
                    
                    text = raw.decode(encoding)

                    self.df = pd.read_csv(
                        io.StringIO(text),
                        quotechar='"',
                        skipinitialspace=True,
                    )
                    
                    
                    self.encoding_used = encoding
                    break

                except UnicodeDecodeError as e:
                    last_error = e
            else:

                # if we get here, none of the encodings worked
                self.errors.append(f"Unable to decode CSV file: {last_error}")
                self.df = pd.DataFrame()
                return
            self.df = self.df.replace("\u00A0", " ", regex=True)
            before = len(self.df)
            
            self.df = self.df.dropna(how="all")
            self.df = self.df[
                self.df.apply(
                    lambda row: any(
                        str(value).strip()
                        and str(value).strip().lower() != "nan"
                        for value in row
                    ),
                    axis=1,
                )
            ]

            removed = before - len(self.df)
            self.warnings.append(
                f"{removed} completely blank row(s) were skipped during import."
            )
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            self.df = pd.DataFrame()

    def add_warning(self, row_num, field, value, message):
        self.errors.append(
            f"Row {row_num}, {field}: {message}. Original value: {value!r}"
        )

    def clean_value(self, val):
        if pd.isna(val):
            return None
        if isinstance(val, str):
            val = val.strip()
            return val if val else None
        return val
    
    def get_val(self, row, key):
        col = self.mapping.get(key)
        if not col:
            return None
        return self.clean_value(row.at[col])
    
    def parse_date(self, val, field_name, warnings):
        val = self.clean_value(val)

        if not val:
            return None

        if isinstance(val, datetime):
            return val.date()

        if isinstance(val, date):
            return val

        if isinstance(val, str):
            for fmt in [
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%m/%d/%y",
                "%d-%b-%y",     # 27-Jun-26
            ]:
                try:
                    return datetime.strptime(val, fmt).date()
                except ValueError:
                    pass

        warnings.append(f"{field_name}: invalid date '{val}'")
        return None
    
    def parse_bool_presence(self, val):
        val = self.clean_value(val)
        return bool(val)
    
    def parse_activity_type(self, val, errors):
        val = self.clean_value(val)
        if not val:
            errors.append("activity_type is required")
            return None
        first = str(val).lower()[0]
        if first in ["v", "t"]:
            return first
        errors.append(f"activity_type must start with V or T; got '{val}'")
        return None

    def parse_session_format(self, val, location_name, url, errors):
        # Always derive session_format.
        # Do not consume or validate the uploaded session_format value.

        location_name = self.clean_value(location_name)
        url = self.clean_value(url)
        if val and str(val).lower().startswith("o"):
            return "o"
        
        has_location = bool(location_name)
        has_url = bool(url)

        if has_location and has_url:
            return "b"
        if has_location:
            return "i"
        if has_url:
            return "o"
        if not has_location and not has_url:
            return "s"
        
    
    def parse_zip(self, val, warnings):
        val = self.clean_value(val)
        if not val:
            return None
        val = str(val)
        if val.endswith(".0"):
            val = val[:-2]
        import re
        if re.fullmatch(r"\d{5}", val):
            return val
        warnings.append(f"zip: expected 5 digits; got '{val}'")
        return None
    
    def parse_url(self, val, warnings):
        val = self.clean_value(val)
        if not val:
            return None
        val = str(val).strip()
        if val.startswith("http://") or val.startswith("https://"):
            return val
        if "." in val and " " not in val:
            return "https://" + val
        warnings.append(f"url: invalid URL '{val}'")
        return None
    
    def parse_email(self, val, warnings):
        val = self.clean_value(val)
        if not val:
            return None
        val = str(val).strip()
        if re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", val):
            return val
        warnings.append(f"contact_email: invalid email '{val}'")
        return None
    
    def required_text(self, value, field_name, errors):
        value = str(value or "").strip()

        if not value:
            errors.append(f"{field_name} is required")

        return value
    
    def normalize(self):
        if self.df is None or self.df.empty:
            return
        # Trim whitespace from strings
        self.df = self.df.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))

        self.df.columns = self.df.columns.str.strip()

        # Drop blank spreadsheet columns like Unnamed: 17
        self.df = self.df.loc[
            :, ~self.df.columns.str.startswith("Unnamed:")
        ]
        self.df = self.df.fillna("")
        
        # Optional: also standardize
        self.df.columns = [str(c) for c in self.df.columns]

    def clean_row(self, row):
        warnings = []
        errors = []

        cleaned = {
            "title": str(self.get_val(row, "title")).strip(),
            "description": self.get_val(row, "description"),
            "city": self.get_val(row, "city"),
            "location_name": self.get_val(row, "location_name"),
            "address": self.get_val(row, "address"),
            "start_date": self.parse_date(self.get_val(row, "start_date"), "start_date", warnings),
            "end_date": self.parse_date(self.get_val(row, "end_date"),"end_date", warnings ),
            "zip": self.parse_zip( self.get_val(row, "zip"), warnings),
            "has_cost": self.parse_bool_presence(self.get_val(row, "has_cost")),
            "ongoing": self.parse_bool_presence(self.get_val(row, "ongoing")),
            "activity_url": self.parse_url(self.get_val(row, "activity_url"),warnings),
            "contact_email": self.parse_email(self.get_val(row, "contact_email"), warnings),
            "time_commitment": self.get_val(row, "time_commitment"),
            "time_description": self.get_val(row, "time_description"),
            "date_description": self.get_val(row, "date_description"),
            "prerequisites": self.get_val(row, "prerequisites"),
            "categories": self.get_val(row, "categories"),
            "expire_date": self.parse_date(self.get_val(row, "expire_date"),"expire_date", warnings ),
        }

        cleaned["title"] = self.required_text(
            self.get_val(row, "title"),
            "Title",
            errors,
        )
        
        # derived / rule-based fields that depend on cleaned values
        cleaned["activity_type"] = self.parse_activity_type(
            self.get_val(row, "activity_type"),
            errors
        )

        cleaned["session_format"] = self.parse_session_format(
            self.get_val(row, "session_format"),
            cleaned["location_name"],
            cleaned["activity_url"],
            errors
        )

        return cleaned, warnings, errors
    
    # Step 3: validate
    def validate(self):
        if self.df is None or self.df.empty:
            self.errors.append("No data to process")
            return

        
        for field, col in self.mapping.items():
            if col not in self.df.columns:
                self.errors.append(f"Missing required column: {col} for field {field}")

        for idx, row in self.df.iterrows():
            has_location = bool(self.clean_value(row.get("location_name")))
            has_url = bool(self.clean_value(row.get("activity_url")))
 
            if not has_location and not has_url:
                self.warnings.append(
                    f"Row {idx + 2}: Event has neither a location nor a URL."
                )

    # Step 4: process → insert into staging
    def process(self):
        RawLoadData.objects.filter(upload=self.upload).delete()
        
        if self.df is None or self.df.empty:
            return
        database_errors=[]

        for i, row in self.df.iterrows():
            row_num = i + 1

            cleaned, warnings, errors = self.clean_row(row)
            if cleaned["title"] == "REQUIRED":
                continue
            
            database_errors = []
            if errors:
                status = "error"
            elif warnings:
                status = "warning"
            else:
                status = "accepted"

            try:
                
                RawLoadData.objects.create(
                    upload=self.upload,
                    row_number=row_num,
                    organization=self.upload.organization,

                    title=cleaned["title"],
                    description=cleaned["description"],
                    city=cleaned["city"],
                    location_name=cleaned["location_name"],
                    address=cleaned["address"],

                    start_date=cleaned["start_date"],
                    end_date=cleaned["end_date"],

                    zip=cleaned["zip"],
                    has_cost=cleaned["has_cost"],
                    ongoing=cleaned["ongoing"],

                    activity_type=cleaned["activity_type"],
                    session_format=cleaned["session_format"],

                    time_commitment=cleaned["time_commitment"],
                    time_description=cleaned["time_description"],
                    date_description=cleaned["date_description"],
                    activity_url=cleaned["activity_url"],
                    contact_email=cleaned["contact_email"],
                    prerequisites=cleaned["prerequisites"],
                    categories=cleaned["categories"],
                    status=status,
                    validation_warnings={ "messages": warnings},
                    validation_errors={"messages": errors},
                )

            except Exception as e:
                error_message =f"Database error while saving row: {e}"
                database_errors.append(
                        f"Row {row_num} database error: {e}"
                    )
                RawLoadData.objects.create(
                    upload=self.upload,
                    row_number=row_num,
                    organization=self.upload.organization,
                    status="error",
                    validation_errors={"messages": [error_message]},
                    validation_warnings={"messages": warnings},
                )
                
            if database_errors:
                self.upload.load_errors = database_errors
                self.upload.database_error_count = len(database_errors)
                self.upload.status="error"
                self.upload.save()
                
    # Helper to handle mapping with defaults
    def _src_col(self, field_name):
        # Returns the CSV/Excel column mapped to this field, or fallback to the same name
        return self.mapping.get(field_name, field_name)