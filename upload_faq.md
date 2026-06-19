# Upload process
To upload a file with multiple activities, 

1. Download the template file -- [Click here to go to the column definitions](#some-id)
2. Complete the file and be sure to save it as CSV (if you see anything about UTF-8 format, you should pick it).
3. Select your file clicking the Upload file button.


## Raw Review - 
**Errors**: these are rows that cannot be loaded because they violate data rules - for example, you must have an activity title and the activity type must be a v (for volunteer) or a t (for training). 

**Warnings**: these are rows with issues - for example if you don't put an actual DATE in a date column, we cannot process it. We can still load the row - but that date field will end up blank. You can chose to omit the row from the load by clicking the Skip box. Then you could type that activity in manually, or you could submit another file with the corrected activity in a second upload process. Alternatively, you could chose to load the row and then just edit the created activity.

**Accepted**: these are rows without issue and will be submitted to the rest of the process.

## Location Review
In this page you should review your activity's locations. We will try to find the location in the system and if we find it we will show the matching location in the review. If we don't find any thing that looks like your location, the system will plan to create one for you. Sometimes we get it wrong. 

**Actions for each location**:

* Matched to existing location (if we got it right, leave this setting)
* Pick a different location (use this if we matched to the wrong location - there is a different location in the system that should be used)
* Create NEW location from my data (we got it wrong and it's not in the system yet, even though we thought it was. You need to select this so it will create a new location under your organization)
* Merge into another uploaded location (This is useful if your original file had slightly different address or name for the same location.)
* Skip (use this when you just want to load the activity with NO location - this is the setting for online only locations).


**Page Action**
Once you have reviewed all the locations, if you CHANGED any locations, then you should CONFIRM LOCATION DECISIONS. You will be able to see the new location info on this page before you CONTINUE.


## Activity Review (FINAL)
In this last review page, you will see how your activity will look on the Volunteer or Training page. These pages show activities one date at a time. If the same activity has multiple dates then you will see multiple cards for each date. Use this page as a preview for the load. 

**Actions for each Activity**
You can choose to REMOVE a single activity from the upload, but still proceed with the rest (there is a checkbox to remove a single activity).

**Page Action**
Once you PUBLISH, users in the system will be able to query your activities. Your activities are now live!


## Upload Dashboard
Once the upload is complete you will see a summary statment of the upload with row counts. 
From this screen you can **View the Published Activities**. If something happened, you can chose to **Undo Upload** the upload which will remove all the uploaded rows from the production data.

## Organization Management 
Use the menu option under Organizer to view the Organization Management for your organization. This is where you can edit locations, activities or managers. All your loaded activities will appear on this page. Use the pencil icon to edit something, and if available, a trash can to delete it. 

<a name="some-id" />
## Download Template (Field Key)</a>


| Field | Description |
| ----------- | ----------- |
|"title" | REQUIRED. This is the name of your activity (this line will appear at the top of the activity listing in bold).|
|"description"| Use this for a longer description of your activity. |
|"location_name"| If you know the location exists in the system, use the name as it appears - to avoid creating new copies of the same location. The system will use this name plus the address to try and find existing locations - but if they cannot be found by the system it will automatically add it as a new location managed by your organization.|
|"address"| Street address of the location.|
"city" | City of the location.,
"zip"| 5-digit zip code of the location - if this is in Wisconsin we will use the zip to find the region and county. This field will also be important to create a Flag for the map.|
"activity_type"| REQUIRED. activity type - v for volunteer opportunity and t for training session.|
"ongoing"| Any non-blank value in this column will be used to set the value to Ongoing. Leave blank if your events has dates instead. |
"start_date"| If ongoing is blank, you must put in a start date. The date should be in this format YYYY-MM-DD format.|
"end_date"| If start_date is NOT blank and this field IS blank it will default to the start_date. If your event crosses multiple date, put the last date of the event here in this format YYYY-MM-DD format.|
"time_commitment"| OPTIONAL. You may use this to indicate how long participants should expect to commit to this event. Free-form text.
"date_description"| OPTIONAL. Indicate additional info (beyond start-end dates, or the ongoing flag) regarding dates here. Free-form text that will appear below the Activity title. |
"time_description"| OPTIONAL. Indicate something about the time for your activity here. This is a free-form text that will appear below your activity.|
"activity_url"| If your activity is online you must include this field. It will also be used at the activity level for the Connect link.|
"contact_email"| You must provide either the activity url or a contact email. One of these is required.|
"has_cost"| If your activity is free, leave this blank. If there is a value in this column it will be set with a $ on the form.|
"prerequisities"| OPTIONAL. This field can be used to indicate any prerequisites for your activity.
"categories" | You can list the categories for your activity here with a comma between each one. Here are the values you can use: aq=Aquatic Life, cs=Citizen Science, eco=Ecology, edu=Education, geo=Geology, hc=Human Connections, pla=Plants, ste=Stewardship, wat=Water, wea=Weather & Climate, and wil=Wildlife. You must use the 2-3 letter codes, inside double quotes separated by commas. For example, "cs, wil, edu".


### NOTE
If you have a system that can generate a download file for you, you may find that you have different column NAMES that our template uses. That's OK, if the field names in your CSV file don't match our template settings, you will have an option to map YOUR field names into our database NAMES.