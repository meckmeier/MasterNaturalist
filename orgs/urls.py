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
    path("about/", TemplateView.as_view(template_name="orgs/about.html"), name="about"),
   
    path('orgs/', views.orgs, name="orgs"),
    path('org_mgmt/', views.org_mgmt, name='org_mgmt'),
    path("locations/", views.locations, name="locations"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("profile/", views.profile_view, name="profile"),
    
    path("org_detail/<int:org_id>/", views.org_detail, name="org_view"),
    path("org_detail/<int:org_id>/edit/", views.org_detail, name="org_edit"),
    path("org_detail/new/", views.org_detail, name="org_create"),
    
    path("follow_org/<int:org_id>", views.follow_org, name="follow_org"),
     
    path("activity/new/", views.activity_form_view, name="activity_create"),
    path("activity/<int:activity_id>/", views.activity_form_view, name="activity_view"),
    path("activity/<int:activity_id>/edit", views.activity_form_view, name="activity_edit"),

    path("locs/new/", views.loc_view, name="loc_create"),
    path("locs/<int:loc_id>/edit/", views.loc_view, name="loc_edit"),
    path("locs/<int:loc_id>/", views.loc_view, name="loc_view"),

    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete" ),
    path("map/", views.map_view, name="map"),
    path("test_email",views.test_email, name="test_email")
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)