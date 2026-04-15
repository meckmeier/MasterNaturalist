

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Q, Prefetch, F
from django.http import  Http404, HttpResponseRedirect,  HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from datetime import date, timedelta
from pathlib import Path
from .utils import update_new_fields
import markdown
import json
import pandas as pd
from .services.csv_importer import CSVImporter

from collections import defaultdict

from orgs.models import *
from .forms import *

def sort_key(x):
    # Use date or expire_date; fallback to far-future
    d = getattr(x, "date", None) or getattr(x, "expire_date", None)
    if d is None:
        return date.max
    return d


def landing(request):
     # view only shows the main landing page. all info is rendered in the html page.
     return render(
        request,
        "orgs/landing.html")

def filter(request):
    # main activity filter page - 
    if request.method == "POST":
        filter_form = FilterForm(request.POST)

        if filter_form.is_valid():
            county=filter_form.cleaned_data.get("county")
            filters = {
                "region": filter_form.cleaned_data.get("region"),
                "county": county.id if county else None,
                "city": filter_form.cleaned_data.get("city"),
                "categories": [c.id for c in filter_form.cleaned_data.get("categories")],
                "type": filter_form.cleaned_data.get("type"),
                "org": filter_form.cleaned_data.get("org"),
                "my_orgs": filter_form.cleaned_data.get("my_orgs"),
                "q": filter_form.cleaned_data.get("q"),
            }

            request.session["filters"] = filters
            #print("from filter page", filters)

            return redirect("results")

    else:
        filter_form = FilterForm()

    categories = EventCategory.objects.all().order_by("name")

    grouped_categories = {}

    for cat in categories:
        group = cat.category_class or "Other"
        grouped_categories.setdefault(group, []).append(cat)

    return render(request, "orgs/filter.html", {
        "filter_form": filter_form,
        "grouped_categories": grouped_categories
    })

def results(request):
    # activities results... should i change this so we know what it is?
   
    sessions = Session.objects.current().select_related(
            "activity",        # follow FK from Session -> Activity
            "activity__org",   # Activity -> Organization
            "location"         # Session -> Location
        ).prefetch_related(
            "activity__categories"  # m2m from Activity -> categories
        )
    #print(request.session.get("filters"))
    filters = request.session.get("filters", {})
    
    if filters.get("categories"):
        sessions = sessions.filter(activity__categories__id__in=filters["categories"]).distinct()
           
    if filters.get("type"):
        sessions = sessions.filter(activity__activity_type=filters["type"])
            
    if filters.get("county") :
        sessions = sessions.filter(location__county_id__id=filters["county"])
            
    if filters.get("org"):
        sessions = sessions.filter(activity__org__id=filters["org"])

    if filters.get("my_orgs"):
        followed_orgs = request.user.profile.following_orgs.all()
            
        sessions = sessions.filter(activity__org__in=followed_orgs)
           
    if filters.get("region"):
        sessions = sessions.filter(
            Q(activity__org__region_name=filters["region"]) 
            | Q(location__region_name=filters["region"])
        )
                  
    if filters.get("q"):  
        
        sessions= sessions.filter(
            Q(activity__title=filters["q"]) 
                | Q(activity__description__icontains=filters["q"])
                )      
    q=filters.get("q")
    clean_get = request.GET.copy()
    for p in ["page", "curr_page", "onl_page","ong_page"]:
        clean_get.pop(p, None)
    
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Current: future start dates, sorted by start ascending
    upcoming_sessions = sessions.upcoming().order_by('start')
    
    # New: recently created, sorted by created_on descending
    new_sessions = sessions.filter(activity__created_at__gte=thirty_days_ago).order_by('-activity__created_at', F('start').asc(nulls_first=True))
    
    # Ongoing: start <= now <= end, sorted by start ascending
    ongoing_sessions = sessions.ongoing().order_by('activity__title')
    #print("ongoing sessions", ongoing_sessions)

    # For client-side tab segmentation, pass the whole filtered queryset
    return render(request, "orgs/results.html",{
                    "upcoming" : upcoming_sessions,
                    "new": new_sessions,
                    "ongoing": ongoing_sessions,
                    "query_params": clean_get,
                    "orgs": Organization.objects.filter(deleted=False).order_by("org_name"),
                    "cats": EventCategory.objects.all(),
                    "q":q, # i needed to pass this q from the filter_form so i can highlight the search text in the html

                  } )

def orgs(request):
    # view that runs the org list - this page has it's own filter page.
    q = request.GET.get("q", "")
    locations_qs = Location.objects.active()

    volunteer_qs = (
    Activity.objects.volunteer().prefetch_related(
            Prefetch(
             "sessions",
             queryset=Session.objects.current().order_by("start")
         )
        ))
    
    training_qs = (
        Activity.objects.training().prefetch_related(
            Prefetch(
                "sessions",
                queryset=Session.objects.current().order_by("start")
            )
        ))
    
    org_queryset = (
        Organization.objects.active()
        .order_by("org_name")
        .prefetch_related(   
            Prefetch(
                "activities",  # must match the related_name on model
                queryset=volunteer_qs,
                to_attr="pre_volunteer"  # this creates the attribute you reference later
            ),
            Prefetch(
                "activities",
                queryset=training_qs,
                to_attr="pre_training"
            ),
            Prefetch("locations", queryset=locations_qs, to_attr="pre_locs"),
            
        )
    )
        
    get_data = request.GET.copy()

    if "org_id" in get_data and "org" not in get_data:
        get_data["org"]=get_data["org_id"]

    filter_form=OrgFilterForm(get_data or None)
    if filter_form.is_valid():
    
        data = filter_form.cleaned_data
        if data.get("org"):
            org_queryset=org_queryset.filter(id=data["org"].id)

        if data.get("my_orgs"):
            followed_orgs = request.user.profile.following_orgs.active()
            org_queryset = org_queryset.filter(pk__in=followed_orgs)

        if data.get("county") :
            org_queryset=org_queryset.filter(locations__county_id=data["county"]).distinct()

        if data.get("region"):
            org_queryset=org_queryset.filter(region_name=data["region"]).distinct()

        if data.get("q"):
            org_queryset =org_queryset.filter(Q(org_name__icontains=q) 
                                      | Q(about__icontains=q)
                                      | Q(locations__loc_name__icontains=q)
                                      ).distinct()
        if data.get("has_v"):
            org_queryset = org_queryset.filter(
                activities__in=volunteer_qs
            ).distinct()

        if data.get("has_t"):
            org_queryset = org_queryset.filter(
                activities__in=training_qs
                ).distinct()
    
    orgs=Paginator(org_queryset, 5)
    page_number = request.GET.get('page')
    page_obj = orgs.get_page(page_number)

    followed_orgs = FollowOrg.objects.filter(profile=request.user.profile).values_list('followOrg_id', flat=True) if request.user.is_authenticated else []
    counties = County.objects.all()
    all_orgs =Organization.objects.active().order_by("org_name")
    clean_get = request.GET.copy()
    clean_get.pop("page", None)

    #this is code to test the prefetch data sets.
    # for org in org_queryset[:5]:  # just first few
    #    print(org.org_name, getattr(org, 'pre_volunteer', []))

    return render(
        request,
        "orgs/orgs.html",
        {
            "organizations": page_obj,
            "q": q,
            "followed_orgs": followed_orgs,
            "filter_form": OrgFilterForm(request.GET or None),
            "counties": counties,
            "query_params": clean_get,
            "orgs": all_orgs,
        }
    )

def follow_org(request, org_id):
    #utility that adds an org to the orgFollowers table or removes it if it is there.
    # once done it returns from where it was called.
    next_url = request.POST.get("next") or request.GET.get("next")
    org = Organization.objects.get(id=org_id)
    profile = Profile.objects.get(user=request.user)
    follow_relation, created = FollowOrg.objects.get_or_create(profile=profile, followOrg=org)
    
    if not created:
        follow_relation.delete()

    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=None):
        return redirect(next_url)
    else:
        return redirect("landing")  # fallback

def org_mgmt(request):
    # managing YOUR organizations - this is where you can edit them, add activities, etc.
    managers_qs=OrgManager.objects.all().select_related("profile__user")    
    
    if not request.user.is_authenticated:
        return redirect("login")
    
    # staff gets to see all the organizations
    if request.user.profile.staff:
        orgs = Organization.objects.active().prefetch_related(
            Prefetch(
                "locations", 
                queryset=Location.objects.active(),
                to_attr="pre_locs"  # optional: lets you access org.active_locs
            ),
            Prefetch(
                "activities",
                queryset=Activity.objects.with_active_flag(),
                to_attr="pre_activities"  # optional: access as org.active_activities
            ),
            Prefetch(
                "managed",
                queryset=managers_qs,
                to_attr="pre_mgrs"
            )
            )
    # if you are not staff, you have to be in the OrgManagers table to see the org on this page.
    else:
        orgs = (
            Organization.objects.active()
            .filter(managed__profile=request.user.profile)
            .distinct()
            .prefetch_related(
                Prefetch(
                    "locations",
                    queryset=Location.objects.active(),
                    to_attr="pre_locs"  # optional: access as org.active_locs in template
                ),
            Prefetch(
                "activities",
                queryset=Activity.objects.with_active_flag(),
                to_attr="pre_activities"  # optional: access as org.active_activities
            ),
            Prefetch(
                "managed",
                queryset=managers_qs,
                to_attr="pre_mgrs"
            )
            )
        )
    get_data = request.GET.copy()
    filter_form=OrgFilterForm(get_data or None)
    if filter_form.is_valid():
    
        data = filter_form.cleaned_data
        if data.get("org"):
            orgs=orgs.filter(id=data["org"].id)

    return render(request, "orgs/org_mgmt.html", {
        "organizations": orgs,
        "filter_form": OrgFilterForm(request.GET or None),
            })

def org_detail(request, org_id=None, view_only=False):
    #edit a single organization - only the organization fields.
    # in theory you should be in a can_edit state if you are on this page, but this just double checks it.

    can_edit=False

    # if there is an org_id then you are editing an existing org.
    if org_id:
        org = get_object_or_404(Organization, id=org_id)
        if org.can_edit(request.user):
            can_edit = True
    #if no org_id then you are creating a new one.
    else:
        org = None
        if request.user.is_authenticated:
            can_edit=True
                                    
    if request.method == "POST" and not view_only:
        form= OrgForm(request.POST, instance=org)
        

        if form.is_valid() :
            org = form.save(commit=False)
            if not org_id:
                org.owner = request.user.profile
            if not org.created_by:
                org.created_by = request.user.profile
            org.updated_by = request.user.profile
            org.save()
            if not OrgManager.objects.filter(org=org, profile=request.user.profile).exists():
                OrgManager.objects.create(
                    org=org,
                    profile=request.user.profile,
                    role='owner'  # if you added the role field
                )
            
            # once you have finished editing your organization record, you should go back to the org dashboard.
            messages.success(request, "Organization added successfully.", extra_tags=f"orgmsg-{org.id}")
            return redirect(f"{reverse('org_mgmt')}#org-{org_id}")
        else:
            messages.success(request, "there are errors in the form.", extra_tags=f"org-msg org-{org.id}")

            print("org form errors",form.errors)
            
            #print("non field error", form.non_field_errors())
            #print("FORMSET is_valid:", loc_formset.is_valid())
            #print("FORMSET non_form_errors:", loc_formset.non_form_errors())
            #print("MANAGEMENT errors:", loc_formset.management_form.errors)
            #print("TOTAL_FORMS:", request.POST.get("locations-TOTAL_FORMS"))
            #print("INITIAL_FORMS:", request.POST.get("locations-INITIAL_FORMS"))
            #if the forms are not valid - stay on the org_detail page.

            return render(request, "orgs/org_detail.html", {
                "org": org,
                "events": [],
                "form": form,
                "view_only": view_only,
                "can_edit": can_edit,
            })
        
    else:
        form = OrgForm(instance=org)
        
    if view_only:
        for field in form.fields.values():
            field.disabled = True
    # if it's just a get then display the org_detail form.    
    return render(request, "orgs/org_detail.html", {
                "org": org,
                "events": [],
                "form": form,
                "view_only": view_only,
                "can_edit": can_edit})

def loc_detail(request, loc_id=None):
    loc=get_object_or_404(Location, id=loc_id) if loc_id else None
    view_only= request.resolver_match.url_name =="loc_view"
    can_edit = True
    

    org_on_url = request.GET.get("org")
    
    if not org_on_url and not loc:
        messages.success(request, "Org context is needed for to create a new location", extra_tags=f"main-msg")
        return redirect(f"{reverse('org_mgmt')}")
    
    if request.method == "POST" and can_edit and not view_only:
        form= LocForm(request.POST, instance=loc) 
        
        if form.is_valid():
            if loc is None:
                loc = form.save(commit=False)  # get the unsaved Location instance
                loc.org_id = org_on_url
                loc.owner = request.user.profile
                loc.created_by = request.user.profile
                loc.updated_by = request.user.profile
                loc.save()
                messages.success(request, f"Location '{loc.loc_name}' saved successfully!")
                return redirect(f"{reverse('org_mgmt')}#org-{loc.org.id}")
            else:
                loc = form.save(commit=False)
                loc.updated_by = request.user.profile
                loc.save()
                messages.success(request, f"Location '{loc.loc_name}' updated successfully!")
                return redirect(f"{reverse('org_mgmt')}#org-{loc.org.id}")
            
        else:
            print("loc form errors",form.errors)
            messages.error(request, "there are errors in the form.")
            return render(request, "orgs/location_form.html", {
                "loc": loc,
                "form": form,
                "view_only": view_only,
                "can_edit": can_edit,
             })
        
    else:
        if loc:  # editing existing
            form = LocForm(instance=loc)
        else:  # creating new
            
            loc = Location(org_id=org_on_url) if org_on_url else Location()
            form = LocForm(instance=loc)
                
    if view_only:
        for field in form.fields.values():
            field.disabled = True
        
    return render(request, "orgs/location_form.html", {
                "loc": loc,
                "form": form,
                "view_only": view_only,
                "can_edit": can_edit,
               })
    
def locations(request):
    
    q = request.GET.get("q", "")
    today = timezone.now().date()

    volunteer = (Session.objects
        .filter(    Q(activity__expire_date__isnull=True) | Q(activity__expire_date__gte=today),
                activity__activity_type="v")
        )
    training = (Session.objects
                .filter ( Q(activity__expire_date__isnull=True) | Q(activity__expire_date__gte=today),
                         activity__activity_type="t")
        )
    queryset = (
        Location.objects
        .filter(deleted=False)
        .order_by("loc_name")
        .select_related(
            "org",        # follow FK from Session -> Activity
        )
        .prefetch_related(
            
            Prefetch(
                "sessions",  # must match the related_name on model
                queryset=volunteer,
                to_attr="volunteer"  # this creates the attribute you reference later
            ),
            Prefetch(
                "sessions",
                queryset=training,
                to_attr="training"
            )
        ))
    
     
    get_data = request.GET.copy()

    if "org_id" in get_data and "org" not in get_data:
        get_data["org"]=get_data["org_id"]

    filter_form=LocFilterForm(get_data or None)
    if filter_form.is_valid():
    
        data = filter_form.cleaned_data
        today = timezone.now().date()

        if data.get("org"):
            queryset=queryset.filter(org__id=data["org"].id)

        if data.get("loc"):
            queryset=queryset.filter(id=data["loc"].id)

        if data.get("my_orgs"):
            followed_orgs = request.user.profile.following_orgs.filter(deleted=False)
            queryset = queryset.filter(org__id__in=followed_orgs)

        if data.get("county") :
            queryset=queryset.filter(county_id=data["county"]).distinct()

        if data.get("region"):
            queryset=queryset.filter(region_name=data["region"]).distinct()

        if data.get("q"):
            queryset =queryset.filter(Q(org__org_name__icontains=q) 
                                      | Q(org__about__icontains=q)
                                      | Q(loc_name__icontains=q)
                                      | Q(about__icontains=q)
                                      ).distinct()
        if data.get("has_v"):
            queryset = queryset.filter(
                sessions__in=volunteer
            ).distinct()

        if data.get("has_t"):
            queryset = queryset.filter(
                sessions__in=training
                ).distinct()
    
   
    locs=Paginator(queryset, 5)
    page_number = request.GET.get('page')
    page_obj = locs.get_page(page_number)

    followed_orgs = FollowOrg.objects.filter(profile=request.user.profile).values_list('followOrg_id', flat=True) if request.user.is_authenticated else []
    counties = County.objects.all()
    all_locs =Location.objects.filter(deleted=False).order_by("loc_name")
    clean_get = request.GET.copy()
    clean_get.pop("page", None)
    import json
    print("queryset is:", queryset)
    print("type of queryset:", type(queryset))
    json_locs = json.dumps([
        {
            "id": loc.id,
            "name": loc.loc_name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "county": loc.county_id.county_name if loc.county_id else ""
        }
        for loc in queryset
        if loc.latitude and loc.longitude
    ])

    return render(
        request,
        "orgs/locations.html",
        {
            "locs": page_obj,
            "q": q,
            "followed_orgs": followed_orgs,
            "filter_form": filter_form,
            "counties": counties,
            "query_params": clean_get,
            "orgs": all_locs,
            "json_locs": json_locs,
        }
    )

def lookup_zip(request):
    zip_code = request.GET.get("zip_code", "").strip()
    print("zip_code",zip_code)
    if not zip_code:
        return JsonResponse({"county_id": None, "region": None})

    try:
        zip_row = ZipToCounty.objects.select_related("county").get(zip=zip_code)
    except ZipToCounty.DoesNotExist:
        return JsonResponse({"county_id": None, "region": None})

    county = zip_row.county
    print("county", county)
    return JsonResponse({
        "county_id": county.id,
        "region": county.region_name,  # adjust if needed
    })

@login_required
def org_set_default_location(request, org_id, loc_id):
    org = get_object_or_404(Organization, id=org_id)
    loc = get_object_or_404(Location, id=loc_id, org=org)

    if not org.can_edit(request.user):
        return HttpResponseForbidden()

    org.default_location = loc
    org.save(update_fields=["default_location"])

    messages.success(request, f"{loc.loc_name} is now the default location.")
    #return redirect("org_mgmt")
    url = reverse("org_mgmt")
    return redirect(f"{url}#org-{org.id}")

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("landing"))
        else:
            return render(request, "orgs/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "orgs/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("landing"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "orgs/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
            Profile.objects.create(user=user)
        except IntegrityError:
            return render(request, "orgs/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("landing"))
    else:
        return render(request, "orgs/register.html")
    
@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "orgs/profile.html", {"form": form})
    

def activity_detail(request, activity_id=None):
    is_new = activity_id is None
    confirm = request.POST.get("confirm_duplicate")

    categories = EventCategory.objects.all().order_by("name")
    grouped_categories = defaultdict(list)
    grouped_ids = {}

    for cat in categories:
        group = cat.category_class or "Other"
        grouped_categories[group].append(cat)

    for group, cats in grouped_categories.items():
        grouped_ids[group] = [str(cat.id) for cat in cats]

    # always in org context
    if is_new:
        org_id = request.GET.get("org") or request.POST.get("org")
        org = get_object_or_404(Organization, id=org_id)
        activity = Activity(org=org)
    else:
        activity = get_object_or_404(Activity, id=activity_id)
        org = activity.org

    can_edit = False
    if request.user.is_authenticated:
        if request.user.profile.staff or  org.can_edit(request.user):
            can_edit = True

    if not can_edit:
        return redirect("org_mgmt")

    default_location_id = ""
    if org and org.default_location_id:
        default_location_id = str(org.default_location_id)

    location_id = request.GET.get("location")
    initial = [{"location": location_id}] if request.method == "GET" and location_id else None

    activity_form = ActivityForm(
        request.POST or None,
        instance=activity,
    )

    session_formset = SessionFormSet(
        request.POST or None,
        instance=activity,
        initial=initial,
        prefix="sessions",
        form_kwargs={"org": org},
    )

    if request.method == "POST":
        if activity_form.is_valid() and session_formset.is_valid():
            activity = activity_form.save(commit=False)

            if is_new:
                activity.owner = request.user.profile

                if activity_form.possible_duplicate() and not confirm:
                    return render(request, "orgs/activity_form.html", {
                        "activity": activity,
                        "activity_form": activity_form,
                        "session_formset": session_formset,
                        "can_edit": can_edit,
                        "duplicate_warning": True,
                        "default_location_id": default_location_id,
                        "grouped_categories": grouped_categories,
                        "grouped_ids": grouped_ids,
                    })

            if not activity.owner:
                activity.owner = request.user.profile
            if not activity.created_by:
                activity.created_by = request.user.profile
            activity.updated_by = request.user.profile
            activity.org = org
            activity.save()

            sessions = session_formset.save(commit=False)
            for s in sessions:
                if not s.created_by:
                    s.created_by = request.user.profile
                s.updated_by = request.user.profile
                s.activity = activity
                s.save()

            for s in session_formset.deleted_objects:
                s.delete()

            return redirect(f"{reverse('org_mgmt')}#org-{org.id}")

        print("Session formset errors:", session_formset.errors)
        print("Management errors:", session_formset.management_form.errors)
        print("Main form errors:", activity_form.errors)

    return render(request, "orgs/activity_form.html", {
        "activity": activity,
        "activity_form": activity_form,
        "session_formset": session_formset,
        "can_edit": can_edit,
        "duplicate_warning": False,
        "default_location_id": default_location_id,
        "grouped_categories": grouped_categories,
        "grouped_ids": grouped_ids,
    })

def location_search(request):
    q = request.GET.get("q", "").lower()
    org_id = request.GET.get("org_id")
    
    locations = Location.objects.all()
   
    if q:
        locations = locations.filter(
        Q(loc_name__icontains=q) |
        Q(city_name__icontains=q)
    )

    org_locations = locations.filter(org_id=org_id)
    other_locations = locations.exclude(org_id=org_id)
    print("org_locations", org_locations)
    def serialize(loc):
        return {
            "id": loc.id,
            "label": loc.loc_name,
            "city": loc.city_name,
            "org_name": loc.org.org_name if loc.org else "",
        }

    return JsonResponse({
        "org_locations": [serialize(l) for l in org_locations],
        "other_locations": [serialize(l) for l in other_locations],
    })

def quick_location_create(request):
    org_id = request.GET.get("org_id") or request.POST.get("org_id")
    org = get_object_or_404(Organization, id=org_id)

    if request.method == "POST":
        form = LocModal(request.POST)

        if form.is_valid():
            location = form.save(commit=False)
            location.org = org
            location.created_by = request.user.profile
            location.updated_by = request.user.profile
            location.save()

            return JsonResponse({
                "success": True,
                "id": location.id,
                "label": location.loc_name,
                "city": location.city_name or "",
                "org_name": location.org.org_name if location.org else "",
            })

        return JsonResponse({
            "success": False,
            "errors": form.errors,
        }, status=400)

    form = LocModal()
    return render(request, "orgs/location_form_modal.html", {
        "form": form,
        "org": org,
    })

def activity_delete(request,activity_id=None):
    activity = get_object_or_404(Activity, id=activity_id)

    if request.method == "POST":
        org_id = activity.org.id
        activity.deleted=True
        activity.deleted_at=timezone.now()
        activity.save()
        return redirect(f"{reverse('org_mgmt')}#org-{org_id}")

    return render(request, "orgs/_activity_confirm_delete.html", {
        "activity": activity
    })

def map_view(request):

    locations_qs = Location.objects.filter(
        state="WI",
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related('county_id')

    locations_json = [
        {
            "id": loc.id,
            "name": loc.loc_name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "county": loc.county_id.county_name if loc.county_id else None,
        }
        for loc in locations_qs
    ]

    context = {"locations": json.dumps(locations_json, cls=DjangoJSONEncoder)}
    # Render template
    return render(request, "orgs/map.html", context)


def test_email(request):
    context = {}

    if request.method == "POST":
        sendto = request.POST.get("sendto")

        try:
            send_mail(
                subject="Test Email from Postmark",
                message="This is a test email via Postmark + Anymail.",
                from_email=None,  # uses DEFAULT_FROM_EMAIL
                recipient_list=[sendto],
                fail_silently=False,
            )
            context["success"] = True
            context["sendto"] = sendto

        except Exception as e:
            context["error"] = str(e)
            context["sendto"] = sendto

    else:
        # default value for first load
        context["sendto"] = "mary.eckmeier@gmail.com"

    return render(request, "orgs/test_email.html", context)

def superuser_required(user):
    return user.is_superuser

@user_passes_test(superuser_required)
def run_backfill(request):
    update_new_fields()
    return HttpResponse("Backfill complete")




def manager_add_page(request):
    org_id = request.GET.get("org")
    org = get_object_or_404(Organization, id=org_id)

    profiles = Profile.objects.select_related("user").all()
    #print("profiles", profiles)
    return render(request, "orgs/add_mgr.html", {
        "org": org,
        "profiles": profiles
    })

@require_POST
def add_manager(request):
    org_id = request.POST.get("org_id")
    profile_id = request.POST.get("profile_id")

    org = get_object_or_404(Organization, id=org_id)
    profile = get_object_or_404(Profile, id=profile_id)

    # prevent duplicates
    OrgManager.objects.get_or_create(org=org, profile=profile)

    return redirect("org_mgmt")

def debug_sessions(request):
    today = timezone.now().date()
    thirty_days_ago = timezone.now() - timedelta(days=30)

    qs = Session.objects.current().select_related(
        "activity", "activity__org"
    )

    # Toggle filters via URL params
    if request.GET.get("active") == "1":
        qs = qs.filter(
            deleted=False,
            activity__deleted=False,
            activity__org__deleted=False
        )

    if request.GET.get("upcoming") == "1":
        qs = qs.filter(start__gte=today)

    if request.GET.get("ongoing") == "1":
        qs = qs.filter(
            start__lte=today
        ).filter(
            Q(end__isnull=True) | Q(end__gte=today)
        )
    if request.GET.get("new") == "1":
        qs = qs.filter(activity__created_at__gte=thirty_days_ago).order_by('-activity__created_at', F('start').asc(nulls_first=True))

    # Optional: show only "bad" rows
    if request.GET.get("bad") == "1":
        qs = qs.filter(
            Q(deleted=True) |
            Q(activity__deleted=True) |
            Q(activity__org__deleted=True)
        )

    qs = qs.order_by("start")

    return render(request, "orgs/debug_sessions.html", {
        "sessions": qs,
        "today": today
    })

@login_required
def upload_csv(request, org_id):
    org = get_object_or_404(Organization, id=org_id)

    if not (OrgManager.objects.filter(org=org, profile=request.user.profile).exists()  or request.user.profile.staff):
        return HttpResponseForbidden()
    
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.organization =org
            upload.uploaded_by = request.user
            upload.save()
            return redirect("upload_map", upload_id=upload.id)
    else:
        form = UploadFileForm()
    return render(request, "orgs/upload.html", {"form": form})

# Step 1: Map columns
def upload_map(request, upload_id):
    upload = get_object_or_404(ActivityUpload, id=upload_id)
    
    # Read first row to show column headers
    df = pd.read_csv(upload.file) if upload.file.name.endswith(".csv") else pd.read_excel(upload.file, engine="openpyxl")
    first_row = list(df.columns)

    if request.method == "POST":
        # Example: user-submitted mapping comes as mapping_ColumnName fields
        mapping = {}
        for col in first_row:
            field = request.POST.get(f"mapping_{col}")
            if field:
                mapping[field] = col

        # Save mapping in session (or a model if you prefer)
        request.session[f"mapping_{upload_id}"] = mapping
        print("Received mapping:", mapping)  # Debug log
        # Update upload status
        upload.status = "mapped"
        upload.save()

        # Redirect to staging step
        return redirect("upload_stage", upload_id=upload.id)

    # GET request → show mapping form
    return render(request, "orgs/upload_map.html", {"upload": upload, "columns": first_row})

# Step 2: Stage data
def upload_stage(request, upload_id):
    upload = get_object_or_404(ActivityUpload, id=upload_id)
    
    
    # Example: you would get mapping from previous step
    mapping = request.session.get(f"mapping_{upload_id}")
    if not mapping:
        return redirect("upload_map", upload_id=upload.id)
    print ("Using mapping for staging:", mapping)  # Debug log
    importer = CSVImporter(upload, mapping=mapping)
    importer.read()
    importer.normalize()
    importer.validate()

    if importer.errors:
        # You could show errors or redirect to review page
        request.session[f"errors_{upload_id}"] = importer.errors
        return redirect("upload_review", upload_id=upload.id)

    importer.process()
    upload.status = "staged"
    upload.save()

    return redirect("upload_review", upload_id=upload.id)

# Step 3: Review / cleanup
def upload_review(request, upload_id):
    upload = get_object_or_404(ActivityUpload, id=upload_id)
    
    # Fetch all staged rows
    staged_rows = RawLoadData.objects.filter(upload=upload)
    
    # Fetch any errors from the staging process (from session)
    errors = request.session.pop(f"errors_{upload_id}", [])

    if request.method == "POST":
        # Handle row skipping
        skip_ids = request.POST.getlist("skip_row")
        RawLoadData.objects.filter(id__in=skip_ids).update(status="skipped")
        return redirect("upload_commit", upload_id=upload.id)

    return render(request, "orgs/upload_review.html", {
        "upload": upload,
        "staged_rows": staged_rows,
        "errors": errors
    })
# Step 4: Commit to final tables
def upload_commit(request, upload_id):
    upload = get_object_or_404(ActivityUpload, id=upload_id)
    staged_rows = RawLoadData.objects.filter(upload=upload, status="valid")
    
    # Implement logic to insert into your final Activity/Location tables here
    # e.g., for row in staged_rows: Activity.objects.create(...)

    upload.processed = True
    upload.status = "completed"
    upload.save()
    return redirect("upload_processing", upload_id=upload.id)

# Success page
def upload_success(request):
    return render(request, "orgs/upload_success.html")

def normalize(text):
    return text.strip().lower() if text else ""

def upload_processing(request, upload_id):
    #Purpose: Take the raw rows and map them into your four pending tables:
    #Location_Pending
    #Session_Pending
    #Activity_Pending
    print("Starting processing for upload:", upload_id)
    upload_info = get_object_or_404(ActivityUpload, id=upload_id)
    rows = RawLoadData.objects.filter(upload_id=upload_id)

    for row in rows:
        with transaction.atomic():
            print(f"Processing row {row.id}")

            # -----------------------------
            # Normalize
            # -----------------------------
            lkp_loc_name = normalize(row.location_name)
            lkp_city = normalize(row.city)
            lkp_address = normalize(row.address)
            lkp_title = normalize(row.title)

            # -----------------------------
            # 1. Check Pending_Location FIRST
            # -----------------------------
            pending_location = Pending_Location.objects.filter(
                loc_name__iexact=lkp_loc_name,
                city_name__iexact=lkp_city,
                address__iexact=lkp_address
            ).first()

            if pending_location:
                # ✅ Already staged — reuse it
                pass

            else:
                # -----------------------------
                # 2. Check real Location
                # -----------------------------
                matched_location = Location.objects.filter(
                    loc_name__iexact=lkp_loc_name,
                    city_name__iexact=lkp_city
                    
                ).first()

                # -----------------------------
                # 3. Create Pending_Location
                # -----------------------------
                if matched_location:
                    pending_location = Pending_Location.objects.create(
                        loc_name=matched_location.loc_name,
                        city_name=matched_location.city_name,
                        address=matched_location.address,
                        real_location=matched_location,
                        processing_status="matched",
                        source_upload_id=upload_id,
                        org=upload_info.organization
                    )
                else:
                    pending_location = Pending_Location.objects.create(
                        loc_name=row.location_name,
                        city_name=row.city,
                        address=row.address,
                        processing_status="new",
                        source_upload_id=upload_id,
                        org=upload_info.organization
                    )

   
    #Wrap each row (or batch) in transaction.atomic() to avoid partial inserts.
    return redirect("upload_approval", upload_id=upload_id)


def upload_approval(request, upload_id):

    # GET (this is the only query you need)
    sessions = Pending_Session.objects.select_related(
            "activity",
            "location",
            "location__real_location"
        ).filter(activity__source_upload_id=upload_id)
    return render(request, "orgs/upload_approval.html", {
        "sessions": sessions
    })

def upload_publish(request, upload_id):
    #urpose: Move approved rows from pending tables into production.
    #Logic:
    #Promote locations first (Location_Pending → Location)
    #Promote sessions (Session_Pending → Session)
    #Promote activities (Activity_Pending → Activity)
    #Wrap the entire promotion in a transaction per row (or per batch).
    #Mark pending rows as archived or approved for audit.
    #URL example: /promote_pending_activity/
    return render(request, "orgs/upload_success.html")

def upload_reject(request, upload_id):
    #Purpose: Mark rows as rejected and optionally log reasons.
    #Logic:
    #Update pending rows with status “rejected” and save any user comments.
    #Optionally, move rejected rows to a separate table for audit.
    #URL example: /reject_pending_activity/
    return render(request, "orgs/upload_success.html")

def test_html(request):
    activity=Activity.objects.first()
    activity_form = ActivityForm(instance=activity)
    default_location_id =""
    return render(request, "orgs/test_html.html", {
        "activity": activity,
        "activity_form": activity_form,
        "default_location_id": default_location_id,
        })


def render_markdown(request, filename):
    
    file_path = Path(settings.BASE_DIR) / f"{filename}.md"
    
    if not file_path.exists():
        raise Http404(f"{filename}.md not found at {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_content = markdown.markdown(md_content)
   
    return render(request, "orgs/legal_page.html", {
        "content": html_content,
        "title": filename.capitalize()
    })