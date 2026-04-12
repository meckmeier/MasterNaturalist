from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

from . import views
urlpatterns = [
    path("",  views.landing, name="landing"),

    path("filter/", views.filter, name="filter"),
        path("results/", views.results, name="results"),
    
    path("orgs/", views.orgs, name="orgs"),
    path("org_mgmt/", views.org_mgmt, name="org_mgmt"),
        path("manager/add/", views.add_manager, name="add_manager"),
        path("manager/add/page/", views.manager_add_page, name="manager_add_page"),
        path("org_detail/<int:org_id>/", views.org_detail, name="org_view"),
        path("org_detail/<int:org_id>/edit/", views.org_detail, name="org_edit"),
        path("org_detail/new/", views.org_detail, name="org_create"),
        path("activity/new/", views.activity_detail, name="activity_create"),
        path("activity/<int:activity_id>/", views.activity_detail, name="activity_view"),
        path("activity/<int:activity_id>/edit", views.activity_detail, name="activity_edit"),
        path("activity/<int:activity_id>/delete/", views.activity_delete, name="activity_delete"),
        path("locs/new/", views.loc_detail, name="loc_create"),
        path("locs/<int:loc_id>/edit/", views.loc_detail, name="loc_edit"),
        path("locs/<int:loc_id>/", views.loc_detail, name="loc_view"),
    path("map/", views.map_view, name="map"),
    path("about/", TemplateView.as_view(template_name="orgs/about.html"), name="about"),
    path("locations/", views.locations, name="locations"),
    path("follow_org/<int:org_id>", views.follow_org, name="follow_org"),
    path( "org/<int:org_id>/default-location/<int:loc_id>/",views.org_set_default_location,name="org_set_default_location"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("profile/", views.profile_view, name="profile"),
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete" ),
   
    path("upload/<int:org_id>/", views.upload_csv, name="upload_csv"),
    path("upload/<int:upload_id>/map/", views.upload_map, name="upload_map"),
    path("upload/<int:upload_id>/stage/", views.upload_stage, name="upload_stage"),
    path("upload/<int:upload_id>/review/", views.upload_review, name="upload_review"),
    path("upload/<int:upload_id>/commit/", views.upload_commit, name="upload_commit"),
    path("upload/success/", views.upload_success, name="upload_success"),
    path("upload/<int:upload_id>/processing/", views.upload_processing, name="upload_processing"),
    path("upload/<int:upload_id>/approval", views.upload_approval, name="upload_approval"),
    path("upload/<int:upload_id>/publish/", views.upload_publish, name="upload_publish"),
    path("upload/<int:upload_id>/reject/", views.upload_reject, name="upload_reject"),
    
    path("lookup-zip/", views.lookup_zip, name="lookup_zip"),
    path("test_email",views.test_email, name="test_email"),
    path("admin/run-backfill/", views.run_backfill),
    path("debug/sessions/", views.debug_sessions, name="debug_sessions"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)