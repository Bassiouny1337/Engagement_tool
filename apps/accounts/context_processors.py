"""Expose role capabilities to all templates as `caps.<capability>`."""


class _Caps:
    def __init__(self, user):
        self.user = user

    def __getattr__(self, name):
        user = self.user
        return bool(
            getattr(user, "is_authenticated", False) and user.has_capability(name)
        )

    # Allow dict-style access too: caps.manage_engagements works via __getattr__,
    # but templates may also do {{ caps.manage_engagements }}.


def capabilities(request):
    user = getattr(request, "user", None)
    if user is None:
        return {}
    return {"caps": _Caps(user)}
