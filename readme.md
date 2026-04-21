This is my new readme file.
Organizations, Locations, Activities (that can be volunteer opportunities, or trainings)
search pages for each list. add pages for each object. backend in Postgres sql database.
user logins and profiles for managing screen edits.



Feature (feature-location--merged to main and now in production.): adding adjustments to the location table in the over data model. Currently each location has an org - but that is only to manage editing (and larger things like state parks can be under the state park org which is usually only going to be managed by staff). 
Orgs have Activities which have Sessions. Sessions have Locations. (these are the one to many paths thru the data model).

Orgs have a default location - and if you are creating a new session that is configured as either InPerson or Hybrid, it will prepopulate the location with the org's default location.


PRODUCTION NOTE:
make sure you upload the csv files and then runthe code that populates the tables:

python manage.py load_locations_from_csv "orgs/data/state_parks.csv" "Wisconsin State Parks"
python manage.py load_locations_from_csv "orgs/data/state_forests.csv" "Wisconsin State Forests"
python manage.py load_locations_from_csv "orgs/data/recreation_areas.csv" "Wisconsin Recreation Areas"


python manage.py update_latlng
(this is not updating the latlng data on production)

feature-map
 - tasks
1. configure current locations.html to show list OR map - make sure filter implementation lets you show filtered maps.
2. load wisconsin sites - state parks, state forests, recreation areas. make sure you have the orgs for each.
left over code for next steps in this feature:
Next UI steps:
* hide/show the url and location fields based on the session_format selection (javascript change)
* find better ways than a giant drop down to select a differnt location.


Future Feature:
Configure an upload process that will take in a csv or excel file and load it into Pending Locations, Pending Activities and Pending Sessions for audit/approval and push into the production tables. So we can automate the loading of data. (this is one way to automate getting activities into the system... maybe even extend this into an API thing so we can pull the data directly from connected organizations ultimately)

Notes from meeting with Tim:
unhide password when typing.
present the rules when typing a password.
xfind a way to say what the icons mean right away (?) - on the main pages as a simple legend.
xmd pages should not have numbers.use 2nd layer headers.
xmake region icons bigger on the activity screen.
implement the default search page?
... keep me notified of all the bird stuff...
--- what just's happening in the next 2 weeks.
--- what's in an area. 

x can i re-implement the filter page on the side bar./ maybe rebuild with activity name instead of results.

(let the initial page show with filter visible.)
xcolor the tabs - and color the markers.
walk thru the story and make sure you have implemented the following tasks:
xfilter fields based on session_format 
xadd example data in the various form fields
make sure the notices are always in red
volunteer = lime green 
training = blue
consider making the end_date required if you have a start date... if you are doing ongoing then you don't have any dates...
add a check to the delete manager where you cannot delete yourself.

ok - you have good work done on the forms but you still have a couple things to fix:
1. get the location picker to actually work on the org form.
2. make sure that your errors all actually show on the forms (both activities and org and location) because you are getting required errors but they are not showing on the form.
