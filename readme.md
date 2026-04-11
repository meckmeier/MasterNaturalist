This is my new readme file.
Organizations, Locations, Activities (that can be volunteer opportunities, or trainings)
search pages for each list. add pages for each object. backend in Postgres sql database.
user logins and profiles for managing screen edits.


Feature Steps:
Test the following: 

create org with no default location
create org with default location
add/edit location under org
create in-person session and confirm default fills
switch to hybrid and confirm it fills
override location and save
edit an existing activity/session and make sure nothing weird happens
confirm users can still only edit the right locations

Feature in this version: adding adjustments to the location table in the over data model. Currently each location has an org - but that is only to manage editing (and larger things like state parks can be under the state park org which is usually only going to be managed by staff). 
Orgs have Activities which have Sessions. Sessions have Locations. (these are the one to many paths thru the data model).

Orgs have a default location - and if you are creating a new session that is configured as either InPerson or Hybrid, it will prepopulate the location with the org's default location.

Next UI steps:
* hide/show the url and location fields based on the session_format selection (javascript change)
* find better ways than a giant drop down to select a differnt location.

Next Feature:
Configure an upload process that will take in a csv or excel file and load it into Pending Locations, Pending Activities and Pending Sessions for audit/approval and push into the production tables. So we can automate the loading of data. (this is one way to automate getting activities into the system... maybe even extend this into an API thing so we can pull the data directly from connected organizations ultimately)