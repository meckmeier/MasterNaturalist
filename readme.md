This is my new readme file.
Organizations, Locations, Activities (that can be volunteer opportunities, or trainings)
search pages for each list. add pages for each object. backend in Postgres sql database.
user logins and profiles for managing screen edits.



Feature (feature-location--merged to main and now in production.): adding adjustments to the location table in the over data model. Currently each location has an org - but that is only to manage editing (and larger things like state parks can be under the state park org which is usually only going to be managed by staff). 
Orgs have Activities which have Sessions. Sessions have Locations. (these are the one to many paths thru the data model).

Orgs have a default location - and if you are creating a new session that is configured as either InPerson or Hybrid, it will prepopulate the location with the org's default location.


PRODUCTION NOTE:
make sure you upload the csv files and then run the code that populates the tables:

python manage.py load_locations_from_csv "orgs/data/state_parks.csv" "Wisconsin State Parks"
python manage.py load_locations_from_csv "orgs/data/state_forests.csv" "Wisconsin State Forests"
python manage.py load_locations_from_csv "orgs/data/recreation_areas.csv" "Wisconsin Recreation Areas"
python manage.py update_latlng (now in a management form so it can be run from the app directly by staff people 10 at a time.)


Future Feature:
Configure an upload process that will take in a csv or excel file and load it into Pending Locations, Pending Activities and Pending Sessions for audit/approval and push into the production tables. So we can automate the loading of data. (this is one way to automate getting activities into the system... maybe even extend this into an API thing so we can pull the data directly from connected organizations ultimately)
Move time description to the Session.

START HERE:
Work on the upload process
1. Action needed on all pages of the upload.
X my row names => wildpaths' row names
X first time here -- overview or map of the upload process.
X move template and instructions to the top.

X map: save / cancel only. only show if their are unmapped fields.

X stage - do better format. only show the error or warnings - what will be omitted from the load, what will go in that you might want to edit, and what was accepted.

Xlocation - do a fuzzy match on name... 
Xadjust the decision box - use a drop down. add a feature to ignore match and use my location (you need to check on all the status values in this table)

x duplicate location management

session url should be the field loaded... and it would by default be the url for the activity. 
if its online it needs a session url/ and the activity needs either a url OR a contact email.
you need to apply the same rules on the upload process.
the remove button on the activities doesn't actually skip the activities in the load.


xFinal Review - for review activities.
xchange skip to REMOVE and don't save here, just continue.

add a rollback confirmation.


verify that the email sent when createing a new org actually creates the new user account.
test that with other people.


add 2fa
X Install 2FA 
X Run migrations
* note on login page: For added security you can enable 2FA authentication.
* banner on OrgMgmt - For added security, organizers should enable two-factor authentication.
* add menu option 
<a href="{% url 'two_factor:setup' %}">Set up two-factor authentication</a>
* later enforce it: add to org_mgmt view:
if request.user.is_authenticated:
    is_organizer = request.user.profile.managers.exists() or request.user.is_staff

    if is_organizer and not request.user.is_verified():
        return redirect("two_factor:setup")

Add Rate Limiting (you can only do something so many times)
* login, signin, registration, etc.
- pip install django-ratelimit
- add to views
from django_ratelimit.decorators import ratelimit
@ratelimit(key='ip', rate='5/m', method='POST')
def my_view(request):


Version Two:
* one new field to Profile (terms_accepted_at)
* added allauth framework along with turnstile captcha feature to mitigate bot logins. Verify email with password rules to help ensure that only legitmate users will be able to make changes to the database. Moved browse and search features to the public access.
* replaced registration/ with accounts/ folder and all the associated user forms to have email be validated during registration.
* menu changes included color fix, staff submenu for admin/ and user info screen. New edit profile option under Volunteer.
* feedback will send me an email when someone submits.
* added update_latlng staff only page. 
* converting all the profile.staff references to the user.is_staff field instead.
 --- NOTE make sure that anyone with staff in production is also Is_staff in user (I did this today but just double check it).
 --- You really need to test all the pages again staff/ mgrs / and none -- 
* added a link to org dashboard from session page... so when you edit you can get back more quickly.
* changed colors on the landing page buttons to use the colors from the logo.
* activity form enhancement to hide/show dates based on ongoing selection.
* Adding a new organization is now a two step process... user is NOT required to be logged in for the organization to be created.
* adding some filter context to the activity page - just added number found in results on the other two pages.
* changed no cost to has cost, but still show free checkbox on form... seemed to make more sense this way. Show as $ without words on form.
* i button with info on the dates. Hide start/end when you click ongoing
* changed language: More info instead of contact for url links.
* added Free to the activities filter.
* Hide references to favorites on public access... have created full experience for public viewers.
* Add prerequisite field to activities.
* DNS is now on cloudflare.

Upload process:
* check that no end date will default to the start date (for a single day activity)
* check other processes to make sure they really work


Future wishlist - make a video that explains how to manage an org in this system.
Talk to Sage about creating a way to 'register' for an activity in her system directly from here.
