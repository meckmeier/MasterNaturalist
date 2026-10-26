# orgs/middleware.py
from django.http import Http404
from django.urls import get_script_prefix, set_script_prefix

from .models import State

# Paths that are never state-prefixed
EXEMPT_PREFIXES = ("admin", "static", "media", "accounts", "__debug__")


class StateMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.state = None

        first, _, rest = request.path_info.lstrip("/").partition("/")
        if first and first not in EXEMPT_PREFIXES:
            state = State.objects.filter(slug=first).first()
            if state:
                if not state.is_active:
                    raise Http404("State not available")
                request.state = state
                request.path_info = "/" + rest
                set_script_prefix(f"{get_script_prefix()}{state.slug}/")

        return self.get_response(request)