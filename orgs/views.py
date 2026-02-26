from pkgutil import get_data
from django.contrib.auth import authenticate, login, logout

from django.db import IntegrityError
from django.http import  HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages


from orgs.models import *
from .forms import *

def index(request):
    

    q = request.GET.get("q","")
    queryset = Organization.objects.filter(deleted=False).order_by('org_name')
    get_data = request.GET.copy()

    if "org_id" in get_data and "org" not in get_data:
        get_data["org"]=get_data["org_id"]

    filter_form=OrgFilterForm(get_data or None)
    if filter_form.is_valid():
    
        data = filter_form.cleaned_data
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
            events__event_type='v'
                ).filter(
                    Q(events__date__gte=timezone.now()) | Q(events__online=True)
                ).distinct()

        if data.get("has_t"):
            queryset = queryset.filter(
            events__event_type='t'
                ).filter(
                    Q(events__date__gte=timezone.now()) | Q(events__online=True)
                ).distinct()


    orgs=Paginator(queryset, 5)
    page_number = request.GET.get('page')
    page_obj = orgs.get_page(page_number)

    followed_orgs = FollowOrg.objects.filter(profile=request.user.profile).values_list('followOrg_id', flat=True) if request.user.is_authenticated else []
    counties = County.objects.all()
    orgs =Organization.objects.filter(deleted=False).order_by("org_name")
    clean_get = request.GET.copy()
    clean_get.pop("page", None)

    return render(request, "orgs/index.html",
                  {
                    "organizations": page_obj,
                    "followed_orgs": followed_orgs, 
                    "q": q,
                    #"my_orgs":my_orgs,
                    "counties": counties,
                    #"county": county,
                    #"region": region,
                    "query_params": clean_get,
                    "orgs": orgs,
                    "filter_form": filter_form,
                  } )

def event_list(request):
    
    q = request.GET.get("q", "")
    queryset = Event.objects.filter(deleted=False).order_by("date")
    get_data = request.GET.copy()

    if "org_id" in get_data and "org" not in get_data:
        get_data["org"]=get_data["org_id"]

    if not get_data.get("filter_type"):
        get_data["filter_type"] = "u"

    filter_form=EventFilterForm(get_data or None)
 
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        
        if data.get("county") :
            queryset=queryset.filter(orgloc__county_id=data["county"])
        
        if data.get("org"):
            queryset=queryset.filter(org=data["org"])

        if data.get("my_orgs"):
            followed_orgs = request.user.profile.following_orgs.all()
            queryset = queryset.filter(org__in=followed_orgs)
            

        if data.get("region"):
            queryset=queryset.filter(
                Q(org__region_name=data["region"]) 
                | Q(orgloc__region_name=data["region"])
            )
       
        if data.get("categories"):
            queryset=queryset.filter(categories__in=data["categories"]).distinct()

        if data.get("event_type"):
            queryset = queryset.filter(event_type=data["event_type"])

        filter_type = data.get("filter_type")

        if  filter_type == "u":

            queryset = queryset.upcoming()

        elif filter_type == "o":
            queryset = queryset.online()

        elif filter_type == "p":
            queryset = queryset.past()
            
        elif filter_type == "a":
            queryset = queryset.all_visible()
        
        q=filter_form.cleaned_data.get("q")
        if data.get("q"):
            q=data["q"]
            queryset =queryset.filter(Q(event_name__icontains=q) 
                                    | Q(event_description__icontains=q)
                                    | Q(org__org_name__icontains=q)
                                    | Q(orgloc__loc_name__icontains=q)
                                    )


    events=Paginator(queryset, 5)
    page_number = request.GET.get('page')
    page_obj = events.get_page(page_number)
    orgs= Organization.objects.filter(deleted=False).order_by("org_name")
   
    clean_get = request.GET.copy()
    clean_get.pop("page", None)

    return render(request, "orgs/event_list.html",{
                    "events": page_obj,
                    "filter_form": filter_form,
                    "query_params": clean_get,
                    "orgs": orgs,
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
        loc_formset = OrgLocationFormSet(request.POST, instance=org)
        
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
        loc_formset = OrgLocationFormSet(instance=org)
        
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


def event_form_view(request, event_id=None):  
    view_only = request.resolver_match.url_name == "event_view"
    can_edit = False
    org_id = request.GET.get("org_id")

    
    if event_id:
        event = get_object_or_404(Event, id=event_id)   
        if event.org.owner == request.user.profile:
            can_edit = True
    else:
        event = None 
        form = EventForm(request.POST or None, org_id=org_id) 

    if request.user.profile.staff:
        can_edit=True

    if request.method == "POST" and not view_only:
        form = EventForm(request.POST, instance=event)
       
        if form.is_valid() :
            print("form is valid")
            event = form.save()
            messages.success(request, "Organization details saved successfully.")
            return redirect("event_edit", event_id=event.id)
        else:
            messages.error(request, "there are errors in the form.")
            print("form errors",form.errors)
            print("non field error", form.non_field_errors)
    else:
        form = EventForm(instance=event)
        if not event and org_id:
            try:
                org = Organization.objects.get(id=org_id)
                form.initial["org"]=org
            except Organization.DoesNotExist:
                pass
        
        
    if view_only:
        for field in form.fields.values():
            field.disabled = True

    return render(request, "orgs/event_form.html", {
        "form": form,
        "view_only": view_only,
        "event": event,
        "can_edit": can_edit,
        
    })

def load_orgloc(request):
    org_id = request.GET.get("org_id")

    
    if org_id:
        selected_qs =( 
            OrgLocation.objects
            .filter(org_id=org_id, deleted=False)
            .select_related("org")
            .order_by("loc_name"))
    else:
        selected_qs = OrgLocation.objects.none()
    
    # Get locations for the selected org - if you have one
    other_qs=(
        OrgLocation.objects
        .filter( deleted=False)
        .exclude(org_id=org_id)
        .select_related("org")
        .order_by("loc_name"))

    locations = list(selected_qs) + list(other_qs)

    data =[
        {
            "id": loc.id,
            "loc_name": f"{loc.loc_name} ({loc.org.org_name})"
        }
        for loc in locations    
    ]
   
    return JsonResponse(data, safe=False)
    
    


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
    
