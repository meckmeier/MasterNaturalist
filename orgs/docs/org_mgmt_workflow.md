# Organization Management -
When users request a new organization, the email making the request will automatically be added as the Owner of the Org in the OrgManagers table. If you have an entry in the OrgManagers table, you will see the Manage Organization button at the bottom of the landing page.

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

