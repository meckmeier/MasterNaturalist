from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404

from .models import Organization, OrgManager


def org_access_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        org_id = kwargs.get("org_id")

        if org_id is None:
            org_id = request.GET.get("org") or request.POST.get("org")

        org = get_object_or_404(Organization, id=org_id)

        if not (
            request.user.is_staff
            or OrgManager.objects.filter(
                org=org,
                profile=request.user.profile
            ).exists()
        ):
            return HttpResponseForbidden()

        request.org = org

        return view_func(request, *args, **kwargs)

    return wrapper