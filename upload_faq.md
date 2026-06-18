# Upload process
To upload a file with multiple activities, 

1. Download the template file (below is a list of each column and what they mean).
2. Complete the file and be sure to save it as CSV (with a UTF-8 format).
3. Select your file using the Upload file button.


## Raw Review - 
**Errors**: these are rows that cannot be loaded because they violate data rules - you must have an activity title and the activity type must be a v (for volunteer) or a t (for training). 

**Warnings**: these are rows with issues - for example if you don't put an actual DATE in a date column, we cannot process it. It doesn't mean we can load the row - just that the date field will end up blank. You can chose to omit the row from the load and either type it in manually, or submit it in another file corrected. Or you can load it and just fix it after the load in the system.

**Accepted**: these are rows without issue and will be submitted to the rest of the process.

## Location Review
In this page you should review the locations for activities that are in physical locations. We will try to find the location in the system and if we find it we will show the matching location in the review. Sometimes we get it wrong. 

**Actions for each location**:

* Matched to existing location (if we got it right, leave this setting)
* Pick a different location (use this if we got it wrong - there is a different location in the system that should be used)
* Create NEW location from my data (we got it wrong and it's not in the system, even though we thought it was)
* Merge into another uploaded location(This is useful if your original file put in a slightly different address or name for the same location. )
* Skip (use this when you just want to load the activity with NO location - this is the setting for online only locations).


**Page Action**
Once you have reviewed all the locations, if you CHANGED any locations, then you should CONFIRM LOCATION DECISIONS. You will be able to see the new location info on this page before you CONTINUE.


## Activity Review (FINAL)
In this last review page, you will see what the activity will look like in the basic date format. That means if your activity has multiple dates on it then you will see multiple cards for each date. This just lets you see how the data will look once it's loaded. 

**Actions for each Activity**
You can choose to REMOVE a single activity from the upload, but still proceed with the rest (there is a checkbox to remove a single activity).

**Page Action**
Once you PUBLISH, users in the system will be able to query your activities.


## Upload Dashboard
Once the upload is complete you will be presented with a summary statment of the upload with some row counts. 
From this screen you can **View the Published Activities**. If something catastrophic occurred, you can chose to **Undo Upload** the upload which will remove all the uploaded rows from the production data.

## Organization Management 
Use the menu option under Organizer to view the Organization Management for your organization. This is where you can edit locations, activities or managers. All your loaded activities will appear on this page. You can find the pencil icon to edit something, and if available, a trash can icon to delete something. 

## Download Template (Field Key)


| Field | Description |
| ----------- | ----------- |
|"title" | REQUIRED. This is the name of your activity (this line will appear at the top of the activity listing in bold).|
|"description"| Use this for a longer description of your activity. |
|"location_name"| If you know the location exists in the system, use the name as it appears - to avoid creating new copies of the same location. The system will use this name plus the address to try and find existing locations - but if they cannot be found by the system it will automatically add it as a new location managed by your organization.|
|"address"| Street address of the location.|
"city" | City of the location.,
"zip"| 5-digit zip code of the location - if this is in Wisconsin we will use the zip to find the region and county. This field will also be important to create a Flag for the map.|
"activity_type"| REQUIRED. activity type - v for volunteer opportunity and t for training session.|
"ongoing"| Put an "x" in this column if your event does not have start-end dates but is simply an ongoing schedule.|
"start_date"| If ongoing is blank, you must put in a start date. The date should be in this format YYYY-MM-DD format.|
"end_date"| If start_date is NOT blank and this field IS blank it will default to the start_date. If your event crosses multiple date, put the last date of the event here in this format YYYY-MM-DD format.|
"date_description"| OPTIONAL. To create a longer description about the date, you can complete this field. You can leave it blank if you just want to show start - end date; or the phrase ongoing for ongoing. But if you want a longer description - like "Wednesdays in April" you may optionally fill this in.|
"time_description"| OPTIONAL. If you want to specify additional information about the time - like the hours of the activity you may optionally complete this field.|
"activity_url"| If your activity is online you must include this field. It will also be used at the activity level for the Connect link.|
"contact_email"| If you want the Connect link to go to an email address. You must provide either the activity url or a contact email. One of these is required.|
"has_cost"| If your activity is free, leave this blank. If there is a value in this column it will be set with a $ on the form.|
"prerequisities"| OPTIONAL. This field can be used to indicate any prerequisites for your activity.

### NOTE
If you have a system that can generate a download file for you, you may find that you have different column NAMES that our template uses. That's OK, if the field names in your CSV file don't match our template settings, you will have an option to map YOUR field names into our database NAMES.