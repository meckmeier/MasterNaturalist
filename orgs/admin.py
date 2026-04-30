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
admin.site.register(ActivityUpload)
admin.site.register(RawLoadData)
admin.site.register(Pending_Activity)
admin.site.register(Pending_Session)
admin.site.register(Pending_Location)
admin.site.register(ZipToCounty)

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["created_at", "name", "email", "page_url"]
    search_fields = ["name", "email", "note", "page_url"]
    ordering = ["-created_at"]