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
)
def get_database_summary():

   return {
    "title": "Database Summary",
    "icon": "database",
    "rows": [
        ("Organizations", Organization.objects.count()),
        ("Locations", Location.objects.count()),
        ("Activities", Activity.objects.count()),
        ("Sessions", Session.objects.count()),
    ],
}

    
def get_data_quality_summary():

    return {
        "title": "Data Quality",
            "icon": "data_quality",
            "rows": [
                ("organizations_without_activities", Organization.objects.filter( activities__isnull=True).distinct().count()),
                ("activities_without_sessions", Activity.objects.filter(sessions__isnull=True).distinct().count()),
                ("locations_without_sessions",Location.objects.filter(sessions__isnull=True).distinct().count()),
                ("uploaded_activities", Activity.objects.filter( source_upload__isnull=False ).count()),
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
                    ("active", User.objects.filter(is_active=True).count()),
                    ("staff", User.objects.filter(is_staff=True).count()),
                    ("superusers",User.objects.filter(is_superuser=True).count()),
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
def get_pending_enrollments():

    return OrganizationEnrollmentRequest.objects.filter(
        status="p"
    ).count()

def build_dashboard():
    return {
        "sections": [
            get_database_summary(),
            get_data_quality_summary(),
            get_freshness_summary(),
            get_security_summary(),
            get_email_summary(),
            get_performance_summary(),
            get_development_summary(),
        ],
          "pending_enrollments": get_pending_enrollments(),
    }
