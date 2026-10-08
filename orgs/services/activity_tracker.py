
from orgs.models import ActivityLog


def track_activity(request, action, org=None, location=None, activity=None):
    
    user = request.user if request.user.is_authenticated else None
    
    ActivityLog.objects.create(
        user=user,
        action=action,
        org=org,
        location=location,
        activity=activity,

    )

