# Organization Management -
When users request a new organization, the email making the request will automatically be added as the Owner of the Org in the OrgManagers table. If you have an entry in the OrgManagers table, you will see the Manage Organization button at the bottom of the landing page.

url: path("org/enroll/", views.org_enroll, name="org_enroll"),
(shows an html - org_enroll.html which is based on the orgEnrollmentForm form that will populate the OrgEnrollment table.)
SAVE will send an email to Staff to approve the organization. Also will show:  path("org/enroll/thanks/", views.org_enroll_thanks, name="org_enroll_thanks"),

url: path("staff/org-enrollments/", views.org_enrollment_list, name="org_enrollment_list"),
    path("staff/org-enrollments/<int:enrollment_id>/approve/", views.org_approve, name="org_approve"),
    path("staff/org-enrollments/<int:enrollment_id>/deny/", views.org_deny, name="org_deny"),  

(shows org_enrollment_list.html which lists all the enrollment records. Unapproved ones will have an APPROVE and DENY buttons. Deny is dead path - sends an email and records denial. Approve generates an email to the orgEnrollment email to say they can proceed to create a username if the org email already exists in the database. The link contains info that will let me create the OrgManager.
The approve will also create the Organization, and Location (default) records, and if i have the user will create the OrgManager record.




## Organization
There is an edit PENCIL on the Organization Management page, where you can edit the Organization record. One feature here is to add a Default Location - this will allow you to automatically select a preferred location for activities when you add new ones.

## Locations
Locations = Addresses. These addresses are periodically run thru a latitude/longitude code that will allow them to appear on the Main Map page with a flag.  Locations by default will "belong" to the organization that creates them. Belonging to an Organization just means that the Location details can be updated by people in the OrgManagers table for the owning organization. Any location can be selected for activities used by this organization.

## Activities
Activity are adding from the Org Management page, or thru the Upload Activities routine. This is the only way that activities are added. If you have only one or two activities to add, you can just use the main Org Management page to + (add a new activity).

Activities consist of a minimum of one session, but can have multiple sessions. Sessions describe the WHERE and WHEN of an activity. Activities come in two flavors: Learn and Volunteer. 

activity_create and activity_edit - urls that both hand off to the activity_form_workflow:
    workflow will determine if in POST if the activity looks like it already exists and provide a confirm message.
    workflow will set created, owner and updated by values based on current user.
    if NEXT parameter = org_mgmt, then go to org_mgmt , and reset to the org location.
    if no next, then go to a full Activities (filtered to this one) view.

