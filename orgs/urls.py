from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from . import views
urlpatterns = [
    path("", views.index_dense, name="index"),
    path('dense/', views.index_dense, name="index_dense"),
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

    path("eventlist/", views.events, name="events"),
    path("ajax/load-orgloc/", views.load_orgloc, name="ajax_load_orgloc"),
    path("password_reset/", auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete" ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)