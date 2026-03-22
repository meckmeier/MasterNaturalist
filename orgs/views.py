from django.contrib.auth.decorators import login_required

from django.contrib.auth import authenticate, login, logout

from django.db import IntegrityError
from django.http import  HttpResponseRedirect, JsonResponse, HttpResponse
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import date, timedelta
from django.db.models import Q, Prefetch, F
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
import json
from django.core.mail import send_mail

from orgs.models import *
from .forms import *

def sort_key(x):
    # Use date or expire_date; fallback to far-future
    d = getattr(x, "date", None) or getattr(x, "expire_date", None)
    if d is None:
        return date.max
    return d


def index_dense(request):

    q = request.GET.get("q", "")
    today = timezone.now().date()

    active_locations = Location.objects.filter(deleted=False)

    volunteer = (
    Activity.objects
        .filter( Q(expire_date__isnull=True) | Q(expire_date__gte=today), activity_type="v")
        .prefetch_related(
            Prefetch(
             "sessions",
             queryset=Session.objects.current().order_by("start")
         )
        ))
    
    training = (
        Activity.objects
        .filter( Q(expire_date__isnull=True) | Q(expire_date__gte=today), activity_type="t")
        .prefetch_related(
            Prefetch(
                "sessions",
                queryset=Session.objects.current().order_by("start")
            )
        ))
    
    queryset = (
        Organization.objects
        .filter(deleted=False)
        .order_by("org_name")
        .prefetch_related(   
            Prefetch(
                "activities",  # must match the related_name on model
                queryset=volunteer,
                to_attr="volunteer"  # this creates the attribute you reference later
            ),
            Prefetch(
                "activities",
                queryset=training,
                to_attr="training"
            ),
            Prefetch("locations", queryset=active_locations),
            
        )
    )
        
    get_data = request.GET.copy()

    if "org_id" in get_data and "org" not in get_data:
        get_data["org"]=get_data["org_id"]

    filter_form=OrgFilterForm(get_data or None)
    if filter_form.is_valid():
    
        data = filter_form.cleaned_data
        today = timezone.now().date()

        if data.get("org"):
            queryset=queryset.filter(id=data["org"].id)

        if data.get("my_orgs"):
            followed_orgs = request.user.profile.following_orgs.filter(deleted=False)
            queryset = queryset.filter(pk__in=followed_orgs)

        if data.get("county") :
            queryset=queryset.filter(locations__county_id=data["county"]).distinct()

        if data.get("region"):
            queryset=queryset.filter(region_name=data["region"]).distinct()

        if data.get("q"):
            queryset =queryset.filter(Q(org_name__icontains=q) 
                                      | Q(about__icontains=q)
                                      | Q(locations__loc_name__icontains=q)
                                      ).distinct()
        if data.get("has_v"):
            queryset = queryset.filter(
                activities__in=volunteer
            ).distinct()

        if data.get("has_t"):
            queryset = queryset.filter(
                activities__in=training
                ).distinct()
    
    followed_orgs = FollowOrg.objects.filter(profile=request.user.profile).values_list('followOrg_id', flat=True) if request.user.is_authenticated else []

    orgs=Paginator(queryset, 5)
    page_number = request.GET.get('page')
    page_obj = orgs.get_page(page_number)

    followed_orgs = FollowOrg.objects.filter(profile=request.user.profile).values_list('followOrg_id', flat=True) if request.user.is_authenticated else []
    counties = County.objects.all()
    all_orgs =Organization.objects.filter(deleted=False).order_by("org_name")
    clean_get = request.GET.copy()
    clean_get.pop("page", None)


    
    return render(
        request,
        "orgs/index_dense.html",
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
        }
    )


def activities(request):
    today = timezone.now().date()
    
    q = request.GET.get("q", "")
    get_data = request.GET.copy()
    sessions = Session.objects.filter(
            Q(start__gte=today) |  # future sessions
            Q(start__lte=today, end__gte=today) |  # ongoing sessions with an end
            Q(start__isnull=True , ongoing=True)  # started in the past, no end date
        ).order_by("start").select_related(
            "activity",        # follow FK from Session -> Activity
            "activity__org",   # Activity -> Organization
            "location"         # Session -> Location
        ).prefetch_related(
            "activity__categories"  # m2m from Activity -> categories
        )
    


    filter_form=EventFilterForm(get_data or None)
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        
        if data.get("categories"):
            sessions = sessions.filter(activity__categories__in=data["categories"]).distinct()
           
        if data.get("type"):
            sessions = sessions.filter(activity__activity_type=data["type"])
            
        if data.get("county") :
            sessions = sessions.filter(location__county_id=data["county"])
            
        if data.get("org"):
            sessions = sessions.filter(activity__org=data["org"])

        if data.get("my_orgs"):
            followed_orgs = request.user.profile.following_orgs.all()
            
            sessions = sessions.filter(activity__org__in=followed_orgs)
           
        if data.get("region"):
            sessions = sessions.filter(
                Q(activity__org__region_name=data["region"]) 
                | Q(location__region_name=data["region"])
            )
                  
        if data.get("q"):  
            sessions= sessions.filter(
                Q(activity__title=data["q"]) 
                   | Q(activity__description__icontains=data["q"])
                 )      
 

    clean_get = request.GET.copy()
    for p in ["page", "curr_page", "onl_page","ong_page"]:
        clean_get.pop(p, None)
    now = timezone.now()
    thirty_days_ago = timezone.now() - timedelta(days=30)

    # Current: future start dates, sorted by start ascending
    upcoming_sessions = sessions.filter(start__gt=now).order_by('start')
    
    # New: recently created, sorted by created_on descending
    new_sessions = sessions.filter(activity__created__gte=thirty_days_ago).order_by('-activity__created', F('start').asc(nulls_first=True))
    
    # Ongoing: start <= now <= end, sorted by start ascending
    ongoing_sessions = sessions.filter(Q(start__lt=now, end__lt=now) | Q(ongoing=True)).order_by('start')


    # For client-side tab segmentation, pass the whole filtered queryset
    return render(request, "orgs/activities.html",{
                    "upcoming" : upcoming_sessions,
                    "new": new_sessions,
                    "ongoing": ongoing_sessions,
                    "filter_form": filter_form,
                    "query_params": clean_get,
                    "orgs": Organization.objects.filter(deleted=False).order_by("org_name"),
                    "cats": EventCategory.objects.all(),
                    "q":q, # i needed to pass this q from the filter_form so i can highlight the search text in the html
                  } )

def events(request):
    today = timezone.now().date()
    
    q = request.GET.get("q", "")
    get_data = request.GET.copy()
    current_sessions = Session.objects.filter(
            start__isnull=False,  # ignore sessions without a start date
            ).filter(
                Q(start__gte=today) |  # future sessions
                Q(start__lte=today, end__gte=today) |  # ongoing sessions with an end
                Q(start__gte=today, end__isnull=True)  # started in the past, no end date
        
        ).order_by("start").select_related(
            "activity",        # follow FK from Session -> Activity
            "activity__org",   # Activity -> Organization
            "location"         # Session -> Location
        ).prefetch_related(
            "activity__categories"  # m2m from Activity -> categories
        )
    
    expired_sessions=Session.objects.filter(
        start__lte =today
        ).order_by("start").select_related(
            "activity",        # follow FK from Session -> Activity
            "activity__org",   # Activity -> Organization
            "location"         # Session -> Location
        ).prefetch_related(
             "activity__categories"  # m2m from Activity -> categories
        )
    
    online = Session.objects.filter(
        Q(end__gte=today) | Q(end__isnull=True),
        session_format__in=["o","b"],
        
            ).order_by("start").select_related(
                "activity",        # follow FK from Session -> Activity
                "activity__org",   # Activity -> Organization
                "location"         # Session -> Location
            ).prefetch_related(
                "activity__categories"  # m2m from Activity -> categories
        )

    ongoing = Session.objects.filter(
        Q(end__gte=today) | Q(end__isnull=True),
         ongoing=True
               
            ).order_by("start").select_related(
                "activity",        # follow FK from Session -> Activity
                "activity__org",   # Activity -> Organization
                "location"         # Session -> Location
            ).prefetch_related(
                "activity__categories"  # m2m from Activity -> categories
        )



    filter_form=EventFilterForm(get_data or None)
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        
        if data.get("categories"):
 
            current_sessions = current_sessions.filter(categories__in=data["categories"]).distinct()
            expired_sessions = expired_sessions.filter(categories__in=data["categories"]).distinct()
            online = online.filter(categories__in=data["categories"]).distinct()
            ongoing = ongoing.filter(categories__in=data["categories"]).distinct()

        if data.get("type"):

            current_sessions = current_sessions.filter(activity__activity_type=data["type"])
            expired_sessions= expired_sessions.filter(activity__activity_type=data["type"])
            online = online.filter(activity__activity_type = data["type"])
            ongoing = ongoing.filter(activity__activity_type = data["type"])

        if data.get("county") :
            current_sessions = current_sessions.filter(location__county_id=data["county"])
            expired_sessions=expired_sessions.filter(location__county_id=data["county"])
            
        if data.get("org"):

            current_sessions = current_sessions.filter(activity__org=data["org"])
            expired_sessions = expired_sessions.filter(activity__org=data["org"])
            online = online.filter(activity__org = data["org"])
            ongoing = ongoing.filter(activity__org = data["org"])

        if data.get("my_orgs"):
            followed_orgs = request.user.profile.following_orgs.all()
            
            current_sessions = current_sessions.filter(activity__org__in=followed_orgs)
            expired_sessions = expired_sessions.filter(activity__org__in=followed_orgs)
            online = online.filter(activity__org__in=followed_orgs)
            ongoing = ongoing.filter(activity__org__in=followed_orgs)     

        if data.get("region"):
            current_sessions = current_sessions.filter(
                Q(activity__org__region_name=data["region"]) 
                | Q(location__region_name=data["region"])
            )
            expired_sessions = expired_sessions.filter(
                Q(activity__org__region_name=data["region"]) 
                | Q(location__region_name=data["region"])
            )
            online = online.filter(
                Q(activity__org__region_name=data["region"]) 
                | Q(location__region_name=data["region"])
            )
            ongoing = ongoing.filter(
               Q(activity__org__region_name=data["region"]) 
                | Q(location__region_name=data["region"])
            )
            
        if data.get("q"):  
            current_sessions= current_sessions.filter(
                Q(activity__title=data["q"]) 
                   | Q(activity__description__icontains=data["q"])
                 )      
            expired_sessions = expired_sessions.filter(
                Q(activity__title=data["q"]) 
                   | Q(activity__description__icontains=data["q"])
                 )      
            online = online.filter(
                 Q(activity__title=data["q"]) 
                   | Q(activity__description__icontains=data["q"])
                 )   
            ongoing = ongoing .filter(
                Q(activity__title=data["q"]) 
                   | Q(activity__description__icontains=data["q"])
                 )   
             
    curr=Paginator(current_sessions, 5)
    curr_page = request.GET.get('curr_page')
    curr_page_obj = curr.get_page(curr_page)

    onl=Paginator(online, 5)
    onl_page = request.GET.get('onl_page')
    onl_page_obj = onl.get_page(onl_page)

    ong=Paginator(ongoing, 5)
    ong_page = request.GET.get('ong_page')
    ong_page_obj = ong.get_page(ong_page)

    exp=Paginator(expired_sessions, 5)
    exp_page = request.GET.get('exp_page')
    exp_page_obj = exp.get_page(exp_page)

    clean_get = request.GET.copy()
    for p in ["page", "curr_page", "onl_page","ong_page"]:
        clean_get.pop(p, None)

    return render(request, "orgs/activities.html",{
                    "sessions" : curr_page_obj,
                    "expired_sessions": exp_page_obj,
                    "online": onl_page_obj,
                    "ongoing": ong_page_obj,
                    "filter_form": filter_form,
                    "query_params": clean_get,
                    "orgs": Organization.objects.filter(deleted=False).order_by("org_name"),
                    "cats": EventCategory.objects.all(),
                    "q":q, # i needed to pass this q from teh filter_form so i can highlight the search text in the html
                  } )




def follow_org(request, org_id):

    org = Organization.objects.get(id=org_id)
    profile = Profile.objects.get(user=request.user)
    follow_relation, created = FollowOrg.objects.get_or_create(profile=profile, followOrg=org)
    
    if not created:
        follow_relation.delete()

    url = reverse("index");
    query_string = request.META.get('QUERY_STRING', '');
    if query_string:
        url = f"{url}?{query_string}"
    
    referer = request.META.get('HTTP_REFERER', None)
    if referer:
        return redirect(referer)
    else:
        return redirect("index")  # fallback
    

def org_detail(request, org_id=None, view_only=False):
    can_edit=False 
    view_only = request.resolver_match.url_name == "org_view"
    if org_id:
        org = get_object_or_404(Organization, id=org_id)
        if request.user.profile.staff or org.owner==request.user.profile:
            can_edit=True
    else:
        org = None
        if request.user.is_authenticated:
            can_edit=True
                                    
    if request.method == "POST" and not view_only:
        form= OrgForm(request.POST, instance=org)
        loc_formset = LocationFormSet(request.POST, instance=org, prefix="locations")
        
        if request.user.is_authenticated and not can_edit:
             messages.error(request, "You do not have permission to update this record.")
             return render(request, "orgs/org_detail.html", {
                "org": org,
                "events": [],
                "form": form,
                "view_only": view_only,
                "loc_formset": loc_formset,
                "can_edit": can_edit,
             })
      
        if form.is_valid() and loc_formset.is_valid():
            org = form.save(commit=False)
            if not org_id:
                org.owner = request.user.profile
            org.save()
            loc_formset.instance = org
            loc_formset.save()
            messages.success(request, "Organization details saved successfully.")
            return redirect("org_view", org_id=org.id)
        else:
            messages.error(request, "there are errors in the form.")
            print("org form errors",form.errors)
            print("loc formset errors", loc_formset.errors)
            print("non field error", form.non_field_errors())
            print("FORMSET is_valid:", loc_formset.is_valid())
            print("FORMSET non_form_errors:", loc_formset.non_form_errors())
            print("MANAGEMENT errors:", loc_formset.management_form.errors)
            print("TOTAL_FORMS:", request.POST.get("locations-TOTAL_FORMS"))
            print("INITIAL_FORMS:", request.POST.get("locations-INITIAL_FORMS"))

            return render(request, "orgs/org_detail.html", {
                "org": org,
                "events": [],
                "form": form,
                "view_only": view_only,
                "loc_formset": loc_formset,
                "can_edit": can_edit,
            })
        
    else:
        form = OrgForm(instance=org)
        loc_formset = LocationFormSet(instance=org, prefix="locations")
        
    if view_only:
        for field in form.fields.values():
            field.disabled = True
        
    return render(request, "orgs/org_detail.html", {
                "org": org,
                "events": [],
                "form": form,
                "view_only": view_only,
                "loc_formset": loc_formset,
                "can_edit": can_edit})


def loc_view(request, loc_id=None):
    can_edit=False 
    view_only = request.resolver_match.url_name == "loc_view"
    if loc_id:
        loc = get_object_or_404(Location, id=loc_id)
        if request.user.profile.staff or loc.org.owner==request.user.profile:
            can_edit=True
    else:
        loc = None
        if request.user.is_authenticated:
            can_edit=True
                                
    if request.method == "POST" and not view_only:
        form= LocForm(request.POST, instance=loc)
        if not form.is_valid():
            print(form.errors)
        if form.is_valid():
            loc = form.save(commit=False)
            
            loc.save()
            
            messages.success(request, "loc details saved successfully.")
            return redirect("loc_view", loc_id=loc.id)
        else:
            messages.error(request, "there are errors in the form.")
            print("loc form errors",form.errors)
            print("non field error", form.non_field_errors())
            return render(request, "orgs/location_form.html", {
                "loc": loc,
                "form": form,
                "view_only": view_only,
                "can_edit": can_edit,
             })
        
    else:
        form = LocForm(instance=loc)
        
    if view_only:
        for field in form.fields.values():
            field.disabled = True
        
    return render(request, "orgs/location_form.html", {
                "loc": loc,
                "form": form,
                "view_only": view_only,
                "can_edit": can_edit})


    

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "orgs/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "orgs/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


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
        return HttpResponseRedirect(reverse("index"))
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
    
def activity_form_view(request, activity_id=None): 
    
    view_only = request.resolver_match.url_name == "activity_view"
    can_edit = False
    # is this new or existing activity
    if activity_id:
        activity = get_object_or_404(Activity, id=activity_id)
        if request.user.profile.staff or activity.org.owner == request.user.profile:
            can_edit = True
    else:
        activity=Activity()
        if request.user.is_authenticated or request.user.staff:
            can_edit = True

    #figure out redirect
    if request.method == "POST" and not view_only:
        org_id= request.POST.get("org")
        location_id=request.POST.get("locations")

        activity_form = ActivityForm(request.POST, instance=activity)
        session_formset = SessionFormSet(request.POST, instance=activity, prefix="sessions")

        if activity_form.is_valid() and session_formset.is_valid():
            activity = activity_form.save()
            session_formset.instance=activity
            session_formset.save()

            print("Session formset errors:", session_formset.errors)
            print("Management errors:", session_formset.management_form.errors)
            print("main form errors" , activity_form.errors)
            if location_id:
                return redirect(f"{reverse('locations')}?#activity-{activity.id}")
            elif org_id:
                return redirect(f"{reverse('index_dense')}?org={org_id}")
            else:
                return redirect(f"{reverse('activities')}#activity-{activity.id}")

    #this is the GET part of the code
    else:
        org_id = request.GET.get("org")
        location_id = request.GET.get("location")
        if org_id:
                activity.org_id = org_id
        initial = []
        if location_id:      
                initial.append({
                     "location": location_id
                     })

        activity_form = ActivityForm(instance=activity)
        session_formset = SessionFormSet(
                instance=activity,
                initial=initial,
                prefix="sessions"
            )
        
    if view_only:
        for field in activity_form.fields.values():
            field.disabled = True

    return render(request, "orgs/activity_form.html", {
        "activity": activity,
        "activity_form": activity_form,
        "session_formset": session_formset,
        "can_edit": can_edit,
        "view_only": view_only,
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

    
from django.core.mail import send_mail
from django.http import HttpResponse

def test_email(request):
    try:
        send_mail(
            subject="Test Email from Postmark",
            message="This is a test email via Postmark + Anymail.",
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=["mary@eckmeier.com"],
            fail_silently=False,
        )
        return HttpResponse("Email sent successfully via Postmark!")
    except Exception as e:
        return HttpResponse(f"Error sending email: {str(e)}")