from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.shortcuts import redirect

from . import views
urlpatterns = [
    path("",  views.landing, name="landing"),

    
    path("activities/", views.activities, name="activities"),
    path("orgs/", views.orgs, name="orgs"),
    path("org/enroll/", views.org_enroll, name="org_enroll"),
    path("org/enroll/thanks/", views.org_enroll_thanks, name="org_enroll_thanks"),
    path("staff/org-enrollments/", views.org_enrollment_list, name="org_enrollment_list"),
    path("staff/org-enrollments/<int:enrollment_id>/approve/", views.org_approve, name="org_approve"),
    path("staff/org-enrollments/<int:enrollment_id>/deny/", views.org_deny, name="org_deny"),  
    path("locations/manage/", views.location_manage, name="location_manage"),
    path("locations/manage/", views.location_manage, name="location_manage"),
    path("locations/<int:location_id>/action/", views.location_action, name="location_action"),
    path("org-invite/<uuid:token>/", views.accept_org_invite, name="accept_org_invite",),
    path("org_mgmt/", views.org_mgmt, name="org_mgmt"),
        path("org/<int:org_id>/managers/add/", views.org_manager_add, name="org_manager_add"),
        path("org-managers/<int:pk>/delete/", views.org_manager_delete, name="org_manager_delete"),
        path("orgs/manager-search/", views.org_manager_search, name="manager_search"),
       
        path("org_detail/<int:org_id>/edit/", views.org_edit, name="org_edit"),
        path("org_detail/new/", views.org_create, name="org_create"),
        path("activity/new/", views.activity_create, name="activity_create"),
        
        path("activity/<int:activity_id>/edit", views.activity_edit, name="activity_edit"),
        path("activity/<int:activity_id>/delete/", views.activity_delete, name="activity_delete"),
        path("locations/search/", views.location_search, name="location_search"),
        path("locs/new/", views.loc_detail, name="loc_create"),
        path("locs/<int:loc_id>/edit/", views.loc_detail, name="loc_edit"),
        path("locs/<int:loc_id>/", views.loc_detail, name="loc_view"),
        path("locations/loc_modal/", views.quick_location_create, name="quick_location_create"),
    path("map/", views.map_view, name="map"),
    #path("about/", TemplateView.as_view(template_name="orgs/about.html"), name="about"),
    path("locations/", views.locations, name="locations"),
    path("follow_org/<int:org_id>", views.follow_org, name="follow_org"),
    path("org/<int:org_id>/default-location/<int:loc_id>/",views.org_set_default_location,name="org_set_default_location"),
    path("profile/", views.profile_view, name="profile"),
    path("staff/user/", views.staff_user_manage, name="staff_user_manage"),

    
    path("login", lambda request: redirect("account_login"), name="login"),
    path("logout", lambda request: redirect("account_logout"), name="logout"),
    path("register", lambda request: redirect("account_signup"), name="register"),
    path("password_reset/", lambda request: redirect("account_reset_password"), name="password_reset"),

    path("uploads/", views.upload_dashboard, name="upload_dashboard"),
    path("upload/<int:org_id>/", views.upload_csv, name="upload_csv"),
    path("upload/<int:upload_id>/map/", views.upload_map, name="upload_map"),
    path("upload/<int:upload_id>/stage/", views.upload_stage, name="upload_stage"),
    path("upload/<int:upload_id>/review_raw/", views.upload_review_raw, name="upload_review_raw"),
    path("upload/<int:upload_id>/build_pending/", views.upload_build_pending, name="upload_build_pending"),
    path("upload/<int:upload_id>/review_locations/", views.upload_review_locations, name="upload_review_locations"),
    path("upload/<int:upload_id>/review_activities/", views.upload_review_activities, name="upload_review_activities"),
    path("upload/<int:upload_id>/publish/", views.upload_publish, name="upload_publish"),
    path("upload/<int:upload_id>/success/", views.upload_success, name="upload_success"),
    path("upload/<int:upload_id>/cancel/", views.upload_cancel_confirm, name="upload_cancel_confirm"),
    path("upload/<int:upload_id>/rollback-confirm/",views.upload_rollback_confirm,name="upload_rollback_confirm",),

    path("upload/<int:upload_id>/rollback/", views.upload_rollback, name="upload_rollback"),
    path("uploads/<int:upload_id>/results/",views.upload_results,name="upload_results"),
    path("lookup-zip/", views.lookup_zip, name="lookup_zip"),
    path("staff/update-latlng/", views.run_update_latlng, name="run_update_latlng"),
    path("staff/cleanup-imports/", views.run_cleanup_old_imports, name="run_cleanup_old_imports"),
    path("test_email",views.test_email, name="test_email"),
    path("test_html", views.test_html, name="test_html"),
    path("admin/run-backfill/", views.run_backfill),
    path("debug/sessions/", views.debug_sessions, name="debug_sessions"),
    path("terms/", views.render_markdown, {"filename": "terms"}, name="terms"),
    path("privacy/", views.render_markdown, {"filename": "privacy"}, name="privacy"),
    path("about/",views.render_markdown, {"filename": "about"}, name="about"),
    path("feedback/", views.feedback_view, name="feedback"),
    path("logos/", TemplateView.as_view(template_name="orgs/logos.html"), name="logos"),
    path("upload_faq/", views.render_markdown, {"filename":"upload_faq"},name="upload_faq"),
    path("tutorials/", views.tutorials, name="tutorials")
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)