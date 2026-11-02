from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection
from django.utils import timezone

import django
import platform

from datetime import timedelta
from django.contrib.auth import get_user_model

from orgs.models import (
    Organization,
    OrganizationEnrollmentRequest,
    Location,
    Activity,
    Session,
    Profile,
    ActivityUpload,
    Pending_Activity,
    Pending_Location,
    Pending_Session,
    EmailLog,
    ActivityLog,
)
def get_database_summary(state):

   return {
    "title": "Objects Created",
    "icon": "database",
    "rows": [
        ("Organizations", OrganizationEnrollmentRequest.objects.filter(created_org__isnull=False,state=state).count()),
        ("Locations", Location.objects.filter(org__organizationenrollmentrequest__created_org__isnull=False, org__home_state=state).count()),
        ("Activities", Activity.objects.filter( org__organizationenrollmentrequest__created_org__isnull=False, org__home_state=state).count()),
        ("Sessions", Session.objects.filter(activity__org__organizationenrollmentrequest__created_org__isnull=False, activity__org__home_state=state).count()),
    ],
}

    
def get_data_quality_summary(state):

    return {
        "title": "Data Quality",
            "icon": "data_quality",
            "rows": [
                ("organizations_without_activities", Organization.objects.visible_in(state).filter( activities__isnull=True).distinct().count()),
                ("locations_without_sessions",Location.objects.for_state(state).filter(sessions__isnull=True).distinct().count()),
                ("locations_without_orgs", Location.objects.for_state(state).filter(org__isnull=True).distinct().count()),
                ("uploaded_activities", Activity.objects.filter( source_upload__isnull=False).count()),
                ("orgs without managers", Organization.objects.visible_in(state).filter(managed__isnull=True).distinct().count()),
                ("clicked_activities", Activity.objects.filter(interest_count__gt=0).count()),
                ("activity log", ActivityLog.objects.filter(state=state).count()),
            ]

    }

def get_freshness_summary():

    return { "title": "Freshness",
                "icon": "freshness",
                "rows": [
                    ("newest_organization", Organization.objects.order_by( "-created_at" ).first()),
                    ("newest_activity", Activity.objects.order_by( "-created_at" ).first()),
                    ("newest_location", Location.objects.order_by("-created_at").first()),
                    ("latest_upload", ActivityUpload.objects.order_by("-uploaded_at").first()),
                    ("latest_user",Profile.objects.order_by("-terms_accepted_at").first()),

                ]

    }
def get_security_summary():
    
    User = get_user_model() 
    return { "title": "Security",
               "icon": "security",
               "rows": [

                    ("users", Profile.objects.count()),
                    ("staff", User.objects.filter(is_staff=True).count()),
                    ("inactive", User.objects.filter(is_active=False).count()),
            ]
       
    }
def get_email_summary():

    return {"title": "Email",
               "icon": "email",
               "rows": [
                ("sent", EmailLog.objects.filter(status="SENT").count()),
                ("failed", EmailLog.objects.filter(status="FAILED").count()),
                ("blocked_hourly", EmailLog.objects.filter(status="BLOCKED_HOURLY").count()),
                ("blocked_monthly", EmailLog.objects.filter(status="BLOCKED_MONTHLY").count()),
                ("disabled", EmailLog.objects.filter(status="DISABLED").count()),
               ]


    }
def get_performance_summary():

    with connection.cursor() as cursor:

        cursor.execute("SELECT version();")

        db_version = cursor.fetchone()[0]

    return { "title": "Email",
               "icon": "email",
               "rows": [

       ( "database_engine", connection.vendor),
       ("database_version", db_version),
       ("database_name", connection.settings_dict["NAME"]),

               ]

        

    }

def get_development_summary():

    return { "title": "Email",
               "icon": "email",
               "rows": [

       ( "django",

            django.get_version()),

       ( "python",

            platform.python_version()),

        ("debug",

            settings.DEBUG),

        ("timezone",

            settings.TIME_ZONE),

       ( "allowed_hosts",

            settings.ALLOWED_HOSTS),
               ]
    }
def get_pending_enrollments(state):

    return OrganizationEnrollmentRequest.objects.filter(
        status="p",
        state=state
    ).count()

def build_dashboard(state):
    return {
        "sections": [
            get_database_summary(state),
            get_data_quality_summary(state),
            get_freshness_summary(),
            get_security_summary(),
            get_email_summary(),
            get_performance_summary(),
            get_development_summary(),
        ],
          "pending_enrollments": get_pending_enrollments(state),
    }
