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

Work on the upload process

Remove delete checkbox from session page. only way to delete an activity is on the managing orgs page. (or check out this f() ?)
Add pre-requisite field to the activity.
Move time description to the Session.

Friday:
* restore/start Postmark
* confirm outbound email works again
* confirm entire login/registration process.
* confirm add new organziation works in productions (there are multiple emails there)

Then move DNS to Cloudflare
* import DNS records carefully
* verify:
-Render app works
-Postmark DKIM/SPF still valid
-verification emails send
-HTTPS works

add 2fa
X Install 2FA 
Run migrations
* note on login page: For added security you can enable 2FA authentication.
* banner on OrgMgmt - For added security, organizers should enable two-factor authentication.
* add menu option 
<a href="{% url 'two_factor:setup' %}">Set up two-factor authentication</a>
* later enforce it: add to org_mgmt view:
if request.user.is_authenticated:
    is_organizer = request.user.profile.managers.exists() or request.user.is_staff

    if is_organizer and not request.user.is_verified():
        return redirect("two_factor:setup")



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

Future wishlist - make a video that explains how to manage an org in this system.
Talk to Sage about creating a way to 'register' for an activity in her system directly from here.
