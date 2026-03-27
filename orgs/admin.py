from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(User)
admin.site.register(Organization)
admin.site.register(Location)
admin.site.register(County)
admin.site.register(Commitment)
admin.site.register(Profile)
admin.site.register(FollowOrg)  
admin.site.register(EventCategory)
admin.site.register(Activity)
admin.site.register(Session)
admin.site.register(OrgManager)
