# services/csv_importer.py

import pandas as pd
from datetime import datetime
from orgs.models import RawLoadData

class CSVImporter:
    def __init__(self, upload, mapping=None):
        self.upload = upload
        self.mapping = mapping or {}  # e.g., {"Event Title": "title"}
        #self.errors = []
        #self.df = None

    # Step 1: read file
    def read(self):
        try:
            file=self.upload.file
            file.open()
            file.seek(0)

            if self.upload.file.name.endswith(".csv"):
                self.df = pd.read_csv(self.upload.file)
            else:
                self.df = pd.read_excel(self.upload.file, engine="openpyxl")
           
        except Exception as e:
            self.errors.append(f"Error reading file: {e}")
            self.df = pd.DataFrame()  # empty DataFrame if error
    def apply_mapping(self, raw_rows):
        mapped_rows=[]
        for i, row in enumerate(raw_rows):
            mapped={}
            for field, column in self.mapping.items():
                value=row.get(column)
                #minimal clean up only (safe)
                if isinstance(value,str):
                    value = value.strip()
                mapped[field]=value
            mapped_rows.append({"row_number": i+1,
                                "raw_data":row, 
                                "mapped_data": mapped})
        return mapped_rows
    
    # Step 2: normalize / cleanup
    def normalize(self):
        if self.df is None or self.df.empty:
            return
        # Trim whitespace from strings
        self.df = self.df.apply(lambda col: col.map(lambda x: x.strip() if isinstance(x, str) else x))

        self.df.columns = self.df.columns.str.strip()

        # Optional: also standardize
        self.df.columns = [str(c) for c in self.df.columns]

    # Step 3: validate
    def validate(self):
        if self.df is None or self.df.empty:
            self.errors.append("No data to process")
            return

        
        for field, col in self.mapping.items():
            if col not in self.df.columns:
                self.errors.append(f"Missing required column: {col} for field {field}")

    # Step 4: process → insert into staging
    def process(self):
        RawLoadData.objects.filter(upload=self.upload).delete()
        if self.df is None or self.df.empty:
            return

        for i, row in self.df.iterrows():
            # Map source columns to staging fields
            print("ROW INDEX:", row.index.tolist())
            print("ROW DICT:", row.to_dict())
            print("MAPPING:", self.mapping)
            print("upload", self.upload)
            print("ROW_DATA", row)
            
            date_val = row.at[self.mapping.get("date")]
            
            if date_val:
                if isinstance(date_val, str):
                    try:
                        date_val = datetime.strptime(date_val, "%Y-%m-%d").date()
                    except ValueError:
                        self.errors.append(f"Row {i+1}: Invalid date format {date_val}")
                        date_val = None
            
            try:
                 RawLoadData.objects.create(
                    upload=self.upload,
                    row_number=i + 1,
                    organization=self.upload.organization,
                    title=row.at[self.mapping.get("title")] if self.mapping.get("title") else None,
                    description=row.at[self.mapping.get("description")] if self.mapping.get("description") else None,
                    city=row.at[self.mapping.get("city")] if self.mapping.get("city") else None,
                    location_name=row.at[self.mapping.get("location_name")] if self.mapping.get("location_name") else None,
                    address=row.at[self.mapping.get("address")] if self.mapping.get("address") else None,
                    zip=row.at[self.mapping.get("zip")] if self.mapping.get("zip") else None,
                    state=row.at[self.mapping.get("state")] if self.mapping.get("state") else None,
                    date=date_val,
                    end_date=row.at[self.mapping.get("end_date")] if self.mapping.get("end_date") else None,
                    activity_type = row.at[self.mapping.get("activity_type")] if self.mapping.get("activity_type") else None,
                    time_description = row.at[self.mapping.get("time_description")] if self.mapping.get("time_description") else None,
                    date_description = row.at[self.mapping.get("date_description")] if self.mapping.get("date_description") else None,
                    activity_url = row.at[self.mapping.get("activity_url")] if self.mapping.get("activity_url") else None,
                    no_cost = row.at[self.mapping.get("no_cost")] if self.mapping.get("no_cost") else None,
                    contact_email=row.at[self.mapping.get("contact_email")] if self.mapping.get("contact_email") else None, 
                    online=row.at[self.mapping.get("online")] if self.mapping.get("online") else None, 
                    ongoing=row.at[self.mapping.get("ongoing")] if self.mapping.get("ongoing") else None, 
                    status="valid"
                    )
                
            except Exception as e:
                self.errors.append(f"Row {i + 1} error: {e}")

    # Helper to handle mapping with defaults
    def _src_col(self, field_name):
        # Returns the CSV/Excel column mapped to this field, or fallback to the same name
        return self.mapping.get(field_name, field_name)


    