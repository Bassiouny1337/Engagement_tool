from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.clients.models import ClientOrg
from apps.engagements.models import Engagement, EngagementDomain, TeamAssignment
from apps.reporting.report import build_markdown

from .models import Finding
from .query import by_severity, severity_counts


class FindingFixture:
    def setUp(self):
        self.c = ClientOrg.objects.create(name="Acme")
        self.mgr = User.objects.create_user("mgr", password="pw-123456789", role=Role.MANAGER)
        self.pt = User.objects.create_user("pt", password="pw-123456789", role=Role.PENTESTER)
        self.rev = User.objects.create_user("rev", password="pw-123456789", role=Role.REVIEWER)
        self.eng = Engagement.objects.create(client=self.c, title="Acme Test", code="A-1",
                                             summary="Scoped web test")
        EngagementDomain.objects.create(engagement=self.eng, domain_key="web")
        TeamAssignment.objects.create(user=self.pt, engagement=self.eng)
        TeamAssignment.objects.create(
            user=self.rev, engagement=self.eng,
            engagement_role=TeamAssignment.EngagementRole.REVIEWER,
        )


class SeverityOrderTests(FindingFixture, TestCase):
    def test_by_severity_orders_most_severe_first(self):
        Finding.objects.create(engagement=self.eng, title="low", severity="low")
        Finding.objects.create(engagement=self.eng, title="crit", severity="critical")
        Finding.objects.create(engagement=self.eng, title="med", severity="medium")
        order = [f.title for f in by_severity(self.eng.findings.all())]
        self.assertEqual(order, ["crit", "med", "low"])

    def test_severity_counts_includes_zeroes(self):
        Finding.objects.create(engagement=self.eng, title="x", severity="high")
        counts = severity_counts(self.eng.findings.all())
        self.assertEqual(counts["high"], 1)
        self.assertEqual(counts["critical"], 0)
        self.assertIn("info", counts)


class FindingPermissionTests(FindingFixture, TestCase):
    def test_pentester_can_create_finding(self):
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.post(reverse("findings:create", args=[self.eng.code]), {
            "title": "SQLi", "severity": "high", "status": "open",
        })
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Finding.objects.filter(title="SQLi").exists())

    def test_reviewer_cannot_create_finding(self):
        self.client.login(username="rev", password="pw-123456789")
        resp = self.client.post(reverse("findings:create", args=[self.eng.code]), {
            "title": "x", "severity": "low", "status": "open",
        })
        self.assertEqual(resp.status_code, 403)

    def test_reviewer_can_mark_reviewed(self):
        f = Finding.objects.create(engagement=self.eng, title="XSS", severity="medium")
        self.client.login(username="rev", password="pw-123456789")
        resp = self.client.post(reverse("findings:review", args=[self.eng.code, f.pk]))
        self.assertEqual(resp.status_code, 302)
        f.refresh_from_db()
        self.assertTrue(f.is_reviewed)
        self.assertEqual(f.reviewed_by, self.rev)

    def test_pentester_cannot_review(self):
        f = Finding.objects.create(engagement=self.eng, title="XSS", severity="medium")
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.post(reverse("findings:review", args=[self.eng.code, f.pk]))
        self.assertEqual(resp.status_code, 403)

    def test_prefill_from_testcase(self):
        tc = self.eng.test_cases.first()
        tc.status = "fail"
        tc.notes = "injectable param id"
        tc.save()
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.get(
            reverse("findings:create", args=[self.eng.code]) + f"?from_testcase={tc.pk}")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, tc.title)


class ReportTests(FindingFixture, TestCase):
    def test_markdown_contains_findings_and_scope(self):
        Finding.objects.create(engagement=self.eng, title="Critical RCE",
                               severity="critical", remediation="Patch now")
        md = build_markdown(self.eng)
        self.assertIn("# Acme Test", md)
        self.assertIn("Critical RCE", md)
        self.assertIn("Patch now", md)
        self.assertIn("Findings overview", md)

    def test_download_sets_attachment_header(self):
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.get(reverse("reporting:download", args=[self.eng.code]))
        self.assertEqual(resp.status_code, 200)
        self.assertIn("attachment", resp["Content-Disposition"])
        self.assertIn("A-1-report.md", resp["Content-Disposition"])
