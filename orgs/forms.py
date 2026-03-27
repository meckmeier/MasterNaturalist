from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError

from .models import *

class OrgForm(forms.ModelForm):
    in_wisconsin = forms.CharField(label='WI', widget=forms.CheckboxInput(), required=False)
    class Meta:
        model = Organization
        fields = ['id', 'org_name', 'org_url', 'volunteer_url','training_url' ,'in_wisconsin', 'about', 'region_name', 'host', 'deleted']
        widgets = {
            "about": forms.Textarea(attrs={
                "rows": 5,
            }),
        }

class LocForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = "__all__"
        widgets = {
            "location_about": forms.Textarea(attrs={
                "rows": 3,
            }),
        }
    
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
        label="Show My Favorite Orgs"
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
        label="Show My Favorite Orgs"
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
    class Meta:
        model = Activity
        fields = "__all__"
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "categories": forms.CheckboxSelectMultiple(),
            "expire_date": forms.DateInput(attrs={"type": "date"}),
            "date_description": forms.TextInput(attrs={"placeholder": "e.g., 'Ongoing weekly'"}),
        }   



class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = "__all__"
        widgets = {
            "start": forms.DateInput(attrs={"type": "date"}),
            "end": forms.DateInput(attrs={"type": "date"}),
            "format": forms.Select(),
        }
        
SessionFormSet = inlineformset_factory(
    Activity,
    Session,
    form=SessionForm,
    extra=0,       # number of blank forms shown initially
    min_num=1,
    validate_min=True,
    can_delete=True
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
class OrgManagerForm(forms.ModelForm):
    class Meta:
        model = OrgManager
        fields = ["profile", "role"]  # org is set in view

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # optional: nicer labels
        self.fields["profile"].label = "User"