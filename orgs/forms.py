from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from collections import defaultdict
from .models import *

class OrgForm(forms.ModelForm):
    in_wisconsin = forms.BooleanField(
        label="WI",
        required=False,
        widget=forms.CheckboxInput()
    )

    org_url = forms.CharField(required=False)
    volunteer_url = forms.CharField(required=False)
    training_url = forms.CharField(required=False)

    class Meta:
        model = Organization
        fields = [
            'id', 'org_name', 'org_url', 'volunteer_url', 'training_url',
            'in_wisconsin', 'about', 'region_name', 'host', 'deleted', 'default_location'
        ]
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
        }

    def clean(self):
        cleaned_data = super().clean()

        for field in ["org_url", "volunteer_url", "training_url"]:
            url = cleaned_data.get(field)
            if url:
                url = url.strip()
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                cleaned_data[field] = url

        return cleaned_data
    def clean_org_name(self):
        name = self.cleaned_data.get("org_name", "").strip()

        qs = Organization.objects.filter(org_name__iexact=name)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise forms.ValidationError(
                "That organization already exists. Please search for it instead of creating a new one."
            )

        return name

class LocModal(forms.ModelForm):
    class Meta:
        model=Location
        fields = ["loc_name"]
        
class LocForm(forms.ModelForm):
    org_loc_url = forms.CharField(required=False)
    class Meta:
        model = Location
        fields = [ "loc_name", "physical_location", "address", "city_name", "county_id", "region_name", "state", "zip_code", "org_loc_url", "location_about", "contact_email"]
        widgets = {
            "location_about": forms.Textarea(attrs={
                "rows": 3,
                "placeholder": "e.g. Great Lakes Visitor Center, Eagle River Trail, UW sMadison Education Building"
            }),
            "org_loc_url": forms.TextInput(attrs={
                "placeholder": "https://www.yourorg.org/location"
            }),
        }
    def clean(self):
        cleaned_data = super().clean()

        for field in ["org_loc_url"]:
            url = cleaned_data.get(field)
            if url:
                url = url.strip()
                if not url.startswith(("http://", "https://")):
                    url = "https://" + url
                cleaned_data[field] = url

        return cleaned_data
    
class BaseLocationFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        all_names =[]
        for form in self.forms:
            if not hasattr(form, "cleaned_data"):
                continue
            if form.cleaned_data.get('DELETE'):
                continue 
            if form.cleaned_data:
                continue

            loc_name = form.cleaned_data.get('loc_name')
            physical = form.cleaned_data.get('physical_location')
            deleted = form.cleaned_data.get('deleted')

            if not loc_name or not physical or deleted:
                continue
            normalized_name = loc_name.strip().lower()

            if normalized_name in all_names:
                raise ValidationError(f"Duplicate location name '{loc_name}' is not allowed.")
            all_names.append(normalized_name)

            qs.Location.objects.filter(
                physical_location=True,
                deleted=False,
                loc_name__iexact=loc_name.strip()
            )
            if form.instance.pk:
                qs=qs.exclude(pk=form.instance.pk)
            if qs.exists():
                raise ValidationError(f"Location name '{loc_name}' already exists for another organization.")


LocationFormSet = inlineformset_factory(
    Organization,
    Location,
    fields = ['id','loc_name', 'region_name','physical_location','org_loc_url', 'contact_email',  'location_about',  'address', 'city_name','county_id', 'state', 'zip_code'],
    extra=0,
    can_delete=True,
    formset=BaseLocationFormSet,
)

class FilterForm(forms.Form):
    type = forms.ChoiceField(
        choices=[("", "Any"), ("v", "Volunteer Opportunity"), ("t", "Training")],
        required=False, 
        label="Type",
        widget=forms.Select(attrs={"class":"form-select"})
    )
    org= forms.ModelChoiceField(
        queryset=Organization.objects.filter(deleted=False).order_by ("org_name"),
        required=False,
        empty_label="Any",
        label="Org Name",
        widget=forms.Select(attrs={"class":"form-select"})
    )  
    my_orgs = forms.BooleanField(
        required=False,
        label="Show events for My Favorite Orgs"
    )
    county = forms.ModelChoiceField(
        queryset = County.objects.all().order_by("county_name"),
        required=False,
        empty_label="Any",
        label="County" ,
        widget=forms.Select(attrs={"class":"form-select"})       
    )
    REGION_CHOICES = [
        ("", "Any"),
        ("C", "Central"),
        ("EC", "East Central"),
        ("NE", "Northeast"),
        ("NW", "Northwest"),
        ("SC", "South Central"),
        ("SE", "Southeast"),
        ("SW", "Southwest"),
        ("St", "Statewide"),
    ]
    region = forms.ChoiceField(
        choices=REGION_CHOICES,
        required=False,
        label="Region",
        widget=forms.Select(attrs={"class":"form-select"})
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class":"form-control mr-2",
            "placeholder":"Search in org, location, event or description"
        })
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=EventCategory.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Event Categories"
    )

class EventFilterForm(forms.Form):
    session_mode = forms.ChoiceField(
    required=False,
    choices=[
        ("", "All formats"),
        ("i", "In person"),
        ("o", "Online"),
    ],
    widget=forms.RadioSelect
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
    activity_type = forms.ChoiceField(
        choices=[("", "Any"), ("v", "Volunteer"), ("t", "Training")],
        required=False, 
        label="Type",
        widget=forms.RadioSelect
    )
    org= forms.ModelChoiceField(
        queryset=Organization.objects.filter(deleted=False).order_by ("org_name"),
        required=False,
        empty_label="Any",
        label="Org Name",
        widget=forms.Select(attrs={"class":"form-select"})
    )  
    my_orgs = forms.BooleanField(
        required=False,
        label="Show events for Organizations I follow"
    )
    county = forms.ModelChoiceField(
        queryset = County.objects.all().order_by("county_name"),
        required=False,
        empty_label="Any",
        label="County" ,
        widget=forms.Select(attrs={"class":"form-select"})       
    )
    REGION_CHOICES = [
        ("", "Any"),
        ("C", "Central"),
        ("EC", "East Central"),
        ("NE", "Northeast"),
        ("NW", "Northwest"),
        ("SC", "South Central"),
        ("SE", "Southeast"),
        ("SW", "Southwest"),
        ("St", "Statewide"),
    ]
    region = forms.ChoiceField(
        choices=REGION_CHOICES,
        required=False,
        label="Region",
        widget=forms.Select(attrs={"class":"form-select"})
    )
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class":"form-control mr-2",
            "placeholder":"Search in org, location, event or description"
        })
    )
    categories = forms.ModelMultipleChoiceField(
        queryset=EventCategory.objects.all().order_by("name"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Event Categories"
    )

class OrgFilterForm(forms.Form):
    org= forms.ModelChoiceField(
        queryset=Organization.objects.filter(deleted=False).order_by ("org_name"),
        required=False,
        empty_label="Any",
        label="Org Name",
        widget=forms.Select(attrs={"class":"form-select"})
    )  
    my_orgs = forms.BooleanField(
        required=False,
        label="Show Followed Organizations"
    )
    has_v = forms.BooleanField(
        required=False,
        label="Has Volunteer Opportunities"
    )
    has_t = forms.BooleanField(
        required=False,
        label="Has Trainings"
    )
   
    REGION_CHOICES = [
        ("", "Any"),
        ("C", "Central"),
        ("EC", "East Central"),
        ("NE", "Northeast"),
        ("NW", "Northwest"),
        ("SC", "South Central"),
        ("SE", "Southeast"),
        ("SW", "Southwest"),
        ("St", "Statewide"),
    ]
    region = forms.ChoiceField(
        choices=REGION_CHOICES,
        required=False,
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

class LocFilterForm(forms.Form):
    org= forms.ModelChoiceField(
        queryset=Organization.objects.filter(deleted=False).order_by ("org_name"),
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
        queryset=Location.objects.filter(deleted=False).order_by ("loc_name"),
        required=False,
        empty_label="Any",
        label="Location Name",
        widget=forms.Select(attrs={"class":"form-select"})
    )
    has_v = forms.BooleanField(
        required=False,
        label="Has Volunteer Opportunities"
    )
    has_t = forms.BooleanField(
        required=False,
        label="Has Trainings"
    )
    county = forms.ModelChoiceField(
        queryset = County.objects.all().order_by("county_name"),
        required=False,
        empty_label="Any",
        label="County" ,
        widget=forms.Select(attrs={"class":"form-select"})       
    )
    REGION_CHOICES = [
        ("", "Any"),
        ("C", "Central"),
        ("EC", "East Central"),
        ("NE", "Northeast"),
        ("NW", "Northwest"),
        ("SC", "South Central"),
        ("SE", "Southeast"),
        ("SW", "Southwest"),
        ("St", "Statewide"),
    ]
    region = forms.ChoiceField(
        choices=REGION_CHOICES,
        required=False,
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

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        model = Profile
        fields = ["bio", "preferred_region", "include_online"]
        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "preferred_region": forms.Select(attrs={"class": "form-select"}),
            "include_online": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

class ActivityForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=EventCategory.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        
        model = Activity
        fields = ["org", "title", "description", "activity_type", "time_commitment", "categories", "date_description", "activity_url", "no_cost", "contact_email", "time_description"] 
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "expire_date": forms.DateInput(attrs={"type": "date"}),
            "date_description": forms.TextInput(attrs={"placeholder": "e.g., Ongoing or Wednesdays in June"}),
            "time_description": forms.TextInput(attrs={"placeholder": "e.g., 2 hours per week, or 9-11:30am"}),
            "deleted": forms.CheckboxInput(attrs={"style": "display:none;"}),
            "activity_url": forms.TextInput(attrs={"placeholder": "https://www.yourorg.org/eventpage"}),
            "contact_email": forms.EmailInput(attrs={"placeholder": "contact@yourorg.org"})
         
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields["activity_type"].required = True

        # ChoiceField (CharField w/ choices)
        self.fields["activity_type"].choices = [
            ("", "Select Type"),
        ] + [
            c for c in self.fields["activity_type"].choices if c[0] != ""
        ]
        
        
        
        grouped = defaultdict(list)

        # ✅ use the existing queryset (important habit)
        for cat in self.fields['categories'].queryset:
            grouped[cat.category_class].append((cat.id, cat.name))

        # ✅ Django-native grouped choices
        self.fields['categories'].choices = [
            (group, choices) for group, choices in grouped.items()
        ]
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

class FeedbackForm(forms.ModelForm):
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