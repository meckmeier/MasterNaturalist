
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q
from django.utils import timezone

region_list = [
    ('C','Central')
    ,('EC', 'East Central')
    ,('NE', 'Northeast')
    ,('NW','Northwest')
    ,('SC','South Central')
    ,('SE','Southeast')
    ,('SW', 'Southwest')
    ,('St','Statewide')]

class Commitment(models.Model):
    time= models.CharField(max_length=50)

    def __str__(self):
        return self.time

class EventCategory(models.Model):
    name=models.CharField(max_length=50, unique=True)
    description=models.CharField(max_length=200, blank=True, null=True)

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
        return f'Profile of {self.user.username}'
    
    @property
    def following_orgs(self):
        return Organization.objects.filter(following__profile=self)
    
    def following_count(self):
        return self.following.count()
    
class Organization(models.Model):
    org_name = models.CharField(max_length=255)
    org_url = models.URLField(max_length=200, default="", blank=True)
    in_wisconsin = models.BooleanField(default=True)
    host = models.BooleanField(default=False)
    about = models.TextField(default ="" , blank=True)
    region_name = models.CharField(max_length =100, choices = region_list, default='', blank=True)
    training_url = models.URLField(max_length=200, default="", blank=True)
    volunteer_url = models.URLField(max_length=200, default="", blank=True)
    owner = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='owned_orgs', default="", null=True, blank=True)
    deleted=models.BooleanField(default=False)

    class Meta:
        ordering = ["org_name"]

    def __str__(self):
        return self.org_name
    
    def follower_count(self):
        return self.following.count()
    def upcoming_volunteer_count(self):
        return self.events.upcoming().filter(event_type='v').count()
    def upcoming_training_count(self):
        return self.events.upcoming().filter(event_type='t').count()
    def upcoming_online_count(self):
        return self.events.upcoming().filter(online=True).count()
    
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

    @property
    def region_image(self):
        return self.REGION_IMAGE_MAP.get(
            self.region_name,
            'orgs/images/default.jpg'
        )

class FollowOrg(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='followers')
    followOrg = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='following')

    def __str__(self):
        return f'{self.profile.user.username} follows {self.followOrg.org_name}'
        
class OrgLocation(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="locations")
    loc_name= models.CharField(max_length=255)
    physical_location = models.BooleanField(default=False)
    address = models.CharField(max_length=255, default ='', blank=True)
    city_name = models.CharField(max_length=255, blank=True,null=True )
    county_id = models.ForeignKey(County, blank=True, null=True, on_delete=models.SET_NULL, related_name="county")
    region_name = models.CharField(max_length =100, choices = region_list, null=True, blank=True)
    state = models.CharField(max_length=100, default='WI', blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    org_loc_url = models.URLField(max_length=200, default="", blank=True)
    location_about = models.TextField(default="", blank=True , null=True)
    contact_email = models.EmailField(default="", blank=True)
    deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ['loc_name']  # sort by loc_name by default  

    def __str__(self):
        return f"{self.org.org_name}, {self.loc_name}"
    
class EventQuerySet(models.QuerySet):

    def active(self):
        """Not deleted."""
        return self.filter(deleted=False)

    def upcoming(self):
        """Upcoming OR currently running events."""
        today = timezone.now().date()

        return self.active().filter(
            Q(
                end_date__isnull=True,
                date__gte=today
            ) |
            Q(
                end_date__isnull=False,
                date__lte=today,
                end_date__gte=today
            )
        )

    def past(self):
        """Events that have finished."""
        today = timezone.now().date()

        return self.active().filter(
            Q(end_date__isnull=True, date__lt=today) |
            Q(end_date__isnull=False, end_date__lt=today)
        )

    def online(self):
        return self.active().filter(online=True)

    def all_visible(self):
        """All non-deleted events."""
        return self.active()
    
class Event(models.Model):
    event_name = models.CharField(max_length=100)
    event_description = models.TextField(default="", blank=True)
    event_type = models.CharField(max_length=1,
                                  choices=[("v","Volunteer Opportunity"),("t","Training" ), ("m","Master Naturalist")])
    online = models.BooleanField(default=False)
    inperson = models.BooleanField(default=True)
    instructors = models.CharField(max_length=400, blank=True, default="")
    participant_max = models.IntegerField(default=0, blank=True, null=True)
    event_url = models.URLField(max_length=200, default="", blank=True)
    no_cost = models.BooleanField(default=False)
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="events")
    orgloc = models.ForeignKey(OrgLocation, on_delete=models.CASCADE, related_name="eventlocations",blank=True, null=True)
    date_description = models.CharField(max_length=100, default='', blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    time_commitment = models.ForeignKey(Commitment, on_delete=models.SET_NULL, related_name="commitments", blank=True, null=True)
    categories = models.ManyToManyField(EventCategory, blank=True, related_name="events")
    deleted=models.BooleanField(default=False)

    objects = EventQuerySet.as_manager()

    def __str__(self):
        return f"{self.event_name}"

class VolunteerRole(models.Model):
    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="roles"
    )
    orgloc = models.ForeignKey(OrgLocation, on_delete=models.CASCADE, related_name="rolelocations",blank=True, null=True)

    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    time_commitment = models.ForeignKey(
        Commitment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    categories = models.ManyToManyField(
        EventCategory,
        blank=True,
        related_name="category_roles"
    )

    ongoing = models.BooleanField(default=True)
    expire_date = models.DateField(blank=True, null=True)
    online = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
    
