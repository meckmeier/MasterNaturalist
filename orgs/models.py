
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import now
from datetime import timedelta

region_list = [
    ('C','Central')
    ,('EC', 'East Central')
    ,('NE', 'Northeast')
    ,('NW','Northwest')
    ,('SC','South Central')
    ,('SE','Southeast')
    ,('SW', 'Southwest')
    ,('St','Statewide')]

REGION_IMAGE_MAP = {
        'SC': 'orgs/images/SC.jpg',
        'NW': 'orgs/images/NW.jpg',
        'C':  'orgs/images/C.jpg',
        'NE': 'orgs/images/NE.jpg',
        'SW': 'orgs/images/SW.jpg',
        'SE': 'orgs/images/SE.jpg',
        'EC': 'orgs/images/CE.jpg',
        'St': 'orgs/images/St.jpg',
    }
   
class Commitment(models.Model):
    time= models.CharField(max_length=50)

    def __str__(self):
        return self.time

def one_year_from_now():
    return now().date() + timedelta(days=365)

class EventCategory(models.Model):
    name=models.CharField(max_length=50, unique=True)
    description=models.CharField(max_length=200, blank=True, null=True)
    category_class = models.CharField(max_length=200, blank=True, null=True)
    class Meta:
        ordering =["name"]

    def __str__(self):
        return self.name

class County(models.Model):
    county_name=models.CharField(max_length=100)
    region_name = models.CharField(max_length =100, choices = region_list, null=True, blank=True)

    class Meta:
        ordering = ["county_name"]
            
    def __str__(self):
        return self.county_name
    
class User(AbstractUser):
    pass

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio=models.TextField(blank=True)
    staff = models.BooleanField(default=False)
    preferred_region = models.CharField(max_length =100, choices = region_list, default='', blank=True)
     # Personalization Toggles
    include_online = models.BooleanField(default=True)
    
    def __str__(self):
        return f'{self.user.username}'
    
    @property
    def following_orgs(self):
        return Organization.objects.filter(following__profile=self)
    
    def following_count(self):
        return self.following.count()
    
class OrgQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted=False)

class Organization(models.Model):
    org_name = models.CharField(max_length=255, unique=True)
    org_url = models.URLField(max_length=200, default="", blank=True)
    in_wisconsin = models.BooleanField(default=True)
    host = models.BooleanField(default=False)
    about = models.TextField(default ="" , blank=True)
    region_name = models.CharField(max_length =100, choices = region_list, default='', blank=True)
    training_url = models.URLField(max_length=200, default="", blank=True)
    volunteer_url = models.URLField(max_length=200, default="", blank=True)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='owned_orgs', null=True, blank=True)
    deleted=models.BooleanField(default=False)
    deleted_at = models.DateTimeField( null=True, blank=True)
    created_by =models.ForeignKey(Profile, on_delete=models.SET_NULL, blank=True, null=True, related_name="created_orgs")
    created_at =models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_orgs")
    updated_at = models.DateTimeField(auto_now=True)

    objects=OrgQuerySet().as_manager() 
    all_objects= models.Manager()

    class Meta:
        ordering = ["org_name"]

    def __str__(self):
        return self.org_name
    
    def follower_count(self):
        return self.following.count()

    
    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        return (
            user.profile.staff
            or self.orgmanager_set.filter(user=user.profile,
                                          role__in=["owner","admin","editor"]).exists()
    )

    @property
    def region_image(self):
        return REGION_IMAGE_MAP.get(
            self.region_name,
            'orgs/images/default.jpg'
        )

class FollowOrg(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='followers')
    followOrg = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='following')

    def __str__(self):
        return f'{self.profile.user.username} follows {self.followOrg.org_name}'

class OrgManager(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='managers')   
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='managed')
    ROLE_CHOICES = [
        ("owner", "Owner"),
        ("admin", "Admin"),
        ("editor", "Editor"),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="editor")

    class Meta:
        unique_together = ("profile", "org")

    def __str__(self):
        return f'{self.profile.user.username} manages {self.org.org_name}'
    
class LocationQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted=False,
                           org__deleted=False)

        
class Location(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.SET_NULL, related_name="locations", blank=True, null=True)
    loc_name= models.CharField(max_length=255, unique=True)
    physical_location = models.BooleanField(default=True)
    address = models.CharField(max_length=255, default ='', blank=True)
    city_name = models.CharField(max_length=255, blank=True,null=True )
    county_id = models.ForeignKey(County, blank=True, null=True, on_delete=models.SET_NULL, related_name="county")
    region_name = models.CharField(max_length =100, choices = region_list, null=True, blank=True)
    state = models.CharField(max_length=100, default='WI', blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    org_loc_url = models.URLField(max_length=200, default="", blank=True)
    location_about = models.TextField(default="", blank=True , null=True)
    contact_email = models.EmailField(default="", blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='owned_locs', default="", null=True, blank=True)
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField( null=True, blank=True)
    created_by =models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name="created_locations")
    created_at =models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, related_name="updated_locations")
    updated_at = models.DateTimeField(auto_now=True)

    objects = LocationQuerySet().as_manager()       # default behavior
    all_objects = models.Manager()


    class Meta:
        ordering = ['loc_name']  # sort by loc_name by default  

    def __str__(self):
        return f"{self.loc_name}"
    
    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        return (
            user.profile.staff
            or self.org.orgmanager_set.filter(user=user.profile,
                                          role__in=["owner","admin","editor"]).exists()
    )
    
    @property
    def region_image(self):
        return REGION_IMAGE_MAP.get(
            self.region_name,
            'orgs/images/default.jpg'
        )
    
class ActivityQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted=False,
                           org__deleted=False)
    def volunteer(self):
        return self.active().filter(
            activity_type="v"
        )
    def training(self):
        return self.active().filter(
            activity_type="t"
        )
    
class Activity(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="activities")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    activity_type = models.CharField(max_length=1,
                                  choices=[("v","Volunteer Opportunity"),("t","Training" )])
    time_commitment = models.ForeignKey( Commitment, on_delete=models.SET_NULL, null=True, blank=True)
    categories = models.ManyToManyField(EventCategory, blank=True, related_name="category_activities")
    date_description = models.CharField(max_length=100, default='', blank=True, null=True)
    expire_date = models.DateField(default=one_year_from_now())
    activity_url = models.URLField(max_length=200, default="", blank=True)
    no_cost = models.BooleanField(default=False)
    contact_email = models.EmailField(default="", blank=True)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='owned_acts', default="", null=True, blank=True)
    deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by =models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_activities")
    created_at =models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_activities")
    updated_at = models.DateTimeField(auto_now=True)

    objects = ActivityQuerySet().as_manager()       # default behavior
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.title} ({self.org})"
    
    def can_edit(self, user):
        if not user.is_authenticated:
            return False
        return (
            user.profile.staff
            or self.org.orgmanager_set.filter(user=user.profile,
                                          role__in=["owner","admin","editor"]).exists()
    )
    
    @property
    def is_newly_added(self):
        return self.created_at >= timezone.now() - timedelta(days=30)



class SessionQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            deleted=False,
            activity__deleted=False,
            activity__org__deleted=False
        )
    def current(self):
        today = timezone.now().date()

        return self.active().filter(
            Q(start__isnull=True) |
            Q(start__gte=today) |
            (Q(start__lt=today) & (Q(end__isnull=True) | Q(end__gte=today)))
        )
    def upcoming(self):
        today = timezone.now().date()
        return self.active().filter(start__gte=today )

    def ongoing(self):
        today = timezone.now().date()
        return self.active().filter(
            start__lt=today
        ).filter(
            Q(end__isnull=True) | Q(end__gte=today)
        )
    
class Session(models.Model):
    activity=models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="sessions")
    session_format = models.CharField(max_length=1 ,
                              choices=[("o","Online"),("i","InPerson" ),("b","Hybrid")])
    location = models.ForeignKey( Location, null=True, blank=True, on_delete=models.SET_NULL, related_name="sessions")
    session_url = models.URLField(max_length=200, default="", blank=True)
    ongoing = models.BooleanField(default=False)
    start = models.DateField(null=True, blank=True)
    end = models.DateField(null=True, blank=True)
    deleted=models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_by =models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_sessions")
    created_at =models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_sessions")
    updated_at = models.DateTimeField(auto_now=True)

    objects = SessionQuerySet.as_manager()
    all_objects = models.Manager()

    def __str__(self):
        return f"{self.activity.title} – {self.start}"
  
    @property
    def region_image(self):
        # 1️⃣ If event has orgloc, use that region
        if self.location and self.location.region_name:
            region = self.location.region_name
        # 2️⃣ Otherwise fall back to org
        elif self.activity.org and self.activity.org.region_name:
            region = self.activity.org.region_name
        else:
            region = None

        return REGION_IMAGE_MAP.get(
            region,
            'orgs/images/default.jpg'
        )
class ActivityUpload(models.Model):
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="uploads", blank=True, null=True)
    file = models.FileField(upload_to="uploads/")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default="pending")  # pending, processed, failed
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.file.name} ({self.uploaded_at})"
    
class StagingActivity(models.Model):
    upload = models.ForeignKey(ActivityUpload, on_delete=models.CASCADE)
    row_number = models.IntegerField()
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    location_name = models.CharField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    activity_type = models.CharField(max_length=1,
                                  choices=[("v","Volunteer Opportunity"),("t","Training" )])
    time_commitment = models.ForeignKey( Commitment, on_delete=models.SET_NULL, null=True, blank=True)
    date_description = models.CharField(max_length=100, default='', blank=True, null=True)
    expire_date = models.DateField(default=one_year_from_now())
    activity_url = models.URLField(max_length=200, default="", blank=True)
    no_cost = models.BooleanField(default=False)
    contact_email = models.EmailField(default="", blank=True)
    status = models.CharField(max_length=50, default="pending")  # pending, valid, warning, error

    def __str__(self):
        return f"Row {self.row_number} - {self.title or 'No Title'}"
