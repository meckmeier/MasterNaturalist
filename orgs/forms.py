from dataclasses import field


from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from collections import defaultdict
from allauth.account.forms import SignupForm
from django.contrib.auth.models import User
from turnstile.fields import TurnstileField
from django.utils import timezone

from orgs.context_processors import state
from .models import *
from .services.helper_function import default_expire_date, normalize_url


class CustomSignupForm(SignupForm):
    turnstile = TurnstileField()
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    accept_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms of Service and Privacy Policy",
    )

    def __init__(self, *args, **kwargs):
        
        super().__init__(*args, **kwargs)
        

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"
        

    def save(self, request):
        user = super().save(request)

        user.first_name = self.cleaned_data.get("first_name", "").strip()
        user.last_name = self.cleaned_data.get("last_name", "").strip()
        user.save()

        profile, created = Profile.objects.get_or_create(user=user)
        profile.terms_accepted_at = timezone.now()
        profile.save()

        token = request.session.pop("pending_org_invite_token", None)

        if token:
            invite = OrgInvite.objects.filter(
                token=token,
                accepted=False,
            ).first()

            if invite:
                OrgManager.objects.get_or_create(
                    profile=profile,
                    org=invite.org,
                    defaults={"role": invite.role},
                )

                invite.accepted = True
                invite.accepted_at = timezone.now()
                invite.save()

        return user

class OrgEnrollmentForm(forms.ModelForm):
    turnstile = TurnstileField()
    org_url = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "https://www.yourorg.org"})
    )

    class Meta:
        model = OrganizationEnrollmentRequest
        fields = [
            "org_name",
            "org_url",
            "about",
            "region",
            "contact_name",
            "contact_email",
            "contact_title",
            "authorized",
            "message",
            "location_name",
            "address",
            "city",
            "zip",
        ]
        widgets = {
            "about": forms.Textarea(attrs={"rows": 5}),
        }
    def __init__(self, *args, state=None, **kwargs):
        super().__init__(*args, **kwargs)
        if state is None:
            raise ValueError("OrgForm requires a state")
        self.state = state

    def clean(self):
        cleaned_data = super().clean()

        for field in ["org_url", "volunteer_url", "training_url", ]:
            url = cleaned_data.get(field)
            if url:
                url = url.strip()
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                cleaned_data[field] = url

        return cleaned_data
    def clean_org_name(self):
        
        name = self.cleaned_data.get("org_name", "").strip()

        # Check approved organizations
        if Organization.objects.active().visible_in(self.state).filter(org_name__iexact=name).exists():
            raise forms.ValidationError(
                "That organization already exists."
            )

        # Check pending enrollment requests
        if OrganizationEnrollmentRequest.objects.filter(
            org_name__iexact=name,
            status="new",
            state = self.state
        ).exists():
            raise forms.ValidationError(
                "A request for that organization is already pending review."
            )

        return name
    
class OrgForm(forms.ModelForm):

    org_url = forms.CharField(required=False)
    volunteer_url = forms.CharField(required=False)
    training_url = forms.CharField(required=False)
    news_url=forms.CharField(required=False)
    class Meta:
        model = Organization
        fields = [
            'id', 'org_name', 'org_url', 'volunteer_url', 'training_url', 'news_url', 'news_source',
            'is_national','home_state','states_served', 'about', 'region',  'host', 'deleted', 'default_location'
            ,'example_org'
        ]
        labels = {"is_national": "National organization", "home_state": "Home state"}
        widgets = {
            "about": forms.Textarea(attrs={"rows": 5}),
            "org_url": forms.TextInput(attrs={
                "placeholder": "https://www.yourorg.org"
            }),
            "volunteer_url": forms.TextInput(attrs={
                "placeholder": "https://www.yourorg.org/volunteer"
            }),
            "training_url": forms.TextInput(attrs={
                "placeholder": "https://www.yourorg.org/training"
            }),
            "news_url": forms.TextInput(attrs={
                "placeholder": "https://www.yourorg.org/rss_feed or /news or /subscribe"
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["home_state"].queryset = State.objects.filter(is_active=True)
        self.fields["home_state"].disabled = True
        if self.instance and self.instance.pk:
            # editing: show the org's own home state
            field.queryset = State.objects.filter(pk=self.instance.home_state_id)

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("is_national") and not cleaned_data.get("home_state"):
            self.add_error("home_state", "Choose a home state, or mark the organization as national.")
            return cleaned_data
        
        for field in ["org_url", "volunteer_url", "training_url", "news_url"]:
            url = cleaned_data.get(field)
            if url:
                url = url.strip()
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                cleaned_data[field] = url

        return cleaned_data

class LocModal(forms.ModelForm):
    class Meta:
        model=Location
        fields = ["loc_name"]
        
class LocForm(forms.ModelForm):
    org_loc_url = forms.CharField(required=False)
    class Meta:
        model = Location
        fields = [ "loc_name", "physical_location", "address", "city_name", "county_id", "region", "us_state", "zip_code", "org_loc_url", "location_about", "contact_email", "latitude", "longitude", "deleted"]
        widgets = {
            "location_about": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "e.g. Great Lakes Visitor Center, Eagle River Trail, UW sMadison Education Building"
            }),
            "org_loc_url": forms.TextInput(attrs={
                "placeholder": "https://www.yourorg.org/location"
            }),
        }
    def __init__(self, *args, state=None, **kwargs):
        super().__init__(*args, **kwargs)
        if state is None:
            raise ValueError("LocForm requires a state")
        self.state = state
        #the location's own state wins.
        loc_state = state
        if self.is_bound:
            sid = self.data.get(self.add_prefix("us_state"))
            if sid:
                loc_state = State.objects.filter(pk=sid).first() or state
        elif self.instance.pk and self.instance.us_state_id:
            loc_state= self.instance.us_state
        
        self.fields["county_id"].queryset = County.objects.filter(state=loc_state).order_by("county_name")
        self.fields["region"].queryset = Region.objects.filter(state=state).order_by("name")
        # default only for a new location, and only if nothing is set yet
        if not self.instance.pk and not self.initial.get("us_state"):
            self.initial["us_state"] = state.pk
            
    def clean(self):
        cleaned_data = super().clean()
        st = cleaned_data.get("us_state")
        county = cleaned_data.get("county_id")
        region = cleaned_data.get("region")
        if st and county and county.state_id != st.pk:
            self.add_error("county_id", "County is not in the selected state.")
        if st and region and region.state_id != st.pk:
            self.add_error("region", "Region is not in the selected state.")
        for field in ["org_loc_url"]:
            url = cleaned_data.get(field)
            if url:
                url = url.strip()
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                cleaned_data[field] = url

        return cleaned_data
    



class LocationMergeForm(forms.Form):
    from_location = forms.ModelChoiceField(
        queryset=Location.objects.none().order_by("physical_location", "city_name"),
        label="Merge this location"
    )

    to_location = forms.ModelChoiceField(
        queryset=Location.objects.none().order_by("physical_location", "city_name"),
        label="Into this location"
    )

    def __init__(self, *args, state=None, **kwargs):
        super().__init__(*args, **kwargs)
        if state is None:
            raise ValueError("LocationMergeForm requires a state")
        self.state = state
        self.fields["from_location"].queryset = Location.objects.active().for_state(state).order_by("physical_location", "city_name")
        self.fields["to_location"].queryset = Location.objects.active().for_state(state).order_by("physical_location", "city_name")

    def clean(self):
        cleaned = super().clean()
        from_location = cleaned.get("from_location")
        to_location = cleaned.get("to_location")

        if from_location and to_location and from_location == to_location:
            raise forms.ValidationError("You cannot merge a location into itself.")

        return cleaned
    
class EventFilterForm(forms.Form):
    
    time=forms.ChoiceField(
        required=False,
        choices=[
            ("", "Any"),
            ("dated", "Dated"),
            ("ongoing", "Ongoing"),
        ],
        widget=forms.RadioSelect
    )
    ongoing = forms.BooleanField(
        required=False,
        label="Ongoing (no dates)"
    )
    start_date = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"],
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "placeholder": "YYYY-MM-DD"
        })
    )
    end_date = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y"],
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "placeholder": "YYYY-MM-DD"
        })
    )
    session_format = forms.MultipleChoiceField(
        choices=[ ("o", "Online"), ("i", "In Person"), ("s", "Self Selected Locations")],
        required=False,
        initial=["i", "o", "s"],    
        label="Format",
        widget=forms.CheckboxSelectMultiple,
    )
    activity_type = forms.ChoiceField(
        choices=[("", "Any"), ("v", "Volunteer"), ("t", "Training"), ("e", "Event")],
        required=False, 
        label="Type",
        widget=forms.RadioSelect
    )
    org= forms.ModelChoiceField(
        queryset=Organization.objects.none().order_by ("org_name"),
        required=False,
        empty_label="Any",
        label="Org Name",
        widget=forms.Select(attrs={"class":"form-select"})
    )  
    my_orgs = forms.BooleanField(
        required=False,
        label="MyFavorite Organizations' events"
    )
    has_cost = forms.BooleanField(
        required=False,
        label="Free events (no cost)"
    )
    new = forms.BooleanField(
        required=False,
        label="Activity added in past 2 weeks"
    )
    county = forms.ModelChoiceField(
        queryset = County.objects.all().order_by("county_name"),
        required=False,
        empty_label="Any",
        label="County" ,
        widget=forms.Select(attrs={"class":"form-select"})       
    )
    region = forms.ModelChoiceField(
        queryset = Region.objects.none().order_by("name"),
        required=False,
        empty_label="Any",
        label="Region",
        widget=forms.Select(attrs={"class":"form-select"})
    )
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class":"form-control mr-2",
            "placeholder":"Search in org, location, activity title, or description"
        })
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=EventCategory.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Categories"
    )
    month = forms.ChoiceField(
            required=False,
            label="Month",
            widget=forms.Select(attrs={"class": "form-select"})
        )

            
    def __init__(self, *args, state=None, **kwargs):
        super().__init__(*args, **kwargs)
        if state is None:
            raise ValueError("EventFilterForm requires a state")
        else:
            self.fields["org"].queryset = (
                    Organization.objects.active().visible_in(state).order_by("org_name")
                )
            self.fields["county"].queryset = (
                    County.objects.filter(state=state).order_by("county_name")
                )
            self.fields["region"].queryset = (
                    Region.objects.filter(state=state).order_by("name")
                )
        category_qs = EventCategory.objects.all().order_by("category_class", "name")
        self.fields["categories"].queryset = category_qs

        grouped = defaultdict(list)

        for cat in category_qs:
            group_name = cat.category_class
            grouped[group_name].append((cat.pk, cat.name))

        self.category_groups = list(grouped.items())

        if self.is_bound:
            selected = self.data.getlist(self.add_prefix("categories"))
        else:
            selected = self.initial.get("categories", [])

        self.selected_category_ids = [str(x) for x in selected]
        today = date.today()

        choices = [("", "All Months")]

        # Current month through next 11 months
        for i in range(12):
            month = (today.month - 1 + i) % 12 + 1
            year = today.year + ((today.month - 1 + i) // 12)

            value = f"{year}-{month:02d}"
            label = date(year, month, 1).strftime("%B %Y")

            choices.append((value, label))

        self.fields["month"].choices = choices
         
       

        
class OrgFilterForm(forms.Form):
    org= forms.ModelChoiceField(
        queryset=Organization.objects.none().order_by ("org_name"),
        required=False,
        empty_label="Any",
        label="Org Name",
        widget=forms.Select(attrs={"class":"form-select"})
    )  
    my_orgs = forms.BooleanField(
        required=False,
        label="Show Followed Organizations"
    )
    has_volunteer = forms.BooleanField(
        required=False,
        label="Volunteer",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )

    has_training = forms.BooleanField(
        required=False,
        label="Learn",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
   
    region = forms.ModelChoiceField(
        queryset=Region.objects.none().order_by ("name"),
        required=False,
        empty_label="Any",
        label="Region",
        widget=forms.Select(attrs={"class":"form-select"})
    )  
    
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class":"form-control mr-2",
            "placeholder":"Search in name, location or description"
        })
    )
    def __init__(self, *args, state=None, **kwargs):
        super().__init__(*args, **kwargs)
        if state is None:
            raise ValueError("OrgFilterForm requires a state")
        self.fields["org"].queryset = (
            Organization.objects.active().visible_in(state).order_by("org_name")
        )
        self.fields["region"].queryset = (
            Region.objects.filter(state=state).order_by("name")
        )

class LocFilterForm(forms.Form):
    org= forms.ModelChoiceField(
        queryset=Organization.objects.none().order_by ("org_name"),
        required=False,
        empty_label="Any",
        label="Org Name",
        widget=forms.Select(attrs={"class":"form-select"})
    )  
    my_orgs = forms.BooleanField(
        required=False,
        label="Show Followed Organizations"
    )
    loc = forms.ModelChoiceField(
        queryset=Location.objects.none().order_by ("loc_name"),
        required=False,
        empty_label="Any",
        label="Location Name",
        widget=forms.Select(attrs={"class":"form-select"})
    )
    activity_status = forms.ChoiceField(
        required=False,
        initial="has",
        choices=[
            ("has", "Has Activities"),
            ("volunteer", "Volunteer Only"),
            ("training", "Learn Only"),
            ("both", "Has Both"),
            ("all", "All Locations"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    county = forms.ModelChoiceField(
        queryset = County.objects.none().order_by("county_name"),
        required=False,
        empty_label="Any",
        label="County" ,
        widget=forms.Select(attrs={"class":"form-select"})       
    )
    region = forms.ModelChoiceField(
        queryset = Region.objects.none().order_by("name"),
        required=False,
        empty_label="Any",
        label="Region",
        widget=forms.Select(attrs={"class":"form-select"})
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class":"form-control mr-2",
            "placeholder":"Search in name, location or description"
        })
    )
    def __init__(self, *args, state=None, **kwargs):
        super().__init__(*args, **kwargs)
        if state is None:
            raise ValueError("LocFilterForm requires a state")
        self.fields["org"].queryset = Organization.objects.active().visible_in(state).order_by("org_name")
        self.fields["loc"].queryset = Location.objects.filter(deleted=False).for_state(state).order_by("loc_name")
        self.fields["county"].queryset = County.objects.filter(state=state)
        self.fields["region"].queryset = Region.objects.filter(state=state).order_by("name")

class ProfileForm(forms.ModelForm):

    class Meta:
        model = Profile
        fields = ["bio", "my_region", "include_online"]
        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "my_region": forms.Select(attrs={"class": "form-select"}),
            "include_online": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            
        }

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name", "username"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

class StaffUserSelectForm(forms.Form):
    user_id = forms.ModelChoiceField(
        queryset=User.objects.all().order_by("username"),
        label="Choose user"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["user_id"].widget.attrs["class"] = "form-control"


class StaffUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active", "is_staff"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"


class StaffProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["my_region", "include_online", "is_master_naturalist"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                field.widget.attrs["class"] = "form-control"


class ActivityForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=EventCategory.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:        
        model = Activity
        fields = ["org", "title", "description", "activity_type", "categories", "activity_url", "has_cost", "contact_email", "time_commitment", "prerequisites",  "deleted"] 
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "prerequisites": forms.TextInput(attrs={"placeholder": "e.g. Previous training, experience, or materials needed"}),
            
            "deleted": forms.CheckboxInput(attrs={"style": "display:none;"}),
            "activity_url": forms.TextInput(attrs={"placeholder": "https://www.yourorg.org/eventpage"}),
            "contact_email": forms.EmailInput(attrs={"placeholder": "contact@yourorg.org"})
         
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.fields["activity_type"].required = True

        self.fields["activity_type"].choices = [
            ("", "Select Type"),
        ] + [
            c for c in self.fields["activity_type"].choices if c[0] != ""
        ]

        category_qs = EventCategory.objects.all().order_by("category_class", "name")
        self.fields["categories"].queryset = category_qs

        grouped = defaultdict(list)

        for cat in category_qs:
            group_name = cat.category_class
            grouped[group_name].append((cat.pk, cat.name))

        self.category_groups = list(grouped.items())

        if self.is_bound:
            selected = self.data.getlist(self.add_prefix("categories"))
        elif self.instance and self.instance.pk:
            selected = self.instance.categories.values_list("pk", flat=True)
        else:
            selected = self.initial.get("categories", [])

        self.selected_category_ids = [str(x) for x in selected]
    def clean(self):   
        cleaned_data = super().clean()
        url = cleaned_data.get("activity_url")
        email = cleaned_data.get("contact_email")

        if not url and not email:
            message = "Provide either a URL or a contact email."
            self.add_error('activity_url', message)
            self.add_error('contact_email', message)
        
        return cleaned_data
    def possible_duplicate(self):
        title = self.cleaned_data.get("title")
        org = self.cleaned_data.get("org")

        return Activity.objects.filter(
            org=org,
            title__iexact=title
        ).exists()
    
class SessionForm(forms.ModelForm):
    start = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"placeholder": "YYYY-MM-DD"})
    )

    end = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(attrs={"placeholder": "YYYY-MM-DD"})
    )
   
    class Meta:
        model = Session
        fields = "__all__"
        widgets = {
            "session_comment":  forms.TextInput(attrs={"placeholder": "Session times (optional)"}),
            "format": forms.Select(),
            "location": forms.Select(attrs={"class": "form-select form-select-sm real-location-field"}),
        }
    def __init__(self, *args, org=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.org=org
        self.fields["session_format"].choices = [
            ("", "Select format"),
        ] + [
            c for c in self.fields["session_format"].choices if c[0] != ""
        ]

        include_ids = set()

        if org and org.default_location_id:
            include_ids.add(org.default_location_id)

        if self.is_bound:
            field_name = self.add_prefix("location")
            bound_location_id = self.data.get(field_name)
            if bound_location_id:
                include_ids.add(bound_location_id)

        elif self.instance and self.instance.pk and self.instance.location_id:
            include_ids.add(self.instance.location_id)

        if include_ids:
            self.fields["location"].queryset = Location.objects.filter(pk__in=include_ids)
        else:
            self.fields["location"].queryset = Location.objects.none()

        if (
            org
            and org.default_location_id
            and not self.is_bound
            and not (self.instance and self.instance.pk and self.instance.location_id)
        ):
            self.fields["location"].initial = org.default_location_id

class BaseSessionFormSet(BaseInlineFormSet):
    def __init__(self, *args, org=None, **kwargs):
        self.org = org
        super().__init__(*args, **kwargs)

    def get_form_kwargs(self, index):
        kwargs = super().get_form_kwargs(index)
        kwargs["org"] = self.org
        return kwargs
    
SessionFormSet = inlineformset_factory(
    Activity,
    Session,
    form=SessionForm,
    formset=BaseSessionFormSet,
    extra=0,       # number of blank forms shown initially
    min_num=1,
    validate_min=True,
    can_delete=True,
)
class GroupedCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    def optgroups(self, name, value, attrs=None):
        groups = {}

        for option_value, option_label in self.choices:
            category = self.choices.queryset.get(pk=option_value)
            group_name = category.category_class or "Other"

            if group_name not in groups:
                groups[group_name] = []

            groups[group_name].append((option_value, option_label))

        optgroups = []

        for index, (group_name, group_choices) in enumerate(groups.items()):
            subgroup = []
            for subindex, (option_value, option_label) in enumerate(group_choices):
                selected = str(option_value) in value if value else False

                subgroup.append(self.create_option(
                    name,
                    option_value,
                    option_label,
                    selected,
                    index,
                    subindex=subindex,
                    attrs=attrs,
                ))

            optgroups.append((group_name.title(), subgroup, index))

        return optgroups


class UploadFileForm(forms.ModelForm):
    class Meta:
        model = ActivityUpload
        fields = ["file"]

class PendingForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label="I have reviewed the pending data and confirm it is ready to be committed."
    )
    class Meta:
        model = Pending_Activity
        fields = ["confirm","org", "title", "description", "activity_type", "time_commitment", "categories", "date_description", "activity_url", "has_cost", "contact_email", "time_description", "prerequisites", "expire_date", "deleted"]

class FeedbackForm(forms.ModelForm):

    turnstile=TurnstileField()

    class Meta:
        model = Feedback
        fields = ["name", "email", "note", "page_url"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "note": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "page_url": forms.HiddenInput(),
        }



class AddOrgManagerForm(forms.Form):
    profile_id = forms.IntegerField(widget=forms.HiddenInput())
    role = forms.ChoiceField(choices=OrgManager.ROLE_CHOICES)

    def __init__(self, *args, org=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.org = org
        self.profile_obj = None

    def clean_profile_id(self):
        profile_id = self.cleaned_data["profile_id"]
        try:
            self.profile_obj = Profile.objects.select_related("user").get(pk=profile_id)
        except Profile.DoesNotExist:
            raise forms.ValidationError("Please select a valid user.")
        return profile_id

    def clean(self):
        cleaned_data = super().clean()

        if self.org and self.profile_obj:
            if OrgManager.objects.filter(org=self.org, profile=self.profile_obj).exists():
                self.add_error("profile_id", "That user is already a manager for this organization.")

        return cleaned_data

    def save(self):
        return OrgManager.objects.create(
            org=self.org,
            profile=self.profile_obj,
            role=self.cleaned_data["role"]
        )