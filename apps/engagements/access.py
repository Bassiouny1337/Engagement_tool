"""Engagement access control: role gives capability, membership gives reach."""


def visible_engagements(user, queryset):
    """Filter a queryset to engagements the user may see."""
    if not user.is_authenticated:
        return queryset.none()
    if user.can_see_all_engagements:  # admin, manager, auditor
        return queryset
    return queryset.filter(team_assignments__user=user).distinct()


def can_access_engagement(user, engagement):
    """Whether the user may view this engagement at all."""
    if not user.is_authenticated:
        return False
    if user.can_see_all_engagements:
        return True
    return engagement.team_assignments.filter(user=user).exists()


def can_edit_engagement_content(user, engagement):
    """Whether the user may edit test cases / findings on this engagement.

    Needs both the role-level capability and reach (membership, unless the
    role sees everything). Auditors never edit.
    """
    if not user.is_authenticated or user.is_read_only:
        return False
    if not user.has_capability("edit_testcases"):
        return False
    return can_access_engagement(user, engagement)


def is_member(user, engagement):
    return (
        user.is_authenticated
        and engagement.team_assignments.filter(user=user).exists()
    )
