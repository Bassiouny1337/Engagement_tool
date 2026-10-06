from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.domains.constants import CHECKLISTS, DOMAINS, seed_test_cases


class RoleCapabilityTests(TestCase):
    def test_pentester_can_edit_testcases_not_manage_users(self):
        u = User(username="p", role=Role.PENTESTER)
        self.assertTrue(u.has_capability("edit_testcases"))
        self.assertFalse(u.has_capability("manage_users"))

    def test_auditor_is_read_only(self):
        u = User(username="a", role=Role.AUDITOR)
        self.assertTrue(u.is_read_only)
        self.assertFalse(u.has_capability("edit_testcases"))
        self.assertTrue(u.has_capability("view_audit_log"))

    def test_superuser_has_everything(self):
        u = User(username="s", is_superuser=True, role=Role.AUDITOR)
        self.assertTrue(u.has_capability("manage_users"))


class AuthFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester", password="supersecret-123", role=Role.MANAGER
        )

    def test_dashboard_requires_login(self):
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login/", resp.url)

    def test_login_then_dashboard(self):
        self.client.login(username="tester", password="supersecret-123")
        resp = self.client.get(reverse("dashboard:home"))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Engagement Manager")


class ChecklistDataTests(TestCase):
    def test_every_domain_has_a_checklist(self):
        for key in DOMAINS:
            self.assertIn(key, CHECKLISTS, f"{key} missing checklist")
            self.assertTrue(seed_test_cases(key), f"{key} seeds no test cases")
