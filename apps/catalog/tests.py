from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.clients.models import ClientOrg
from apps.engagements.models import Engagement, EngagementDomain, TeamAssignment
from apps.testcases.models import TestCase as TC

from .models import ChecklistItem, Scenario


class CatalogBootstrapTests(TestCase):
    def test_checklist_catalog_seeded_by_migration(self):
        self.assertGreater(ChecklistItem.objects.count(), 100)
        self.assertTrue(ChecklistItem.objects.filter(domain_key="web").exists())


class SeedFromCatalogTests(TestCase):
    def setUp(self):
        self.c = ClientOrg.objects.create(name="Acme")
        self.eng = Engagement.objects.create(client=self.c, title="T", code="A-1")

    def test_adding_domain_seeds_from_catalog_count(self):
        web_items = ChecklistItem.objects.filter(domain_key="web", is_active=True).count()
        EngagementDomain.objects.create(engagement=self.eng, domain_key="web")
        self.assertEqual(self.eng.test_cases.filter(domain_key="web").count(), web_items)

    def test_inactive_items_not_seeded(self):
        ChecklistItem.objects.filter(domain_key="api").update(is_active=False)
        EngagementDomain.objects.create(engagement=self.eng, domain_key="api")
        self.assertEqual(self.eng.test_cases.filter(domain_key="api").count(), 0)


class CatalogPermissionTests(TestCase):
    def setUp(self):
        User.objects.create_user("admin1", password="pw-123456789", role=Role.ADMIN)
        User.objects.create_user("pt", password="pw-123456789", role=Role.PENTESTER)

    def test_admin_can_open_catalog(self):
        self.client.login(username="admin1", password="pw-123456789")
        self.assertEqual(self.client.get(reverse("catalog:home")).status_code, 200)

    def test_pentester_cannot_open_catalog(self):
        self.client.login(username="pt", password="pw-123456789")
        self.assertEqual(self.client.get(reverse("catalog:home")).status_code, 403)

    def test_admin_can_create_checklist_item(self):
        self.client.login(username="admin1", password="pw-123456789")
        resp = self.client.post(reverse("catalog:checklist_new"), {
            "domain_key": "web", "category": "Custom", "title": "New check",
            "order": 1, "is_active": "on",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(ChecklistItem.objects.filter(title="New check").exists())


class PentesterFlowTests(TestCase):
    def setUp(self):
        self.c = ClientOrg.objects.create(name="Acme")
        self.pt = User.objects.create_user("pt", password="pw-123456789", role=Role.PENTESTER)
        self.eng = Engagement.objects.create(client=self.c, title="T", code="A-1")
        EngagementDomain.objects.create(engagement=self.eng, domain_key="web")
        TeamAssignment.objects.create(user=self.pt, engagement=self.eng)
        self.scn = Scenario.objects.create(
            title="SSRF via webhook", domain_key="web",
            summary="Blind SSRF", steps="1. set webhook\n2. hit metadata",
            payloads="http://169.254.169.254/", tags="ssrf, cloud",
        )
        self.client.login(username="pt", password="pw-123456789")

    def test_add_custom_testcase(self):
        resp = self.client.post(reverse("testcases:add_custom", args=[self.eng.code]), {
            "domain_key": "web", "category": "Custom", "title": "My own check",
        })
        self.assertEqual(resp.status_code, 302)
        tc = TC.objects.get(title="My own check")
        self.assertTrue(tc.is_custom)

    def test_add_custom_rejects_out_of_scope_domain(self):
        resp = self.client.post(reverse("testcases:add_custom", args=[self.eng.code]), {
            "domain_key": "atm", "title": "x",
        })
        self.assertEqual(resp.status_code, 400)

    def test_pull_scenario_creates_testcase_with_notes(self):
        resp = self.client.post(
            reverse("testcases:pull_scenario", args=[self.eng.code, self.scn.pk]))
        self.assertEqual(resp.status_code, 302)
        tc = TC.objects.get(source_scenario=self.scn)
        self.assertIn("169.254.169.254", tc.notes)
        self.assertEqual(tc.engagement, self.eng)

    def test_update_notes(self):
        tc = self.eng.test_cases.first()
        resp = self.client.post(
            reverse("testcases:update_notes", args=[self.eng.code, tc.pk]),
            {"notes": "found something"}, HTTP_HX_REQUEST="true")
        self.assertEqual(resp.status_code, 200)
        tc.refresh_from_db()
        self.assertEqual(tc.notes, "found something")

    def test_library_only_shows_in_scope_domains(self):
        Scenario.objects.create(title="ATM jackpot", domain_key="atm", summary="x")
        resp = self.client.get(reverse("testcases:scenario_library", args=[self.eng.code]))
        self.assertContains(resp, "SSRF via webhook")
        self.assertNotContains(resp, "ATM jackpot")
