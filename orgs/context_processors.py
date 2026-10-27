def state(request):
    return {
        "current_state": getattr(request, "state", None),
    }