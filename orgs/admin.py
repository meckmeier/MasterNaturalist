from django.contrib import admin

from .models import *


# Register your models here.
admin.site.register(User)
admin.site.register(Commitment)
admin.site.register(Profile)
admin.site.register(FollowOrg)  
admin.site.register(EventCategory)
admin.site.register(Session)
admin.site.register(OrgManager)
admin.site.register(ActivityUpload)
admin.site.register(RawLoadData)
admin.site.register(Pending_Activity)
admin.site.register(Pending_Session)
admin.site.register(Pending_Location)
admin.site.register(ActivityLog)
admin.site.register(UploadLog)
admin.site.register(Video)

admin.site.register(StateAdmin)

@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "abbr",
        "fips",
        "map_center_lat",
        "map_center_lng",
        "map_zoom",
        "is_active",
    )
    search_fields = (
        "name",
        "abbr",
    )

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "state",
        "code",
    )
    search_fields = (
        "name",
        "state__name",
        "code",
    )
@admin.register(ZipToCounty)
class ZipToCountyAdmin(admin.ModelAdmin):
    list_display = (
        "zip",
        "county",
        "state",
    )
    search_fields = (
        "zip",
        "county__county_name",
        "state__name",
    )
@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = (
        "org_name",
        "home_state",
        "deleted",
        "created_at",
    )
    search_fields = (
        "org_name",
        "home_state__name",
    )
@admin.register(County)
class CountyAdmin(admin.ModelAdmin):
    list_display = (
        "county_name",
        "state",
        "fips",
    )
    search_fields = (
        "county_name",
        "state__name",
        "fips",
    )
@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "interest_count",
        "activity_type",
        "source_upload",
        "created_by",
        "created_at",
    )
    search_fields = (
        "activity_type",
        "interest_count"
    )

@admin.register(OrganizationEnrollmentRequest)
class OrgEnrollmentRequestAdmin(admin.ModelAdmin):
    list_display = (
        "org_name", 
        "created_org",
        "contact_name",
        "contact_email",
        "status",
        "created_at",
    )
    search_fields = (
        "org_name",
        "contact_name",
        "contact_email",
    )
    list_filter = ("status",)
    ordering = ("-created_at",)
@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ["created_at", "name", "email", "page_url"]
    search_fields = ["name", "email", "note", "page_url"]
    ordering = ["-created_at"]
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ["loc_name", "org", "created_at"]
    search_fields = ["name", "org"]
    ordering = ["-created_at"]
@admin.register(OrgInvite)
class OrgInviteAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "org",
        "role",
        "token",
        "accepted",
        "created_at",
    )

    readonly_fields = ("token",)

    search_fields = (
        "email",
        "org__org_name",
    )

    list_filter = (
        "accepted",
        "role",
    )
    ordering = (
        "-created_at",
    )
@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = (
        "sent_at",
        "category",
        "recipient",
        "subject",
        "status",
    )

    list_filter = (
        "status",
        "category",
        "sent_at",
    )

    search_fields = (
        "recipient",
        "subject",
    )

    ordering = ("-sent_at",)