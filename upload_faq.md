# Upload process
Use the Download Template to get a format for uploading data. Make sure you review the data requirements for each column.


| Field | Description |
| ----------- | ----------- |
|"title" | REQUIRED. This is the name of your activity (this line will appear at the top of the activity listing in bold).|
|"description"| Use this for a longer description of your activity. |
|"location_name"| If you know the location exists in the system, use the name as it appears - to avoid creating new copies of the same location. The system will use this name plus the address to try and find existing locations - but if they cannot be found by the system it will automatically add it as a new location managed by your organization.|
|"address"| Street address of the location.|
"city" | City of the location.,
"zip"| 5-digit zip code of the location - if this is in Wisconsin we will use the zip to find the region and county. This field will also be important to create a Flag for the map.|
"activity_type"| activity type - v for volunteer opportunity and t for training session.|
"ongoing"| Put an "x" in this column if your event does not have start-end dates but is simply an ongoing schedule.|
"start_date"| If ongoing is blank, you must put in a start date. The date should be in this format YYYY-MM-DD format.|
"end_date"| If start_date is NOT blank and this field IS blank it will default to the start_date. If your event crosses multiple date, put the last date of the event here in this format YYYY-MM-DD format.|
"date_description"| OPTIONAL. To create a longer description about the date, you can complete this field. You can leave it blank if you just want to show start - end date; or the phrase ongoing for ongoing. But if you want a longer description - like "Wednesdays in April" you may optionally fill this in.|
"time_description"| OPTIONAL. If you want to specify addtional information about the time - like the hours of the activity you may optionally complete this field.|
"activity_url"| If your activity is online you must include this field. It will also be used at the activity level for the Connect link.|
"contact_email"| If you want the Connect link to go to an email address. You must provide either the activity url or a contact email. One of these is required.|
"has_cost"| If your activity is free, leave this blank. If there is a value in this column it will be set with a $ on the form.|
"time_commitment"| You may type one of the following in this field: 1 hour, 2-4 hours, 1/2 day. 1 day, 2-4 days, 5 days +.|
"session_format"| REQUIRED: Type an "o" for online, or "b" for online AND  in-person. Use "i" for in-person only. Use "s" if the location is self-directed.|

