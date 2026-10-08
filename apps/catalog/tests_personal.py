from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role, User

from .models import ChecklistItem, ContributionRequest, Scenario


class PersonalCatalogTests(TestCase):
    def setUp(self):
        self.pt = User.objects.create_user("pt", password="pw-123456789", role=Role.PENTESTER)
        self.mgr = User.objects.create_user("mgr", password="pw-123456789", role=Role.MANAGER)
        self.aud = User.objects.create_user("aud", password="pw-123456789", role=Role.AUDITOR)

    def test_pentester_creates_personal_item(self):
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.post(reverse("catalog:my_checklist_new"), {
            "domain_key": "web", "category": "Custom", "title": "My check",
            "order": 0, "is_active": "on",
        })
        self.assertEqual(resp.status_code, 302)
        item = ChecklistItem.objects.get(title="My check")
        self.assertEqual(item.owner, self.pt)
        self.assertFalse(item.is_global)

    def test_auditor_cannot_access_personal(self):
        self.client.login(username="aud", password="pw-123456789")
        self.assertEqual(self.client.get(reverse("catalog:mine")).status_code, 403)

    def test_personal_items_not_seeded_into_engagements(self):
        from apps.clients.models import ClientOrg
        from apps.engagements.models import Engagement, EngagementDomain
        ChecklistItem.objects.create(domain_key="atm", category="c",
                                     title="personal-only", owner=self.pt)
        c = ClientOrg.objects.create(name="Acme")
        eng = Engagement.objects.create(client=c, title="T", code="A-1")
        EngagementDomain.objects.create(engagement=eng, domain_key="atm")
        # Personal item must not appear in the seeded engagement test cases.
        self.assertFalse(eng.test_cases.filter(title="personal-only").exists())

    def test_request_and_approve_promotion_copies_to_global(self):
        item = ChecklistItem.objects.create(domain_key="web", category="Custom",
                                            title="great check", owner=self.pt)
        self.client.login(username="pt", password="pw-123456789")
        self.client.post(reverse("catalog:request_promotion", args=["checklist", item.pk]),
                         {"note": "useful"})
        req = ContributionRequest.objects.get(checklist_item=item)
        self.assertEqual(req.status, "pending")

        # Manager approves.
        self.client.login(username="mgr", password="pw-123456789")
        resp = self.client.post(reverse("catalog:contribution_approve", args=[req.pk]))
        self.assertEqual(resp.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, "approved")
        # A global copy now exists; the personal one still exists.
        self.assertTrue(ChecklistItem.objects.filter(
            title="great check", owner__isnull=True).exists())
        self.assertTrue(ChecklistItem.objects.filter(pk=item.pk, owner=self.pt).exists())

    def test_pentester_cannot_approve(self):
        item = ChecklistItem.objects.create(domain_key="web", category="c",
                                            title="x", owner=self.pt)
        req = ContributionRequest.objects.create(
            kind="checklist", checklist_item=item, requested_by=self.pt)
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.post(reverse("catalog:contribution_approve", args=[req.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_approved_global_item_seeds_into_new_engagement(self):
        from apps.clients.models import ClientOrg
        from apps.engagements.models import Engagement, EngagementDomain
        item = ChecklistItem.objects.create(domain_key="atm", category="c",
                                            title="promoted-check", owner=self.pt)
        req = ContributionRequest.objects.create(
            kind="checklist", checklist_item=item, requested_by=self.pt)
        req.approve(self.mgr)
        c = ClientOrg.objects.create(name="Acme")
        eng = Engagement.objects.create(client=c, title="T", code="A-9")
        EngagementDomain.objects.create(engagement=eng, domain_key="atm")
        self.assertTrue(eng.test_cases.filter(title="promoted-check").exists())
