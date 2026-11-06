from functools import wraps

from django.http import HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from .models import Organization, OrgManager

from django.contrib.auth.decorators import user_passes_test

superuser_required = user_passes_test(
    lambda u: u.is_active and u.is_superuser,
    login_url="account_login",
)

def state_required(view ):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if request.state is None:
            raise Http404("State required")
        return view(request, *args, **kwargs)
    return wrapper

def org_access_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if getattr(request, "state", None) is None:
            raise Http404("State required")
        org_id = kwargs.get("org_id")

        if org_id is None:
            org_id = request.GET.get("org") or request.POST.get("org")

        org = get_object_or_404(
            Organization.objects.active().visible_in(request.state),
            id=org_id,
        )

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

