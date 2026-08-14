# utils.py
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from datetime import datetime, timedelta,date
import calendar
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail

geolocator = Nominatim(user_agent="volunteer_map_app")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

import logging
import os

from django.core.mail import send_mail
from django.core.cache import cache

logger = logging.getLogger(__name__)

def get_postmark_period_start():
    today = date.today()
    billing_day = settings.POSTMARK_BILLING_DAY

    # If today's date is on or after the billing day,
    # the billing period started this month.
    if today.day >= billing_day:
        return date(today.year, today.month, billing_day)

    # Otherwise it started last month.
    if today.month == 1:
        year = today.year - 1
        month = 12
    else:
        year = today.year
        month = today.month - 1

    # Handle months with fewer days (e.g. billing day = 31)
    last_day = calendar.monthrange(year, month)[1]

    return date(year, month, min(billing_day, last_day))

def safe_send_mail(subject, message, from_email, recipient_list, category, fail_silently=False, html_message=None):

    from orgs.models import EmailLog
    log = EmailLog.objects.create(
        category=category,
        recipient=", ".join(recipient_list),
        subject=subject,
        status="PENDING",)


    # Emergency kill switch
    if os.getenv("EMAIL_ENABLED", "True").lower() != "true":
        logger.warning("Email blocked: EMAIL_ENABLED=False")
        log.status = "DISABLED"
        log.save()
        return 0

    # Hourly limit

    count = EmailLog.objects.filter(
            sent_at__gte=timezone.now() - timedelta(hours=1),
            status="SENT",
        ).count()


    if count >= settings.EMAIL_HOURLY_LIMIT:
        logger.error(
            "Email blocked: hourly limit exceeded (%s)",
            settings.EMAIL_HOURLY_LIMIT,
        )
        log.status="BLOCKED_HOURLY"
        log.save()


        return 0
    
    # Monthly limit
    monthly_count = EmailLog.objects.filter(
        sent_at__gte=get_postmark_period_start(),
        status="SENT",
    ).count()

    if monthly_count >= settings.EMAIL_MONTHLY_LIMIT:
        logger.critical("Monthly email limit exceeded. Email disabled.")
        log.status="BLOCKED_MONTHLY"
        log.save()
        return 0

    # Send email

    sent = send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=recipient_list,
        fail_silently=fail_silently,
        html_message=html_message,
    )
    log.status="SENT"
    log.save()


    return sent

def build_activity_cards(sessions, location=None):
    from orgs.models import Location, Organization, Activity, Session, Profile
    """
    Build activity cards from a queryset or list of Session objects.

    Returns a list of dictionaries:

        {
            "activity": Activity,
            "location": Location,
            "sessions": [Session, ...],
        }

    If a location is supplied, sessions are grouped only by activity.
    Otherwise they are grouped by (activity, location).
    """

    cards = {}

    for session in sessions:

        if location is None:
            key = (session.activity_id, session.location_id)
            card_location = session.location
        else:
            key = session.activity_id
            card_location = location

        if key not in cards:
            cards[key] = {
                "activity": session.activity,
                "location": card_location,
                "sessions": [],
            }

        cards[key]["sessions"].append(session)

    # Sort sessions within each card
    for card in cards.values():
        card["sessions"].sort(
            key=lambda s: (
                s.start is None,
                s.start,
            )
        )
        card["has_online"] = any(
            s.session_format in ["o", "b"]
            for s in card["sessions"]
        )
    # Convert to list
    cards = list(cards.values())

    # Sort cards by earliest session
    cards.sort(
        key=lambda c: (
            c["sessions"][0].start is None,
            c["sessions"][0].start,
            c["activity"].title.lower(),
        )
    )

    return cards

def get_lat_lng(city, county=None, state="WI"):
    parts = [city]
    if county:
        parts.append(f"{county} County")
    parts.extend([state, "USA"])
    
    query = ", ".join(parts)
    location = geocode(query)
    
    if location:
        return location.latitude, location.longitude
    
    return None, None


"""
Temporary utility to update latitude/longitude for Locations
Call manually from Django shell:

>>> from yourapp.utils import update_latlng
>>> update_latlng()
"""

def update_latlng():
    # to call from the:  python manage.py shell
    # >>> from orgs.utils import update_latlng
    # >>> update_latlng()

    geolocator = Nominatim(user_agent="my_django_app")
    for loc in Location.objects.filter(latitude__isnull=True, longitude__isnull=True):
        address = f"{loc.loc_name}, {loc.city}, {loc.state}"
        geo = geolocator.geocode(address)
        if geo:
            loc.latitude = geo.latitude
            loc.longitude = geo.longitude
            loc.save()
            print(f"Updated {loc.loc_name}: {loc.latitude}, {loc.longitude}")
        else:
            print(f"Could not geocode {loc.loc_name}")



def resaveLocations():
    # to call from the:  python manage.py shell
    # >>> from orgs.utils import resaveLocations
    # >>> resaveLocations()
    for loc in Location.objects.all():
        loc.save()