# Wisconsin Master Naturalist - CS50 Capstone
This application is designed to help Wisconsin Master Naturalists to complete their annual re-certification. Naturalists are asked to complete 40 hours of volunteer work and 8 hours of training. Opportunities can be found in nature-based organization throughout the state of Wisconsin. Both volunteer and training hours may be conducted online or in person. 

The main requirements for this project (after having a discussion with the director of the organization):

* Provide a full list of Nature-based Organizations - with geographic designations that are VISUAL.
* Only registered users would be able to see the Events.
* Provide a method of searching organizations by region or county, or those with volunteer or training opportunities.
* Provide a list of upcoming events that the user might want to participate in.
    - ensure that upcoming events are based on the current dates.
* Ability to review past events. 
* Provide a method to search for for specific types of events.

* Allow our partner organizations to record their upcoming events and trainings with security (so no one can edit someone else's events).
* Allow staff to review and edit any existing organizations or events.

## Requirements are implemented below:
All users (logged in or otherwise) are able to 
* view the list of existing Nature-based organizations.

Once logged in users are able to 
* filter the list for geography (either county or region filter)
>make sure this will filter the OrgLOCATIONS! this is a nuance implementation.
* filter by words in the name or description of the organization.
* users are also able to FAVORITE individual organizations which will allow them to see only their Favorites in both list views.
* filter orgs to find those that provide volunteer or training opportunities

From the organization main list, users can click the organization name to go to the Organization Detail page. Here users can: 
* edit the organization data (if they are the 'creator' of the organization or a designated 'staff' person (based on their profile))
* each organization may have one or multiple locations and these can be maintained on this same edit page, using the Django formset.

In addition, users will be able to view events.
* event can be either volunteer opportunities or training sessions.
* these can be filtered in the list view
* or filtered by clicking the link from the organization list view to only events for that org.

* Adding new organizations and associated events can be done via menu options.

## Distinctiveness and Complexity: 
To access the full functionality of the application, you will need to create a username and password - this is done via the Register link.
Although I followed the basic approach we did from project 4 - creating a Profile for each user - this was done to designate a user as Staff. This designation allows the administrator to determine which users are able to edit any existing records. Editing existing orgs and their associated events is only available to the person that created the objects (the 'owner') but reviewing the requirements I needed a way for staff to manage these elements as well. This security was required so I could do the security requirement.

The data model I designed went thru several iterations. Because I have 'organizations' with multiple locations across the state, I build a one-to-many relationship between the Organization and the OrgLocations. However, as I dug into the data, I discovered that some nature organizations (like the Girl Scouts for example) would use existing Wisconsin state properties for their training or volunteer opportunities. 

This required that I decouple the Event Location from the Organization Location. That is an event would be associated with an Organization (Girl Scouts) but the event location would be at a different organizations location - like a Wisconsin State Park. I wanted to keep these hierarchies intact. This was a very valuable exercise that helped me to become much more familiar with the roles of FORMS, to MODELS and displays using both AJAX (as it was described in my searches) and VIEWS in Django.

>The classic database one-to-many form for editing and viewing data was a technique I was eager to understand. Using ChatGPT I was able to identify the "formset" as a way of achieving this and through much trial and error, plus help from the internet, I was able to implement it in this main Organization Detail page. Here you can create (or edit) an organization and work with their underlying locations on the same page.


## Areas of complexity:
### Data Model

Organization => one or many Locations.
(this idea that a single organzation may have multiple locations was driven specifically by the existence of the DNR which has many different state parks - each park has it's own web site, but volunteer and training opportunities are provided by the parent organization, so I wanted to explore how this data model might be implemented here.)

Events are associated to an Organization (especially if it is an online event), but may optionally identify a location - which could be a child of the event Organization or it could be a location for a different organization (Girl Scouts - at a Wisconsin State Park).

Region designations for organizations had been previously identified with an icon - so I captured the icons and built lookups in the model that would allow me to SHOW these images on the forms. It makes the identification of appropriate organizations more direct for the users.

Models in the application are:
    **Commitment** (a list of time commitments that can be modifiable by the administrator)
    **County** (lookup for listing Wisconsin counties for drop downs)
    **User** (based on Abstract User) with an associated Profile (used to capture roles for securing edit capability to Staff and to track Favorites)
    **Organization** + **OrgLocation** (one to many) to describe the organizations.
    **FollowOrg** to track the Profile to Organization relationship
    **Event** to store both volunteer and training opportunities (contains foreign keys to both Organization, and to OrgLocation)

**SQLiteStudio** I downloaded this tool so I could work with the data directly. I used it to import some existing values, and adjusted structures, but recognized that leaving the migration process in Django in charge resulted in many fewer issues. It was a pretty great learning experience. Having the tool really helped me to understand the relationship between the database and the model structures in Django. It was a strangely tough process for me to bridge these two concepts.


### Forms
I used forms extensively in this application. 
The filter form technique is used in both the index and the event_list pages - here I used {% blocks %} to customize the filter form to use fields appropriate for each page. 

In addition I added some custom validation in the form to help me ensure that location names were distinct across all organizations - this is a technique that would benefit from a more universal model level validation, but I just wanted to do a form validation here.

I also used the formset object to get the one-to-many type of form structure as described earlier in this document.

### Views
In my views I made use of the query parameter extensively to implement the filtering functionality.

I also tried to build view structures that would allow me to create a single page for both viewing, editing and creating data objects - both events and organizations. Having two of these really helped to solidify the thinking and implementation.

I did find that each new layer created alot of interconnectedness that made me both curse and ultimately recognize the value of the django framework. It's complicated - but the more complicated it got, the more I could see how valuable these types of frameworks could be.

## HTML/ Bootstrap CSS
In this area I was challenged to ensure that the following points were addressed:
* filtering view using multiple fields.
* linking between organizations and their associated volunteer opportunities and training sessions.
* ability to capture organizations that I want to follow as a user.
* using icons to maximize both functionality and provide a visual representation of key elements like my favorited organizations and the region designation.
* application should be responsive and change views for mobile devices, v. larger screens.

I did a great deal of online searching to understand how to leverage BOOTSTRAP for the formatting of the application and to extend my understanding of the various parts of the Django data model settings. There is one API call for the OrgLocation select when editing or creating new Organization records. 


## What’s contained in each file you created.
Application is called Mstr_nat, with one PROJECT called Orgs which will show the organizations that provide both training and volunteer opportunities that can be used to continue your Master Naturalist designation. After completing the initial training, each year Master Naturalists are required to volunteer 40 hours per year, plus 8 hours of additional training. This will provide you with updated designation and the annual pin.

There are several images used to indicate the location of training and volunteer opportunities to help users identify potential listings that apply to them as well as icons used commonly by the Wisconsin Master Naturalist group.

styles.css file for the formatting of the site
cript.js file for the javascript used in the application


## How to run your application.
When you first hit the main site, you are presented with the organization list, but no other functionality. You must Register to create a username, and then Login with that name to gain access to the additional features.

There are links at the top that act as a menu (and for mobile apps you will see a hamburger menu with the same links).

- Use the Events menu choice to switch to an Event list (this first menu changes to Orgs when you are events, so you can flip between the two main lists).
- Use the FILTER menu choice to see a list of filter fields you can use the find specific elements on your list view - the choices will vary depending on whether you are looking at the events list or the orgs list.
- You have menu options for adding Orgs or Events. If you are the person that adds these elements, you are permitted to edit them as well.
- if you are designated as a STAFF user (this can be done via the ADMIN interface. I didn't build that manually - you must use the \admin switch to get to it where the administrator user can designate someone as staff), you will be able to edit any record in the application. 

## Requirements
Application uses these django elements:
> django.contrib.auth import authenticate, login, logout
> django.db import IntegrityError
> django.http import  HttpResponseRedirect, JsonResponse
> django.urls import reverse
> django.shortcuts import render, redirect, get_object_or_404
> django.core.paginator import Paginator
> django.utils import timezone
> django.db.models import Q
> django.contrib import messages

Project location: 
https://github.com/me50/meckmeier.git
    project: web50/projects/2020/x/capstone

Screencast: https://youtu.be/HwAH8EJCAG0

Copilot recommendation for hosting:
Why Render fits your exact situation
$7/month for a production‑ready web service

Free PostgreSQL (small but enough for your data size)

Persistent disk so your data doesn’t vanish

Easy GitHub deploys

Django Admin works perfectly

No sleeping apps on paid tier

Outbound internet allowed

Handles your concurrency easily

