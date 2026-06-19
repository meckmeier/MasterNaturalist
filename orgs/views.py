

from warnings import filters

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.core.management import call_command
from django.core.paginator import Paginator
from django.core.serializers.json import DjangoJSONEncoder
from django.db import IntegrityError
from django.db import transaction
from django.db.models import Q, Min, Prefetch, F
from django.http import  Http404, HttpResponseRedirect,  HttpResponse, HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.db.models import Count, Q

from datetime import date, timedelta
from pathlib import Path
from .utils import update_new_fields
import markdown
import json
import pandas as pd
from .services.csv_importer import CSVImporter
from orgs.services.activity_tracking import track_activity
from orgs.services.helper_function import get_county_region_from_zip, normalize_address_key, similarity, normalize_location_name


from collections import defaultdict
from io import StringIO
from orgs.models import *
from .forms import *

def sort_key(x):
    # Use date or expire_date; fallback to far-future
    d = getattr(x, "date", None) or getattr(x, "expire_date", None)
    if d is None:
        return date.max
    return d

@staff_member_required
def run_cleanup_old_imports(request):
    output = None

    if request.method == "POST":
        out = StringIO()

        call_command(
            "cleanup_old_imports",
            days=10,
            delete=True,
            stdout=out,
        )

        output = out.getvalue()

    return render(request, "orgs/upload/staff_run_cleanup_imports.html", {
        "output": output,
    })

@staff_member_required
def run_update_latlng(request):
    output = None

    if request.method == "POST":
        out = StringIO()

        call_command(
            "update_latlng",
            stdout=out,
            limit=10,
        )

        output = out.getvalue()

    return render(request, "orgs/staff_run_update_latlng.html", {
        "output": output,
    })

@staff_member_required
def org_enrollment_list(request):

    enrollments = OrganizationEnrollmentRequest.objects.order_by("-created_at")
    return render(request, "orgs/org_enrollment_list.html", {"enrollments": enrollments})

@staff_member_required
def org_deny(request, enrollment_id):

    enrollment = get_object_or_404(
        OrganizationEnrollmentRequest,
        id=enrollment_id
    )

    if request.method == "POST":
        enrollment.status = "d"
        enrollment.reviewed_at = timezone.now()
        enrollment.reviewed_by = request.user
        
        enrollment.save()
        email = enrollment.contact_email.lower().strip()
        send_mail(subject="Your request to add an organization on WildPaths Wisconsin has been DENIED",
                   message=f"""
                        Hello,

                        Your organization, {enrollment.org_name}, has been denied for WildPaths Wisconsin.

                        If you believe this request was denied unjustly, you may respond to this email with an explanation.


                        Thank you!
                        """,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[email],
                                fail_silently=False,
                            )
                                
        messages.success(request, "Organization request denied.")

    return redirect("org_enrollment_list")

@staff_member_required
@transaction.atomic
def org_approve(request, enrollment_id):
    enrollment = get_object_or_404(OrganizationEnrollmentRequest, id=enrollment_id)
    if request.method != "POST":
        return render(request, "orgs/org_approve.html", {"enrollment": enrollment})
    if enrollment.status=="a":
        messages.info(request, "This enrollment has already been approved.")
        return redirect("org_enrollment_list")
    if enrollment.status=="d":
        messages.info(request, "This enrollment has already been denied.")
        return redirect("org_enrollment_list")
    
    print("Creating org for enrollment:", enrollment.org_name)
    # Create the organization (it will be logged as created by the staff member approving it.)
    org = Organization.objects.create(
            org_name=enrollment.org_name,
            about=enrollment.about,
            org_url=enrollment.org_url,
            volunteer_url=enrollment.volunteer_url,
            training_url=enrollment.training_url,
            region_name=enrollment.region_name,
            in_wisconsin=True,
            created_by=request.user.profile,
            updated_by=request.user.profile,
        )
    path = reverse("org_mgmt")
    org_url = f"{settings.SITE_URL}{path}?org={org.id}"
    print("Created org id:", org.id)
    # Optionally, you could also create an OrgManager entry for the contact person here if you want them to have immediate access.
    email = enrollment.contact_email.lower().strip()
    user=User.objects.filter(email__iexact=email).first()
    if user and hasattr(user, "profile"):
        OrgManager.objects.get_or_create(profile=user.profile, org=org, role="owner")
        
        send_mail(subject="Organization Approved on WildPaths Wisconsin",
                   message=f"""
                        Hello,

                        Your organization, {org.org_name}, has been approved for WildPaths Wisconsin.

                        Please use this link to see the new organization:

                        {org_url}

                        Thank you!
                        """,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[email],
                                fail_silently=False,
                            )
    else:
        invite = OrgInvite.objects.create(
            org=org,
            email=email,
            role="owner",
            created_by=request.user.profile,
        )

        invite_url = request.build_absolute_uri(reverse("accept_org_invite", args=[invite.token]))
        send_mail(subject="Organization Approved on WildPaths Wisconsin",
                   message=f"""
                        Hello,

                        Your organization, {org.org_name}, has been approved for WildPaths Wisconsin.

                        Please use this link to create your login and manage the organization:

                        {invite_url}

                        Note: you will be asked to reconfirm your email during this process. Once you have
                        successfully create your username and are able to login, you may use this link to see the 
                        newly created organization management page: {org_url}
                        Thank you!
                        """,
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[email],
                                fail_silently=False,
                            )
                                
    # Mark the enrollment as approved
    enrollment.status = "a"
    enrollment.approved_by = request.user.profile
    enrollment.approved_at = timezone.now()

    enrollment.save()

    messages.success(request, f"Organization '{org.org_name}' has been approved and created.")
    return redirect("org_enrollment_list")

def landing(request):
     # view only shows the main landing page. all info is rendered in the html page.
     return render(
        request,
        "orgs/landing.html")


def orgs(request):
    # view that runs the org list - this page has it's own filter page.
    q = request.GET.get("q", "")
    locations_qs = Location.objects.active()
    active_filters = []


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
        
        activity_status = data.get("activity_status")
            
        if activity_status == "training":
            org_queryset = org_queryset.filter(
                activities__in=training_qs
            ).distinct()

        elif activity_status == "volunteer":
            org_queryset = org_queryset.filter(
                activities__in=volunteer_qs
            ).distinct()

        elif activity_status == "both":
            org_queryset = org_queryset.filter(
                activities__in=training_qs
            ).filter(
                activities__in=volunteer_qs
            ).distinct()

        elif activity_status == "none":
            org_queryset = org_queryset.filter(
                activities__isnull=True
            )

        
    
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
    result_count = org_queryset.count()
    
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
            "active_filters": active_filters,
            "result_count": result_count,
        }
    )

def follow_org(request, org_id):
    #utility that adds an org to the orgFollowers table or removes it if it is there.
    # once done it returns from where it was called.
    next_url = request.POST.get("next") or request.GET.get("next")
    org = Organization.objects.get(id=org_id)

    track_activity(request, "favorite_add", org=org)
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
    today = timezone.localdate()
    if not request.user.is_authenticated:
        return redirect("login")
    
    managers_qs=OrgManager.objects.all().select_related("profile__user")
    activities_qs = (
        Activity.objects
        .with_active_flag()   # ✅ your custom logic
        .annotate(
            next_session_start=Min(
                "sessions__start",
            )
        )
        .order_by(
            "-is_active",
            F("next_session_start").asc(nulls_last=True),
        )
    )
    locations_qs = Location.objects.active()

    # staff gets to see all the organizations
    if request.user.is_staff:
        orgs = (Organization.objects
        .active()
        .annotate(
            hasUploads =Exists(
                    ActivityUpload.objects.filter(organization=OuterRef("pk"))
                ))
        .prefetch_related(
            Prefetch(
                "locations", 
                queryset=locations_qs,
                to_attr="pre_locs"  # optional: lets you access org.active_locs
            ),
            Prefetch(
                "activities",
                queryset=activities_qs,
                to_attr="pre_activities"  # optional: access as org.active_activities
            ),
            Prefetch(
                "managed",
                queryset=managers_qs,
                to_attr="pre_mgrs"
            )
            )
        )
    # if you are not staff, you have to be in the OrgManagers table to see the org on this page.
    else:
        orgs = (
            Organization.objects.active()
            .filter(managed__profile=request.user.profile)
            .distinct()
            .annotate(
                has_uploads=Exists(
                    ActivityUpload.objects.filter(organization=OuterRef("pk"))
                ))
            .prefetch_related(
                Prefetch(
                    "locations",
                    queryset=locations_qs,
                    to_attr="pre_locs"  # optional: access as org.active_locs in template
                ),
                Prefetch(
                    "activities",
                    queryset=activities_qs,
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

def org_enroll(request):
    print("org_enroll called with method", request.method)
    if request.method == "POST":
        track_activity(request, "org_enroll", org=None)
        form = OrgEnrollmentForm(request.POST)
        print("org_enroll form errors", form.errors)
        if form.is_valid():
            print("org_enroll form is valid")
            enrollment = form.save(commit=False)

            if request.user.is_authenticated:
                enrollment.created_by = request.user.profile
                                                                        
            enrollment.save()
            
            print("Enrollment saved:", enrollment.id)
            # send email to staff
            staff_emails = list(
                User.objects.filter(is_staff=True)
                .exclude(email="")
                .values_list("email", flat=True)
            )
            print("staff emails", staff_emails)
            send_mail(
                subject="New Organization Enrollment Request",
                message=(
                    f"A new organization enrollment request has been submitted.\n\n"
                    f"Organization Name: {enrollment.org_name}\n"
                    f"Website: {enrollment.org_url}\n"
                    f"Contact Name: {enrollment.contact_name}\n"
                    f"Contact Email: {enrollment.contact_email}\n\n"
                    f"About: {enrollment.about}\n"
                    f"Review it in on your staff page."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=staff_emails,
                fail_silently=False,
            )

            return redirect("org_enroll_thanks")
        else:
            print("org_enroll form errors:", form.errors.as_json())
            print("POST data:", request.POST)
    else:
        form = OrgEnrollmentForm()

    return render(request, "orgs/org_enroll.html", {"form": form})

def org_enroll_thanks(request):
    return render(request, "orgs/org_enroll_thanks.html")


def accept_org_invite(request, token):
    invite = get_object_or_404(OrgInvite, token=token, accepted=False)
    print("INVITE EMAIL STORED:", invite.email)
    request.session["pending_org_invite_token"]=str(invite.token)
    request.session["pending_org_invite_email"]=invite.email
    
    if not request.user.is_authenticated:
        return redirect("account_signup")
    
    if request.user.email.lower() != invite.email.lower():
        messages.error(request, "This invitation was sent to a different email address than your account email. Please log in with the correct account or contact support.")
        return redirect("account_logout")
    
    OrgManager.objects.get_or_create(profile=request.user.profile, org=invite.org, role=invite.role)

    invite.accepted = True
    invite.accepted_at = timezone.now()
    invite.save()
    messages.success(request, f"You have accepted the invitation to manage {invite.org.org_name}.")
    return redirect("org_mgmt")

def apply_pending_org_invite(request):
    token = request.session.pop("pending_org_invite_token", None)

    if not token or not request.user.is_authenticated:
        return

    invite = OrgInvite.objects.filter(token=token, accepted=False).first()

    if invite:
        OrgManager.objects.get_or_create(
            profile=request.user.profile,
            org=invite.org,
            defaults={"role": invite.role},
        )

        invite.accepted = True
        invite.accepted_at = timezone.now()
        invite.save()

def org_create(request):
    # this is the view for adding a new org - it is now an OrganizationEnrollmentRequest.
    if request.method == "POST":
        form = OrgForm(request.POST)
        if form.is_valid():
            org = form.save(commit=False)
            org.created_by = request.user.profile
            org.updated_by = request.user.profile
            org.owner = request.user.profile
            org.save()
            if not OrgManager.objects.filter(org=org, profile=request.user.profile).exists():
                OrgManager.objects.create(
                    org=org,
                    profile=request.user.profile,
                    role='owner'  # if you added the role field
                )
            return redirect("org_edit", org_id=org.id)
    else:
        form = OrgForm()
    return render(request, "orgs/org_detail.html", {
        "form": form,
        "staff": request.user.is_staff if request.user.is_authenticated else False
        })

def org_edit(request, org_id):

    org = get_object_or_404(Organization, id=org_id)
    if not (
        request.user.is_staff or
        org.managed.filter(profile=request.user.profile).exists()
    ):
        return HttpResponseForbidden("You do not have permission to edit this organization.")
       
                                    
    if request.method == "POST" :
        form= OrgForm(request.POST, instance=org)
        
        if form.is_valid() :
            org = form.save(commit=False)
            if not org.created_by:
                org.created_by = request.user.profile
            org.updated_by = request.user.profile
            org.save()
            messages.success(request, "Organization added successfully.", extra_tags=f"orgmsg-{org.id}")
            return redirect(f"{reverse('org_mgmt')}#org-{org.id}")
        else:
            messages.error(request, "There are errors in the form.")

            #print("org form errors",form.errors)
            
            #print("non field error", form.non_field_errors())
            #if the forms are not valid - stay on the org_detail page.

    else:
        form=OrgForm(instance=org)
      
    # if it's just a get then display the org_detail form.    
    return render(request, "orgs/org_detail.html", {
                "org": org,
                "events": [],
                "form": form,
                "staff": request.user.is_staff if request.user.is_authenticated else False

                })

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
                return redirect(f"{reverse('locations')}?view=list&loc={loc.id}")
            else:
                loc = form.save(commit=False)
                loc.updated_by = request.user.profile
                loc.save()
                messages.success(request, f"Location '{loc.loc_name}' updated successfully!")
                return redirect(f"{reverse('locations')}?view=list&loc={loc.id}")
            
        else:
            #print("loc form errors",form.errors)
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
    active_filters = []

    volunteer = Session.objects.current().filter(
        
        activity__deleted=False,
        activity__org__deleted=False,
        activity__activity_type="v",
    )

    training = Session.objects.current().filter(
        activity__deleted=False,
        activity__org__deleted=False,
        activity__activity_type="t",
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
                                      | Q(location_about__icontains=q)
                                      ).distinct()
        activity_status = data.get("activity_status")
            
        if activity_status == "training":
            queryset = queryset.filter(
                sessions__in=training
            ).distinct()

        elif activity_status == "volunteer":
            queryset = queryset.filter(
                sessions__in=volunteer
            ).distinct()

        elif activity_status == "both":
            queryset = queryset.filter(
                sessions__in=training
            ).filter(
                sessions__in=volunteer
            ).distinct()

        elif activity_status == "none":
            queryset = queryset.exclude(
                Q(sessions__in=training) |
                Q(sessions__in=volunteer)
            )
        elif activity_status == "has":
            queryset = queryset.filter(
                Q(sessions__in=training) |
                Q(sessions__in=volunteer)
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
    #print("queryset is:", queryset)
    #print("type of queryset:", type(queryset))
    json_locs = json.dumps([
        {
            "id": loc.id,
            "name": loc.loc_name,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "county": loc.county_id.county_name if loc.county_id else "",
            "has_training": bool(loc.training),
            "has_volunteer": bool(loc.volunteer),
        }
        for loc in queryset
        if loc.latitude and loc.longitude
    ])
    result_count = queryset.count()

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
            "result_count": result_count,
            "active_filters": active_filters
        }
    )

@staff_member_required
def staff_user_manage(request):

    target_user = None
    user_form = None
    profile_form = None

    created_orgs = updated_orgs = None
    created_locations = updated_locations = None
    created_activities = updated_activities = None

    selected_user_id = request.GET.get("user_id") or request.POST.get("user_id")

    if selected_user_id:
        target_user = get_object_or_404(
            User.objects.select_related("profile"),
            id=selected_user_id
        )

        profile, created = Profile.objects.get_or_create(user=target_user)

        if request.method == "POST":
            user_form = StaffUserUpdateForm(request.POST, instance=target_user)
            profile_form = StaffProfileUpdateForm(request.POST, instance=profile)

            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                return redirect(f"{request.path}?user_id={target_user.id}")

        else:
            user_form = StaffUserUpdateForm(instance=target_user)
            profile_form = StaffProfileUpdateForm(instance=profile)


        created_orgs = Organization.objects.filter(created_by=profile).order_by("-created_at")
        updated_orgs = Organization.objects.filter(updated_by=profile).order_by("-updated_at")

        created_locations = Location.objects.filter(created_by=profile).order_by("-created_at")
        updated_locations = Location.objects.filter(updated_by=profile).order_by("-updated_at")

        created_activities = Activity.objects.filter(created_by=profile).order_by("-created_at")
        updated_activities = Activity.objects.filter(updated_by=profile).order_by("-updated_at")

    select_form = StaffUserSelectForm(
        initial={"user_id": target_user} if target_user else None
    )

    return render(request, "orgs/staff_user_manage.html", {
        "select_form": select_form,
        "target_user": target_user,
        "user_form": user_form,
        "profile_form": profile_form,
        "created_orgs": created_orgs,
        "updated_orgs": updated_orgs,
        "created_locations": created_locations,
        "updated_locations": updated_locations,
        "created_activities": created_activities,
        "updated_activities": updated_activities,
    })


@staff_member_required
def location_manage(request):
    duplicate_groups = (
        Location.objects
        .filter(deleted=False)
        .values("loc_name")
        .annotate(location_count=Count("id"))
        .filter(location_count__gt=1)
        .order_by("loc_name")
    )

    grouped_locations = []

    for group in duplicate_groups:
        locs = (
            Location.objects
            .filter(deleted=False, loc_name=group["loc_name"])
            .select_related("org", "county_id")
            .annotate(
                session_count=Count("sessions", distinct=True),
                activity_count=Count("sessions__activity", distinct=True),
            )
            .order_by("city_name", "address", "org__org_name")
        )

        grouped_locations.append({
            "name": group["loc_name"],
            "count": group["location_count"],
            "locations": locs,
        })

    all_locations = list(
        Location.objects
        .filter(deleted=False)
        .select_related("org", "county_id")
        .annotate(
            session_count=Count("sessions", distinct=True),
            activity_count=Count("sessions__activity", distinct=True),
        )
        .order_by("loc_name", "city_name", "address")
    )

    close_match_groups = []
    used_ids = set()

    for loc in all_locations:
        if loc.id in used_ids:
            continue

        matches = []

        for other in all_locations:
            if loc.id == other.id or other.id in used_ids:
                continue

            score = similarity(loc.loc_name, other.loc_name)

            if score >= 0.88:
                matches.append(other)

        if matches:
            group_locations = [loc] + matches

            for item in group_locations:
                used_ids.add(item.id)

            close_match_groups.append({
                "name": loc.loc_name,
                "count": len(group_locations),
                "locations": group_locations,
            })
    
    address_buckets = defaultdict(list)

    for loc in all_locations:
        address_key = normalize_address_key(loc)

        if address_key:
            address_buckets[address_key].append(loc)

    address_match_groups = []

    for address_key, locs in address_buckets.items():
        unique_names = {
            normalize_location_name(loc.loc_name)
            for loc in locs
            if loc.loc_name
        }

        if len(locs) > 1 and len(unique_names) > 1:
            address_match_groups.append({
                "name": locs[0].address,
                "count": len(locs),
                "locations": locs,
            })
    organizations = Organization.objects.filter(deleted=False).order_by("org_name")

    return render(request, "orgs/staff/location_manage.html", {
        "grouped_locations": grouped_locations,
        "organizations": organizations,
        "close_match_groups": close_match_groups,
        "address_match_groups": address_match_groups,
    })

@staff_member_required
@transaction.atomic
def location_action(request, location_id):
    location = get_object_or_404(Location, id=location_id, deleted=False)

    if request.method != "POST":
        return redirect("location_manage")

    action = request.POST.get("action")

    if action == "update_org":
        org_id = request.POST.get("org_id")

        if org_id:
            org = get_object_or_404(Organization, id=org_id, deleted=False)
            location.org = org
        else:
            location.org = None

        location.save(update_fields=["org"])
        messages.success(request, f"Updated owner organization for {location.loc_name}.")

    elif action == "merge":
        merge_into_id = request.POST.get("merge_into_id")

        if not merge_into_id:
            messages.error(request, "Choose a location to merge into.")
            return redirect("location_manage")

        target = get_object_or_404(Location, id=merge_into_id, deleted=False)

        if target.id == location.id:
            messages.error(request, "You cannot merge a location into itself.")
            return redirect("location_manage")

        moved_sessions = Session.objects.filter(
            location=location,
            deleted=False,
        ).update(location=target)

        location.deleted = True
        location.save(update_fields=["deleted"])

        messages.success(
            request,
            f"Merged {location.loc_name} into {target.loc_name}. "
            f"Moved {moved_sessions} session(s)."
        )

    elif action == "delete":
        active_sessions = Session.objects.filter(
            location=location,
            deleted=False,
            activity__deleted=False,
        ).count()

        if active_sessions > 0:
            messages.error(request, "You cannot delete a location that has sessions.")
            return redirect("location_manage")

        location.deleted = True
        location.save(update_fields=["deleted"])

        messages.success(request, f"Deleted empty location: {location.loc_name}.")

    else:
        messages.error(request, "Choose an action.")

    return redirect("location_manage")



def lookup_zip(request):
    county, region = get_county_region_from_zip(request.GET.get("zip_code"))

    return JsonResponse({
        "county_id": county.id if county else None,
        "region": region,
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


    logout(request)
    return HttpResponseRedirect(reverse("landing"))

    
@login_required
def profile_view(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form=UserForm(request.POST, instance=request.user)
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid() and user_form.is_valid():
            form.save()
            user_form.save()
            return redirect("profile")
    else:
        user_form = UserForm(instance=request.user)
        form = ProfileForm(instance=profile)

    return render(request, "orgs/profile.html", {
        "form": form,
        "user_form": user_form,})



def activities(request):
    q = request.GET.get("q", "")

    activity_id = request.GET.get("activity_id", "")
    current_activity = None
    active_filters = []

    if activity_id:
        current_activity = Activity.objects.filter(id=activity_id).first()
    
    today = timezone.now().date()
    # activities results... should i change this so we know what it is?
   
    queryset = Session.objects.current().select_related(
            "activity",        # follow FK from Session -> Activity
            "activity__org",   # Activity -> Organization
            "location"         # Session -> Location
        ).prefetch_related(
            "activity__categories"  # m2m from Activity -> categories
        )
    get_data = request.GET.copy()

    if "org_id" in get_data and "org" not in get_data:
        get_data["org"]=get_data["org_id"]
        
    
    filter_form=EventFilterForm(get_data or None)
    if filter_form.is_valid():
    
        data = filter_form.cleaned_data
        if data.get("upload"):
            queryset = queryset.filter()
        if data.get("org"):
            queryset=queryset.filter(activity__org__id=data["org"].id)
            active_filters.append(f"{data['org'].org_name} ")
            
        if data.get("my_orgs"):
            followed_orgs = request.user.profile.following_orgs.filter(deleted=False)
            queryset = queryset.filter(activity__org__id__in=followed_orgs)
            
            
        if data.get("county") :
            queryset=queryset.filter(location__county_id=data["county"]).distinct()
            active_filters.append(f"{data['county']} county ")

        if data.get("region"):
            queryset=queryset.filter(location__region_name=data["region"]).distinct()
            active_filters.append(f"{data['region']} region ")

        if data.get("q"):
            queryset =queryset.filter(Q(activity__org__org_name__icontains=q) 
                                    | Q(activity__description__icontains=q)
                                    | Q(location__loc_name__icontains=q)
                                        | Q(activity__title__icontains=q)
                                    ).distinct()
            active_filters.append(f"{data['q']} word search ")

        if data.get("activity_type"):
            queryset=queryset.filter(activity__activity_type=data["activity_type"]).distinct()
            if data["activity_type"] == "t":
                active_filters.append("Training")
            elif data["activity_type"] == "v":
                active_filters.append("Volunteer")
            

        if data.get("categories"):
            queryset = queryset.filter(activity__categories__id__in=data["categories"]).distinct()
            active_filters.append(f"Categories: {', '.join([str(c) for c in data['categories']])}")

        if data.get("ongoing"):
            queryset = queryset.filter(ongoing=True)
            active_filters.append("Ongoing")

        if data.get("has_cost"):
            queryset = queryset.filter(activity__has_cost=False).distinct()
            active_filters.append("Free only")

        if data.get("new"):
            two_weeks_ago = timezone.now() - timedelta(days=15)
            queryset = queryset.filter(activity__created_at__gte=two_weeks_ago)
            active_filters.append(f"Newly created")

        if data.get("start_date"):
            queryset = queryset.filter(start__gte=data["start_date"])
            active_filters.append(f"Start on or after: {data['start_date']}")

        if data.get("end_date"):
            queryset = queryset.filter(start__lte=data["end_date"])
            active_filters.append(f"Start on or before: {data['end_date']}")

        if data.get("session_mode") == "i":
            queryset = queryset.filter(session_format__in=["i", "b","s"])
            active_filters.append("In-person or Hybrid ")

        elif data.get("session_mode") == "o":
            queryset = queryset.filter(session_format__in=["o", "b"])
            active_filters.append("Online or Hybrid ")
    
        
        activity_id = request.GET.get("activity_id")

        if activity_id:
            queryset = queryset.filter(activity_id=activity_id)
            active_filters.append(f" {queryset.first().activity.title if queryset.exists() else 'N/A'}")

    clean_get = request.GET.copy()
    for p in ["page", "curr_page", "onl_page","ong_page"]:
        clean_get.pop(p, None)
    

    # Current: future start dates, sorted by start ascending
    upcoming_sessions = queryset.upcoming().order_by('start')
        
    # Ongoing: start <= now <= end, sorted by start ascending
    ongoing_sessions = queryset.ongoing().order_by('activity__title')
    #print("ongoing sessions", ongoing_sessions)
    result_count = queryset.count()
    

    # For client-side tab segmentation, pass the whole filtered queryset
    return render(request, "orgs/activities.html",{
                    "filter_form":filter_form,
                    "upcoming" : upcoming_sessions,
                    "ongoing": ongoing_sessions,
                    "query_params": clean_get,
                    "orgs": Organization.objects.filter(deleted=False).order_by("org_name"),
                    "cats": EventCategory.objects.all(),
                    "q":q, # i needed to pass this q from the filter_form so i can highlight the search text in the html,
                    "current_activity": current_activity,
                    "active_filters": active_filters,
                    "result_count": result_count,

                  } )

def get_grouped_categories():
    categories = EventCategory.objects.all().order_by("name")
    grouped_categories = defaultdict(list)
    grouped_ids = {}

    for cat in categories:
        group = cat.category_class or "Other"
        grouped_categories[group].append(cat)

    for group, cats in grouped_categories.items():
        grouped_ids[group] = [str(cat.id) for cat in cats]

    return grouped_categories, grouped_ids

def user_can_edit_org(request, org):
    if not request.user.is_authenticated:
        return False
    return request.user.is_staff or org.can_edit(request.user)

def _activity_form_workflow(request, org, activity, is_new=False):
    confirm = request.POST.get("confirm_duplicate")
    grouped_categories, grouped_ids = get_grouped_categories()

    if not user_can_edit_org(request, org):
        return redirect("org_mgmt")

    
    activity_form = ActivityForm(request.POST or None,instance=activity,)

    session_formset = SessionFormSet(
        request.POST or None,
        instance=activity,
        org=org,
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
                        "can_edit": True,
                        "duplicate_warning": True,
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
            activity_form.save_m2m()

            sessions = session_formset.save(commit=False)
            for s in sessions:
                if not s.created_by:
                    s.created_by = request.user.profile
                s.updated_by = request.user.profile
                s.activity = activity
                s.save()

            for s in session_formset.deleted_objects:
                s.delete()

            return redirect(f"{reverse('activities')}?activity_id={activity.id}")

    print("Session formset errors:", session_formset.errors)
    print("Management errors:", session_formset.management_form.errors)
    print("Main form errors:", activity_form.errors)

    return render(request, "orgs/activity_form.html", {
        "activity": activity,
        "activity_form": activity_form,
        "session_formset": session_formset,
        "can_edit": True,
        "duplicate_warning": False,
        "grouped_categories": grouped_categories,
        "grouped_ids": grouped_ids,
    })

def activity_create(request):
    org_id = request.GET.get("org") or request.POST.get("org")
    org = get_object_or_404(Organization, id=org_id)
    activity = Activity(org=org)
    #print("launching activity create for new org", org.org_name)
    return _activity_form_workflow(
        request=request,
        org=org,
        activity=activity,
        is_new=True,
    )

def activity_edit(request, activity_id):
    activity = get_object_or_404(Activity, id=activity_id)
    org = activity.org

    return _activity_form_workflow(
        request=request,
        org=org,
        activity=activity,
        is_new=False,
    )   

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
        if request.user.is_staff or  org.can_edit(request.user):
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
        org=activity.org,
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

        #print("Session formset errors:", session_formset.errors)
        #print("Management errors:", session_formset.management_form.errors)
        #print("Main form errors:", activity_form.errors)

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
    
    locations =  Location.objects.filter(deleted=False)
   
    if q:
        locations = locations.filter(
        Q(loc_name__icontains=q) |
        Q(city_name__icontains=q)
    )
    if org_id:
        org_locations = locations.filter(org_id=org_id)
        other_locations = locations.exclude(org_id=org_id)
    else:
        org_locations = Location.objects.none()
        other_locations = locations
    
    def serialize(loc):
        return {
            "id": loc.id,
            "loc_name": loc.loc_name,
            "label": loc.loc_name,
            "city_name": loc.city_name,
            "state": loc.state,
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
    training_qs = Activity.objects.training().filter(
        sessions__location=OuterRef("pk")
    )

    volunteer_qs = Activity.objects.volunteer().filter(
        sessions__location=OuterRef("pk")
    )

    locations_qs = Location.objects.filter(
        state="WI",
        latitude__isnull=False,
        longitude__isnull=False
    ).select_related("county_id").annotate(
        has_training=Exists(training_qs),
        has_volunteer=Exists(volunteer_qs),
    )
    locations_json = [
    {
        "id": loc.id,
        "name": loc.loc_name,
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "county": loc.county_id.county_name if loc.county_id else None,
        "has_training": loc.has_training,
        "has_volunteer": loc.has_volunteer,
    }
    for loc in locations_qs
    ]
    print ("location json", locations_json)
    context = {"locations": json.dumps(locations_json, cls=DjangoJSONEncoder)}
    # Render template
    return render(request, "orgs/map.html", context)

def test_email(request):
    print("starting email test")
    context = {}
    print("DEBUG =", settings.DEBUG)
    print("EMAIL_BACKEND =", settings.EMAIL_BACKEND)

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

@login_required
def org_manager_add(request, org_id):
    org = get_object_or_404(Organization, pk=org_id)

    if not (
        request.user.is_staff
        or org.managed.filter(id=request.user.profile.id).exists()
    ):
        return HttpResponseForbidden("You do not have permission to add managers.")

    if request.method == "POST":
        form = AddOrgManagerForm(request.POST, org=org)
        if form.is_valid():
            form.save()
            messages.success(request, "Manager added.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)

    return redirect(f"{reverse('org_mgmt')}#org-{org.id}")

def org_manager_search(request):
    q = request.GET.get("q", "").strip()
    results = []

    if q:
        profiles = (
            Profile.objects
            .select_related("user")
            .filter(
                user__email__iexact=q,
                
            )
           
        )

        for profile in profiles:
            user = profile.user
            display_name = f"{user.first_name} {user.last_name}".strip()

            results.append({
                "profile_id": profile.id,
                "email": user.email,
                "username": user.username,
                "display_name": display_name,
            })

    return JsonResponse({"results": results})

def org_manager_delete(request, pk):
    if request.method != "POST":
        return HttpResponseForbidden("Invalid request")

    org_manager = OrgManager.objects.filter(pk=pk).select_related("org").first()
    if not org_manager:
        return redirect("org_mgmt")

    if not (
        request.user.is_staff
        or org_manager.org.managed.filter(id=request.user.profile.id).exists()
    ):
        return HttpResponseForbidden("You do not have permission to delete this manager.") 

    if org_manager.profile_id == request.user.profile.id:
        return HttpResponseForbidden("You cannot remove yourself as a manager.")
    
    org_id = org_manager.org.id
    org_manager.delete()
    return redirect(f"{reverse('org_mgmt')}#org-{org_id}")


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

from orgs.services.mapping import build_mapping, build_dropdown_options, validate_mapping, build_default_mapping

@login_required
def upload_csv(request, org_id):
    org = get_object_or_404(Organization, id=org_id)

    if not (
        OrgManager.objects.filter(org=org, profile=request.user.profile).exists()
        or request.user.is_staff
    ):
        return HttpResponseForbidden()

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            upload = form.save(commit=False)
            upload.organization = org
            upload.uploaded_by = request.user

            importer = CSVImporter(upload)
            importer.read()

            if importer.errors:
                
                return render(request, "orgs/upload/upload.html", {
                    "form": form,
                    "errors": importer.errors,
                    "org": org,
                })
            upload.status = "csv_load"
            upload.save()
            return redirect("upload_map", upload_id=upload.id)

    else:
        form = UploadFileForm()

    return render(request, "orgs/upload/upload.html", {
        "form": form,
        "org": org,
        "errors": [],
    })

# Step 1: Map columns from csv to rawloaddata fields
def upload_map(request, upload_id):
    upload = get_object_or_404(ActivityUpload, id=upload_id)
    importer = CSVImporter(upload)
    importer.read()

    if importer.errors:
        upload.status = "error"
        upload.save(update_fields=["status"])
        return render(request, "orgs/upload/upload_map.html", {
            "errors": importer.errors,
            "upload": upload,
        })

    df = importer.df
    columns = list(df.columns)

    EXCLUDE_FIELDS = ["id", "upload", "row_number", "organization"]

    field_names = [
        f.name for f in RawLoadData._meta.get_fields()
        if not f.many_to_many
        and not f.one_to_many
        and f.name not in EXCLUDE_FIELDS
    ]

    dropdown_options = build_dropdown_options(columns, field_names)

    # Try automatic/default mapping first
    default_mapping = build_default_mapping(columns, field_names)
    default_errors = validate_mapping(default_mapping)

    if request.method == "GET" and not default_errors:
        request.session[f"mapping_{upload_id}"] = default_mapping

        upload.status = "csv_mapped"
        upload.save(update_fields=["status"])

        return redirect("upload_stage", upload_id=upload.id)

    if request.method == "POST":
        mapping = build_mapping(request.POST, columns)
        errors = validate_mapping(mapping)

        if errors:
            upload.status = "error"
            upload.save(update_fields=["status"])

            return render(request, "orgs/upload/upload_map.html", {
                "errors": errors,
                "columns": columns,
                "field_names": field_names,
                "upload": upload,
                "dropdown_options": dropdown_options,
            })

        request.session[f"mapping_{upload_id}"] = mapping

        upload.status = "csv_mapped"
        upload.save(update_fields=["status"])

        return redirect("upload_stage", upload_id=upload.id)

    return render(request, "orgs/upload/upload_map.html", {
        "upload": upload,
        "dropdown_options": dropdown_options,
        "errors": default_errors,
    })


# Step 2: Stage data
def upload_stage(request, upload_id):
    print("Starting upload_stage for upload:", upload_id)
    upload = get_object_or_404(ActivityUpload, id=upload_id)

    mapping = request.session.get(f"mapping_{upload_id}")
    if not mapping:
        return redirect("upload_map", upload_id=upload.id)

    importer = CSVImporter(upload, mapping=mapping)
    def fail_upload(step):
        upload.status = "error"
        upload.save(update_fields=["status"])

        UploadLog.objects.create(
            upload=upload,
            stage="csv_load",
            step=step,
            status="error",
            source_count=RawLoadData.objects.filter(upload=upload).count(),
            created_count=0,
            warning_count=0,
            error_count=len(importer.errors),
            message="\n".join(str(e) for e in importer.errors),
        )

        return render(request, "orgs/upload/upload_review_raw.html", {
            "upload": upload,
            "errors": importer.errors,
            "warnings": importer.warnings,
        })
    importer.read()
    
    if importer.errors:
        return fail_upload("reading file")

    importer.normalize()
    if importer.errors:
        return fail_upload("normalizing data")

    importer.validate()
    if importer.errors:
        return fail_upload("validating data")
    
    try:
        importer.process()
    except Exception as e:
        importer.errors.append(str(e))
        return fail_upload("saving raw data")

    upload.status = "raw_review"
    upload.save(update_fields=["status"])
    
    UploadLog.objects.create(
                upload=upload,
                stage="review_raw",
                step="upload_stage",
                status="success",
                source_count=RawLoadData.objects.filter(upload=upload).count(),
                skipped_count=RawLoadData.objects.filter(upload=upload, status="skipped").count(),
                created_count=RawLoadData.objects.filter(upload=upload, status="valid").count(),
                warning_count=RawLoadData.objects.filter(upload=upload, status="warning").count(),
                error_count=RawLoadData.objects.filter(upload=upload, status="error").count(),
                message="\n".join(str(w) for w in importer.warnings),
            )
    return redirect("upload_review_raw", upload_id=upload.id)

# Step 3: Review Raw table/ cleanup
@login_required
def upload_review_raw(request, upload_id):
    print("Starting upload_review_raw for upload:", upload_id)

    upload = get_object_or_404(ActivityUpload, id=upload_id)

    staged_rows = RawLoadData.objects.filter(upload=upload)
    error_rows = staged_rows.filter(status="error")
    warning_rows = staged_rows.filter(status = "warning")
    skipped_rows = staged_rows.filter(status="skipped")
    accepted_rows = staged_rows.exclude(
            status__in=["warning", "error", "skipped"]
        )

    if request.method == "POST":

        action = request.POST.get("action")
        skip_ids = request.POST.getlist("skip_row")

        RawLoadData.objects.filter(
            upload=upload,
            id__in=skip_ids
        ).update(status="skipped")

        if action == "continue":
            return redirect("upload_build_pending", upload_id=upload.id)

        return redirect("upload_review_raw", upload_id=upload.id)

    return render(request, "orgs/upload/upload_review_raw.html", {
        "upload": upload,
        "staged_rows": staged_rows,

        "error_rows": error_rows,
        "warning_rows": warning_rows,
        "accepted_rows": accepted_rows,
        "skipped_rows": skipped_rows,

        "total_count": staged_rows.count(),
        "error_count": error_rows.count(),
        "warning_count": warning_rows.count(),
        "accepted_count": accepted_rows.count(),
        "skipped_count": skipped_rows.count(),
    })

from orgs.services.pending import build_pending_for_upload

@login_required
def upload_build_pending(request, upload_id):
    upload = get_object_or_404(ActivityUpload, id=upload_id)

    result = build_pending_for_upload(upload)

    if result.errors:
        upload.status = "error"
        upload.save(update_fields=["status"])

        UploadLog.objects.create(
            upload=upload,
            stage="build_pending",
            step="building pending records",
            status="error",
            source_count=RawLoadData.objects.filter(upload=upload).count(),
            created_count=0,
            warning_count=len(result.warnings),
            error_count=len(result.errors),
            message="\n".join(str(e) for e in result.errors),
        )

        pending_locations = Pending_Location.objects.filter(
            source_upload=upload
        ).prefetch_related("pending_sessions").select_related("real_location")

        return render(request, "orgs/upload/upload_review_locations.html", {
            "upload": upload,
            "pending_locations": pending_locations,
            "errors": result.errors,
            "warnings": result.warnings,
        })

    upload.status = "review_locations"
    upload.save(update_fields=["status"])

    UploadLog.objects.create(
        upload=upload,
        stage="build_pending",
        step="building pending records",
        status="success",
        source_count=RawLoadData.objects.filter(upload=upload).count(),
        created_count=Pending_Location.objects.filter(source_upload=upload).count(),
        warning_count=len(result.warnings),
        error_count=0,
        message="\n".join(str(w) for w in result.warnings),
    )

    return redirect("upload_review_locations", upload_id=upload.id)

@login_required
def upload_review_locations(request, upload_id):
    print("Starting upload_review_locations for upload:", upload_id)

    upload = get_object_or_404(ActivityUpload, id=upload_id)

    def get_pending_locations():
        return (
            Pending_Location.objects
            .filter(source_upload=upload)
            .exclude(processing_status="merged")
            .prefetch_related("pending_sessions")
            .select_related("real_location")
            .order_by("loc_name", "city_name", "address")
        )

    pending_locations = get_pending_locations()
    errors = []
    warnings = []

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "continue":
            form_errors = []
            locations = list(pending_locations)

            try:
                with transaction.atomic():
                    for location in locations:
                        decision = request.POST.get(f"decision_{location.id}")
                        merge_into_id = request.POST.get(f"merge_into_{location.id}")
                        real_location_id = request.POST.get(f"real_location_{location.id}")

                        if decision == "matched":
                            

                            location.processing_status = "matched"
                            location.save(update_fields=["processing_status"])

                        elif decision == "different":
                            if not real_location_id:
                                form_errors.append(f"{location.loc_name}: choose an existing location.")
                                continue

                            real_location = Location.objects.filter(id=real_location_id).first()

                            if not real_location:
                                form_errors.append(
                                    f"{location.loc_name}: existing Location ID {real_location_id} was not found."
                                )
                                continue

                            location.real_location = real_location
                            location.processing_status = "matched"
                            location.save(update_fields=["real_location", "processing_status"])

                        elif decision == "merge":
                            if not merge_into_id:
                                form_errors.append(f"{location.loc_name}: choose a location to merge into.")
                                continue

                            if str(location.id) == str(merge_into_id):
                                form_errors.append(f"{location.loc_name}: cannot merge a location into itself.")
                                continue

                            parent = Pending_Location.objects.filter(
                                id=merge_into_id,
                                source_upload=upload,
                            ).first()

                            if not parent:
                                form_errors.append(f"{location.loc_name}: merge location was not found.")
                                continue

                            Pending_Session.objects.filter(
                                location=location,
                                source_upload=upload,
                            ).update(location=parent)

                            location.processing_status = "merged"
                            location.save(update_fields=["processing_status"])

                        elif decision == "create":
                            location.real_location = None
                            location.processing_status = "create"
                            location.save(update_fields=["real_location", "processing_status"])
                            
                        elif decision == "skip":
                            Pending_Session.objects.filter(
                                location=location,
                                source_upload=upload,
                            ).update(location=None)

                            location.real_location = None
                            location.processing_status = "skip"
                            location.save(update_fields=["real_location", "processing_status"])

                        else:
                            form_errors.append(f"{location.loc_name}: no decision was selected.")

                    if form_errors:
                        raise ValueError("Location review has form errors.")

            except ValueError:
                upload.status="error"
                upload.save(update_fields=["status"])
                UploadLog.objects.create(
                    upload=upload,
                    stage="upload_review_locations",
                    step="location decisions",
                    status="error",
                    source_count=Pending_Location.objects.filter(source_upload=upload).count(),
                    created_count=Pending_Location.objects.filter(
                        source_upload=upload,
                        processing_status="matched",
                    ).count(),
                    merged_count=Pending_Location.objects.filter(
                        source_upload=upload,
                        processing_status="merged",
                    ).count(),
                    skipped_count=Pending_Location.objects.filter(
                        source_upload=upload,
                        processing_status="skip",
                    ).count(),
                    warning_count=0,
                    error_count=len(form_errors),
                    message="\n".join(str(e) for e in form_errors),
                )

                return render(request, "orgs/upload/upload_review_locations.html", {
                    "upload": upload,
                    "pending_locations": get_pending_locations(),
                    "errors": form_errors,
                    "warnings": warnings,
                })
            upload.status="review_locations"
            upload.save(update_fields=["status"])
            UploadLog.objects.create(
                upload=upload,
                stage="upload_review_locations",
                step="location decisions",
                status="success",
                source_count=Pending_Location.objects.filter(source_upload=upload).count(),
                created_count=Pending_Location.objects.filter(
                    source_upload=upload,
                    processing_status="matched",
                ).count(),
                merged_count=Pending_Location.objects.filter(
                    source_upload=upload,
                    processing_status="merged",
                ).count(),
                skipped_count=Pending_Location.objects.filter(
                    source_upload=upload,
                    processing_status="skip",
                ).count(),
                warning_count=0,
                error_count=0,
            )

            messages.success(request, "Location decisions saved.")
            return redirect("upload_review_locations", upload_id=upload.id)

    return render(request, "orgs/upload/upload_review_locations.html", {
        "upload": upload,
        "pending_locations": pending_locations,
        "errors": errors,
        "warnings": warnings,
    })

@login_required
def upload_review_activities(request, upload_id):
    print("Starting upload_review_activities for upload:", upload_id)

    upload = get_object_or_404(ActivityUpload, id=upload_id)

    def get_pending_sessions():
        return (
            Pending_Session.objects
            .filter(source_upload=upload)
            .select_related(
                "activity",
                "location",
                "location__real_location",
            )
            .order_by("activity__title", "start")
        )

    pending_sessions = get_pending_sessions()

    errors = []
    warnings = []

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "continue":
            skip_ids = request.POST.getlist("skip_session")

            # Reset all sessions to valid first
            Pending_Session.objects.filter(
                source_upload=upload
            ).update(processing_status="valid")

            # Then mark checked sessions as skipped
            Pending_Session.objects.filter(
                source_upload=upload,
                id__in=skip_ids,
            ).update(processing_status="skip")

            # Skip activities that now have zero publishable sessions
            activities_to_skip = (
                Pending_Activity.objects
                .filter(source_upload=upload)
                .annotate(
                    publishable_session_count=Count(
                        "pending_sessions",
                        filter=~Q(pending_sessions__processing_status="skip"),
                    )
                )
                .filter(publishable_session_count=0)
            )

            skipped_activity_count = activities_to_skip.count()
            activities_to_skip.update(processing_status="skip")

            if skipped_activity_count:
                warnings.append(
                    f"{skipped_activity_count} activity record(s) were marked skipped because all of their sessions were skipped."
                )

            # Optional safety check
            valid_session_count = Pending_Session.objects.filter(
                source_upload=upload,
                processing_status="valid",
            ).count()

            if valid_session_count == 0:
                errors.append("You cannot publish because all sessions are skipped.")

            if errors:
                upload.status="error"
                upload.save(update_fields=["status"])
                UploadLog.objects.create(
                    upload=upload,
                    stage="upload_review_activities",
                    step="activity/session decisions",
                    status="error",
                    source_count=Pending_Session.objects.filter(source_upload=upload).count(),
                    created_count=Pending_Session.objects.filter(
                        source_upload=upload,
                        processing_status="valid",
                    ).count(),
                    skipped_count=Pending_Session.objects.filter(
                        source_upload=upload,
                        processing_status="skip",
                    ).count(),
                    warning_count=len(warnings),
                    error_count=len(errors),
                    message="\n".join(str(e) for e in errors),
                )

                return render(request, "orgs/upload/upload_review_activities.html", {
                    "upload": upload,
                    "pending_sessions": get_pending_sessions(),
                    "errors": errors,
                    "warnings": warnings,
                })
            upload.status="review_activities"
            upload.save(update_fields=["status"])
            UploadLog.objects.create(
                upload=upload,
                stage="upload_review_activities",
                step="activity/session decisions",
                status="success",
                source_count=Pending_Session.objects.filter(source_upload=upload).count(),
                created_count=Pending_Session.objects.filter(
                    source_upload=upload,
                    processing_status="valid",
                ).count(),
                skipped_count=Pending_Session.objects.filter(
                    source_upload=upload,
                    processing_status="skip",
                ).count(),
                warning_count=len(warnings),
                error_count=0,
                message="\n".join(str(w) for w in warnings),
            )

            return redirect("upload_review_activities", upload_id=upload.id)

    return render(request, "orgs/upload/upload_review_activities.html", {
        "upload": upload,
        "pending_sessions": pending_sessions,
        "errors": errors,
        "warnings": warnings,
    })

# Success page
def upload_success(request, upload_id):
    upload = get_object_or_404(ActivityUpload, id=upload_id)
    return render(request, "orgs/upload/upload_success.html", {
        "upload": upload,
        "location_count": Location.objects.filter(source_upload=upload).count(),
        "activity_count": Activity.objects.filter(source_upload=upload).count(),
        "session_count": Session.objects.filter(source_upload=upload).count(),
    })


@login_required
def upload_cancel_confirm(request, upload_id):
    upload = get_object_or_404(ActivityUpload, id=upload_id)
    next_url = request.GET.get("next")

    if not request.user.is_staff and upload.uploaded_by != request.user:
        messages.error(request, "You do not have permission to cancel this upload.")
        return redirect("upload_dashboard")

    if request.method == "POST":

        location_count = Pending_Location.objects.filter(source_upload=upload).count()
        activity_count = Pending_Activity.objects.filter(source_upload=upload).count()
        session_count = Pending_Session.objects.filter(source_upload=upload).count()
        msg = (
            f"Deleted {location_count} locations, "
            f"{activity_count} activities, and "
            f"{session_count} sessions."
        )
        Pending_Session.objects.filter(source_upload=upload).delete()
        Pending_Activity.objects.filter(source_upload=upload).delete()
        Pending_Location.objects.filter(source_upload=upload).delete()
        RawLoadData.objects.filter(upload=upload).delete()

        upload.status = "canceled"
        upload.save(update_fields=["status"])
        UploadLog.objects.create(
                upload=upload,
                stage="cancelled",
                step="removed staging tables",
                status="cancel",
                message = msg
            )
        messages.success(request, "Upload canceled and staged records removed.")
        return redirect("upload_dashboard")

    return render(request, "orgs/upload/upload_cancel_confirm.html", {
        "upload": upload,
        "next": next_url,
    })

@login_required
def upload_rollback_confirm(request, upload_id):
    upload = get_object_or_404(ActivityUpload, id=upload_id)

    context = {
        "upload": upload,
        "location_count": Location.objects.filter(source_upload=upload).count(),
        "activity_count": Activity.objects.filter(source_upload=upload).count(),
        "session_count": Session.objects.filter(source_upload=upload).count(),
    }

    return render(
        request,
        "orgs/upload/upload_confirm_rollback.html",
        context,
    )

@login_required
@require_POST
def upload_rollback(request, upload_id):
    upload = get_object_or_404(ActivityUpload, id=upload_id)
    with transaction.atomic():
        location_count = Location.objects.filter(source_upload=upload).count()
        activity_count = Activity.objects.filter(source_upload=upload).count()
        session_count = Session.objects.filter(source_upload=upload).count()
        msg = (
            f"Deleted {location_count} locations, "
            f"{activity_count} activities, and "
            f"{session_count} sessions."
        )
        UploadLog.objects.create(
                upload=upload,
                stage="rollback",
                step="removed uploaded data from production",
                status="rollback",
                message = msg
            )
        Session.objects.filter(source_upload=upload).delete()
        Activity.objects.filter(source_upload=upload).delete()
        Location.objects.filter(source_upload=upload).delete()

        upload.status = "rollback"
        upload.activities_created=activity_count*-1
        upload.sessions_created = session_count*-1
        upload.locations_created = location_count*-1

        upload.save(update_fields=["status", "activities_created", "sessions_created","locations_created"])
        
        messages.success(request, "Upload rolled back successfully.")

    url = reverse("upload_dashboard")
    return redirect(f"{url}?upload={upload_id}")
    
        
def normalize(text):
    return text.strip().lower() if text else ""


from orgs.services.publish import publish_pending_upload

@login_required
def upload_publish(request, upload_id):
    print("Starting upload_publish for upload:", upload_id)
    upload = get_object_or_404(ActivityUpload, id=upload_id)

    try:
        publish_pending_upload(upload_id, request.user.profile)
        messages.success(request, "Upload published successfully.")
        upload.status="published"
        upload.save(update_fields=["status"])
        UploadLog.objects.create(
                        upload=upload,
                        stage="Activities/Sessions",
                        step="activities published",
                        status="success",
                        source_count=RawLoadData.objects.filter(upload=upload).count(),
                        created_count=Pending_Activity.objects.filter(source_upload=upload, processing_status="valid").count(),
                        skipped_count=Pending_Activity.objects.filter(source_upload=upload, processing_status="skip").count(),
                        warning_count=0,
                        error_count=0,
                    )
        UploadLog.objects.create(
                        upload=upload,
                        stage="Locations",
                        step="locations published",
                        status="success",
                        source_count=RawLoadData.objects.filter(upload_id=upload_id).count(),
                        created_count=Pending_Location.objects.filter(source_upload=upload, processing_status="matched").count(),
                        merged_count=Pending_Location.objects.filter(source_upload=upload, processing_status="merged").count(),
                        skipped_count=Pending_Location.objects.filter(source_upload=upload, processing_status="skip").count(),
                        warning_count=0,
                        error_count=0,
                    )
        url = reverse("upload_dashboard")
        return redirect(f"{url}?upload={upload_id}")

    except Exception as e:
        print("PUBLISH ERROR:", e)
        messages.error(request, f"Upload could not be published: {e}")
        upload.status="error"
        upload.save(update_fields=["status"])
        UploadLog.objects.create(
                        upload=upload,
                        stage="Publish",
                        step="Publish Error",
                        status="error",
                        source_count=RawLoadData.objects.filter(upload_id=upload_id).count(),
                        created_count=Pending_Location.objects.filter(source_upload=upload, processing_status="matched").count(),
                        merged_count=Pending_Location.objects.filter(source_upload=upload, processing_status="merged").count(),
                        skipped_count=Pending_Location.objects.filter(source_upload=upload, processing_status="skip").count(),
                        warning_count=0,
                        error_count=0,
                    )
        return redirect("upload_review_activities", upload_id=upload_id)


@login_required
def upload_dashboard(request):
    upload_id = request.GET.get("upload")
    org_id = request.GET.get("org")

    
    if request.user.is_staff:
        uploads = ActivityUpload.objects.select_related(
            "organization", "uploaded_by"
        ) .prefetch_related("stage_logs").order_by("-uploaded_at")
    else:
        uploads = ActivityUpload.objects.filter(
            Q(uploaded_by=request.user) |
            Q(published_by=request.user.profile)
        ).select_related(
            "organization", "published_by", "uploaded_by"
        ).prefetch_related("stage_logs").order_by("-uploaded_at")

    if upload_id:
        uploads = uploads.filter(id=upload_id)

    if org_id:
        uploads = uploads.filter(organization=org_id)
        
    return render(request, "orgs/upload/upload_dashboard.html", {
        "uploads": uploads,
    })

from types import SimpleNamespace

def upload_results(request, upload_id):
    upload = get_object_or_404(ActivityUpload, id=upload_id)

   
    base_sessions = (
        Session.objects
        .filter(
            activity__source_upload=upload,
            activity__deleted=False,
            activity__org__deleted=False,
        )
        .select_related("activity", "activity__org", "location")
        .prefetch_related("activity__categories")
        .order_by("activity__title", "start")
    )

    volunteer = base_sessions.filter(activity__activity_type="v")
    training = base_sessions.filter(activity__activity_type="t")

    queryset = (
        Location.objects
        .filter(
            deleted=False,
            sessions__activity__source_upload=upload,
        )
        .distinct()
        .order_by("loc_name")
        .select_related("org")
        .prefetch_related(
            Prefetch("sessions", queryset=volunteer, to_attr="volunteer"),
            Prefetch("sessions", queryset=training, to_attr="training"),
        )
    )

    no_location_volunteer = volunteer.filter(location__isnull=True)
    no_location_training = training.filter(location__isnull=True)

    no_location = SimpleNamespace(
        id="noloc",
        loc_name="No Location",
        volunteer=list(no_location_volunteer),
        training=list(no_location_training),
    )
    locs = list(queryset)

    if no_location.volunteer or no_location.training:
            locs.append(no_location)
    print("UPLOAD:", upload.id)

    print("activities:", Activity.objects.filter(source_upload=upload).count())

    print("volunteer activities:", Activity.objects.filter(
        source_upload=upload,
        activity_type="v"
    ).count())

    print("training activities:", Activity.objects.filter(
        source_upload=upload,
        activity_type="t"
    ).count())

    print("sessions:", Session.objects.filter(
        activity__source_upload=upload
    ).count())

    print("sessions with location:", Session.objects.filter(
        activity__source_upload=upload,
        location__isnull=False
    ).count())

    print("volunteer sessions:", volunteer.count())
    print("training sessions:", training.count())

    for loc in locs:
        print(
            loc.loc_name,
            "vol:", len(loc.volunteer),
            "train:", len(loc.training)
        )
    return render(request, "orgs/upload/upload_results.html", {
        "upload": upload,
        "locs": locs,

    })



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


    html = markdown.markdown(
        md_content,
        extensions=[
            "extra",      # includes tables, fenced code, etc.
        ]
    )
   
    return render(request, "orgs/static_page.html", {
        "content": html,
        "title": filename.capitalize()
    })

def feedback_view(request):
    if request.method == "POST":
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Thanks for the feedback.")
            return redirect("feedback")
    else:
        initial_url = request.GET.get("page", "")
        form = FeedbackForm(initial={"page_url": initial_url})

    return render(request, "orgs/feedback.html", {"form": form})