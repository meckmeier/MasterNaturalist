
from orgs.models import ActivityLog


def track_activity(request, action, org=None, location=None, activity=None):
    
    user = request.user if request.user.is_authenticated else None
    session_key = request.session.session_key

    if not session_key:
        request.session.create()
        session_key = request.session.session_key

    ActivityLog.objects.create(
        user=user,
        session_key=session_key,
        action=action,
        org=org,
        location=location,
        activity=activity,
        path=request.path,

    )

