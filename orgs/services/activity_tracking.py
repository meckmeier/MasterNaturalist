# orgs/services/activity_tracking.py

from orgs.models import ActivityLog

def track_activity(request, action, org=None):
    user = request.user if request.user.is_authenticated else None

    ActivityLog.objects.create(
        user=user,
        action=action,
        org=org,
        path=request.path,
        ip_address=get_client_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
    )


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR")