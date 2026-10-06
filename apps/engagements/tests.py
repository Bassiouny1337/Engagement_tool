from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.clients.models import ClientOrg
from apps.testcases.models import TestCase as TC
from apps.testcases.progress import engagement_progress

from .access import can_access_engagement, can_edit_engagement_content
from .models import Engagement, EngagementDomain, TeamAssignment


class EngagementFixtureMixin:
    def setUp(self):
        self.client_org = ClientOrg.objects.create(name="Acme")
        self.manager = User.objects.create_user("mgr", password="pw-123456789", role=Role.MANAGER)
        self.pentester = User.objects.create_user("pt", password="pw-123456789", role=Role.PENTESTER)
        self.other_pt = User.objects.create_user("pt2", password="pw-123456789", role=Role.PENTESTER)
        self.auditor = User.objects.create_user("aud", password="pw-123456789", role=Role.AUDITOR)
        self.eng = Engagement.objects.create(
            client=self.client_org, title="Acme Web Test", code="ACME-2026-01",
            created_by=self.manager,
        )
        TeamAssignment.objects.create(user=self.pentester, engagement=self.eng)


class SeedingTests(EngagementFixtureMixin, TestCase):
    def test_adding_domain_seeds_checklist(self):
        self.assertEqual(self.eng.test_cases.count(), 0)
        EngagementDomain.objects.create(engagement=self.eng, domain_key="web")
        self.assertGreater(self.eng.test_cases.filter(domain_key="web").count(), 0)

    def test_seeding_is_idempotent(self):
        EngagementDomain.objects.create(engagement=self.eng, domain_key="api")
        first = self.eng.test_cases.count()
        # Re-run the seed directly; should add nothing.
        from apps.testcases.models import seed_engagement_domain
        added = seed_engagement_domain(self.eng, "api")
        self.assertEqual(added, 0)
        self.assertEqual(self.eng.test_cases.count(), first)


class ProgressTests(EngagementFixtureMixin, TestCase):
    def test_progress_counts_done_statuses(self):
        EngagementDomain.objects.create(engagement=self.eng, domain_key="web")
        cases = list(self.eng.test_cases.all())
        cases[0].status = TC.Status.PASS
        cases[0].save()
        cases[1].status = TC.Status.FAIL
        cases[1].save()
        prog = engagement_progress(self.eng)
        self.assertEqual(prog["overall"]["done"], 2)
        self.assertTrue(0 < prog["overall"]["pct"] < 100)


class AccessTests(EngagementFixtureMixin, TestCase):
    def test_manager_sees_all(self):
        self.assertTrue(can_access_engagement(self.manager, self.eng))

    def test_assigned_pentester_can_edit(self):
        self.assertTrue(can_edit_engagement_content(self.pentester, self.eng))

    def test_unassigned_pentester_blocked(self):
        self.assertFalse(can_access_engagement(self.other_pt, self.eng))
        self.assertFalse(can_edit_engagement_content(self.other_pt, self.eng))

    def test_auditor_read_only(self):
        self.assertTrue(can_access_engagement(self.auditor, self.eng))
        self.assertFalse(can_edit_engagement_content(self.auditor, self.eng))

    def test_detail_403_for_unassigned(self):
        self.client.login(username="pt2", password="pw-123456789")
        resp = self.client.get(reverse("engagements:detail", args=[self.eng.code]))
        self.assertEqual(resp.status_code, 403)


class LifecycleTests(EngagementFixtureMixin, TestCase):
    def test_valid_transition(self):
        self.assertTrue(self.eng.can_transition_to(Engagement.Status.ACTIVE))

    def test_invalid_transition(self):
        self.assertFalse(self.eng.can_transition_to(Engagement.Status.DELIVERED))


class StatusUpdateViewTests(EngagementFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        EngagementDomain.objects.create(engagement=self.eng, domain_key="web")
        self.tc = self.eng.test_cases.first()

    def test_assigned_pentester_updates_status_via_htmx(self):
        self.client.login(username="pt", password="pw-123456789")
        url = reverse("testcases:update_status", args=[self.eng.code, self.tc.pk])
        resp = self.client.post(url, {"status": "pass"}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        self.tc.refresh_from_db()
        self.assertEqual(self.tc.status, "pass")

    def test_unassigned_pentester_cannot_update(self):
        self.client.login(username="pt2", password="pw-123456789")
        url = reverse("testcases:update_status", args=[self.eng.code, self.tc.pk])
        resp = self.client.post(url, {"status": "pass"})
        self.assertEqual(resp.status_code, 403)

    def test_auditor_cannot_update(self):
        self.client.login(username="aud", password="pw-123456789")
        url = reverse("testcases:update_status", args=[self.eng.code, self.tc.pk])
        resp = self.client.post(url, {"status": "pass"})
        self.assertEqual(resp.status_code, 403)
