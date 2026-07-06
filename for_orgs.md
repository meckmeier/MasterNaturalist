# For Organizations
If you are a nature based organization and would like to share volunteer or learning opportunities in WildPathsWI.org - Welcome! We are excited to have you. Organizations really are the backbone of this site. Without your participation, there wouldn't be much for volunteers to find. But with you, we can build a wonderful community.

## Getting Started
You can <a href="{% url 'help_video' 'CO5Xr3qWKWc' %}" class="help-card help-card-video">view this How-to Video</a> if you prefer to see the steps in action.

First you need to get your organization added. 

1. Use the menu in the top right corner to Add Your Organization.
2. Complete the Form.
3. Click Submit Request.

> | Field | Description |
> | ----------- | ----------- |
> | Organization Name | This name will appear as a "sponsor" for activities - and users can search based on your name. |
> | About | This should be relatively brief but descriptive so volunteers will be able to tell what you do. We will use this description to help us approve your request. |
> | Main URL | We will provide a link to this site - make sure it is in a url format (www.mysite.com for example). |
> | Region | If your organization is based in a specific region in Wisconsin, you can pick it here. This is just informational for volunteers looking at your organization. |
> | Contact Email | This field is really important because we will use this email to communicate with you about the request. You will want to use this email when you register to the site to manage the organization in the future. You will be able to add more people to manage this organization in the future. |
> | Contact Name | REQUIRED. |
> | Contact Title | OPTIONAL, but helpful |
> | Authorized to represent the organization | We are asking you to confirm your role. Once this organization is created you will be responsible for maintaining the organization going forward. We expect only authorized folks to be submit requests. |



After your request is approved, you will receive an email from WildPathsWI.org (it comes from mary@eckmeier.com right now). In the email, you will find a link to asking you to register for the site. 

### Creating a login

1. Click on the link in the email you received from us.
2. Complete the login form
    username - this can be anything you want. 
    email - this MUST match the email you used above in the request form. Otherwise you won't be able to manage your organization.
    password - like all sites with registration we ask that you create a password.
    confirm password - retype your password.
3. Click Create Account.
4. You will receive yet another email from us - this is just to confirm the email really worked.
5. Click the link in that email - and click CONFIRM EMAIL. This will complete your registration.

### Login
The confirm email button should take you to a login screen - but if not click the WildPathsWI Icon in the top right corner and look for the LOGIN button near the bottom of the page.
1. Type your username (or you can use your email - both will work).
2. Type your password.

NOTE that if you forget your password, there is a Forgot Password link on this page.

### Manage Organization
Once you are successfully logged in, the system will automatically make you a manager to your Organization. When you are a manager, you will see a new button at the very bottom of the page (where the login used to be).

1. Click Manage Organizations.
2. From here you can look for pencil icons to EDIT things.
3. Or look for the PLUS button to add.
4. There are Locations (for addresses which will translate to a flag on the map), Activities (for volunteer OR learning opportunities), Managers (to add additional people to manage your organization)

NOTE: if something goes wrong and you are not able to see this page, please submit a feedback request and indicate that you are having login problems. Provide your username and Organization name. Someone will get back to you with a resolution.

NOTE: if you wish to have someone else also manage your organization, have that person create a login. Use the Login button on the main page, and click the link to REGISTER. Once they have created a new login, you will be able to use their email address to add them to the Managers section of your organization.

## Activities
You can <a href="{% url 'help_video' '1P94zw9f604' %}" class="help-card help-card-video">view this how-to-video</a> to see managing your organization in action.

Activities are the primary object in our application.
To add a new activity, click the PLUS sign in the Activities section header.

> | Field | Description |
> | ----------- | ----------- |
> | Title | REQUIRED. This is the main name of your activity. It will appear at the top of each card. |
> | Type | REQUIRED. Activities are either Volunteer or Learn. |
> | Org | This will already be filled in for you. |
> | URL for Activity | Use this slot for more information about this particular activity. |
> | Activity Contact | Use this lot for an email. You must have EITHER a URL or a Contact email - otherwise users won't know how to get in touch with you! |
> | $ | this little checkbox between url and contact is for activities that come with a cost. Just so users can be prepared that the learning activity might not be free. |
> | Description | Descriptions will show with the first 200 or so characters, but will expand when the user clicks on them. To make it easier for users to tell if they want to pursue this activity, make sure you start off with the key information. You can use a lot of characters here if you want to add in other details, though. The field will expand when the user clicks on it. |
> | Prerequisites | If your activity requires previous training, or the volunteer activity requires users to have some abilities, be sure to include it here. |

### Session information
This section is for the when and where... depending on your activity you might have just one session... but you could also have multiple sessions and it's easy to add more here. The final cards are shown BY this session information - so if you have multiple sessions, you will see multiple cards in the activity lists.


> | Field | Description |
> | ----------- | ----------- |
> | Format | In Person = you will need to pick a location. Online = you will need to pick a URL. Hybrid = if the main event is in-person, but there is a way to join online then call it Hybrid. You can specify both a URL and a Location. Self-selected locations - if your volunteer event is done at the volunteers discretion, then use this choice. |
> | URL | for Online and Hybrid - it must be in a url format (www.mysite.org/trainingsession for example). |
> | Location | If you have a default location, it will populate here automatically. But if you have not created a location yet - you can add one now (look below for more details). You can also find locations that might already be in the system. For example, all the state parks are already loaded. If you are a friends organization, for example, you can just pick your state park. |
> | Ongoing | This checkbox indicates that the activity is happening over time. That is, there are not specific dates for it. You CAN choose to specific the range of dates for ongoing activities (so for example, if you are offering volunteer options from October 1 thru the 15 you can specify that in the Start and End). The dates will cause the activity to roll off when it is no longer in effect. |
> | Start | If your activity is happening on specific dates - then you can record that here. If your activity is only one day long, just fill out the Start (the end will default to just one day). Use the YYYY-MM-DD format. |
> | End | If your activity spans multiple days (like a conference that covers several days), then you can enter the end date here. Use the YYYY-MM-DD format. |

### Additional Details
These are optional fields that you can use to provide more details to the end users. 

> | Field | Description |
> | ----------- | ----------- |
> | Date Description | If you want to say something more general than just the date, you can complete this field. |
> | Time | this field is used to specify the duration of the event. |
> | Time Description | like the date description, this is a generic time description. These fields are not session specific, so use them as general information. |
> | Keywords | check the boxes for the content or service categories. These can be used in category searches to help users quickly search for specific types of activities. |


#### Pick a Location
1. Click the Find Location button - a pop up screen will appear.
2. Type in a name for your location... it will look for any possible matches. You can also type in a city name, and it will show you all the locations in your city.
3. If you cannot find the location in the system you can click the ADD LOCATION button.
4. Complete the popup screen with a location name and click OK.
5. The new location will show up as one that is managed by your organization (you will see it on the organization page).
6. You should edit that location after you finish adding in this activity with an address. If it doesn't have an address it won't get a flag on the map.

## Locations
If you created a location while adding in your activity above, you will see that location in the Location section. You can use the Pencil button to edit it and add in address details. You will need to include a full address to get a flag icon on the map. Locations without flags, will still appear on the Location List page.

> | Field | Description |
> | ----------- | ----------- |
> | Name | Use this field to describe the location using a short name. |
> | Address | Street Address |
> | City | City |
> | State | This field defaults to WI |
> | Zip Code | The zip code field will be used to populate the County and Region. There are zip codes that cross counties though, so if we picked the wrong one for you - you are able to change them. |
> | About | Use this field for a longer description of the location. |
> | Location website | OPTIONAL. If your location has it's own web page, you can include it here. |
> | Location email | OPTIONAL. If your location has a specific contact email you can include that here. |
> | Region | The region pick here will drive the map icon on your location and activities. |
> | County | The county tells us which region to pick. It is also a search option for the end user. |


