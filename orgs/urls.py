from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views
urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
  
    
    path("org_detail/<int:org_id>/", views.org_detail, name="org_view"),
    path("org_detail/<int:org_id>/edit/", views.org_detail, name="org_edit"),
    path("org_detail/new/", views.org_detail, name="org_create"),
    
    path("follow_org/<int:org_id>", views.follow_org, name="follow_org"),
    path("events/new/", views.event_form_view, name="event_create"),
    path("events/<int:event_id>/edit/", views.event_form_view, name="event_edit"),
    path("events/<int:event_id>/", views.event_form_view, name="event_view"),
    path("event_list/", views.event_list, name="event_list"),
    path("ajax/load-orgloc/", views.load_orgloc, name="ajax_load_orgloc"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)