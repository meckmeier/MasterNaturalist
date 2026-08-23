from django.contrib import admin

from .models import *


# Register your models here.
admin.site.register(User)
admin.site.register(Organization)
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
admin.site.register(ActivityLog)
admin.site.register(UploadLog)
admin.site.register(Region)
admin.site.register(Video)


@admin.register(OrganizationEnrollmentRequest)
class OrgEnrollmentRequestAdmin(admin.ModelAdmin):
    list_display = (
        "org_name",
        "created_org"
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