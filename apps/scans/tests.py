from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.clients.models import ClientOrg
from apps.engagements.models import Engagement, ScopeItem, TeamAssignment

from .models import Scan
from .parser import NmapParseError, parse_nmap_xml

FIXTURE = Path(__file__).parent / "fixtures" / "sample_nmap.xml"


class ParserTests(TestCase):
    def setUp(self):
        self.xml = FIXTURE.read_text()

    def test_parses_hosts_ports_services(self):
        data = parse_nmap_xml(self.xml)
        self.assertEqual(len(data["hosts"]), 2)
        h1 = data["hosts"][0]
        self.assertEqual(h1["ip"], "10.0.0.1")
        self.assertEqual(h1["hostnames"], ["gw.acme.test"])
        self.assertEqual(h1["os"], "Linux 5.x")  # highest accuracy wins
        self.assertEqual(len(h1["open_ports"]), 2)  # 22, 80 (443 closed)
        names = {p["service"]["name"] for p in h1["open_ports"]}
        self.assertEqual(names, {"ssh", "http"})

    def test_rejects_non_nmap_xml(self):
        with self.assertRaises(NmapParseError):
            parse_nmap_xml("<foo><bar/></foo>")

    def test_rejects_malformed(self):
        with self.assertRaises(NmapParseError):
            parse_nmap_xml("<nmaprun><host>")

    def test_rejects_xxe_entity(self):
        payload = (
            '<?xml version="1.0"?>'
            '<!DOCTYPE nmaprun [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>'
            '<nmaprun scanner="nmap"><host><address addr="&xxe;" addrtype="ipv4"/>'
            '<status state="up"/></host></nmaprun>'
        )
        with self.assertRaises(NmapParseError):
            parse_nmap_xml(payload)


class ScanViewFixture:
    def setUp(self):
        self.c = ClientOrg.objects.create(name="Acme")
        self.pt = User.objects.create_user("pt", password="pw-123456789", role=Role.PENTESTER)
        self.aud = User.objects.create_user("aud", password="pw-123456789", role=Role.AUDITOR)
        self.eng = Engagement.objects.create(client=self.c, title="T", code="A-1")
        TeamAssignment.objects.create(user=self.pt, engagement=self.eng)


class UploadTests(ScanViewFixture, TestCase):
    def _upload(self):
        f = SimpleUploadedFile("scan.xml", FIXTURE.read_bytes(), content_type="text/xml")
        return self.client.post(reverse("scans:upload", args=[self.eng.code]), {"file": f})

    def test_pentester_imports_scan(self):
        self.client.login(username="pt", password="pw-123456789")
        resp = self._upload()
        self.assertEqual(resp.status_code, 302)
        scan = Scan.objects.get(engagement=self.eng)
        self.assertEqual(scan.host_count, 2)
        self.assertEqual(scan.open_port_count, 3)
        # Network domain auto-added.
        self.assertIn("network", self.eng.domain_keys)

    def test_auditor_cannot_import(self):
        self.client.login(username="aud", password="pw-123456789")
        f = SimpleUploadedFile("scan.xml", FIXTURE.read_bytes())
        resp = self.client.post(reverse("scans:upload", args=[self.eng.code]), {"file": f})
        self.assertEqual(resp.status_code, 403)

    def test_bad_file_rejected_gracefully(self):
        self.client.login(username="pt", password="pw-123456789")
        f = SimpleUploadedFile("x.xml", b"<notnmap/>")
        resp = self.client.post(reverse("scans:upload", args=[self.eng.code]), {"file": f}, follow=True)
        self.assertEqual(Scan.objects.count(), 0)
        self.assertContains(resp, "Could not import")


class ServiceActionTests(ScanViewFixture, TestCase):
    def setUp(self):
        super().setUp()
        self.scan = Scan.objects.create(
            engagement=self.eng, filename="scan.xml",
            data=parse_nmap_xml(FIXTURE.read_text()), uploaded_by=self.pt,
        )

    def test_pentester_adds_testcase_from_service(self):
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.post(
            reverse("scans:add_testcase", args=[self.eng.code, self.scan.pk]),
            {"ip": "10.0.0.2", "port": "445", "service": "microsoft-ds"})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(self.eng.test_cases.filter(
            domain_key="network", title__contains="10.0.0.2:445").exists())

    def test_pentester_cannot_add_scope_without_manage(self):
        # Pentester lacks manage_engagements.
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.post(
            reverse("scans:add_scope", args=[self.eng.code, self.scan.pk]),
            {"ip": "10.0.0.1"})
        self.assertEqual(resp.status_code, 403)
        self.assertFalse(ScopeItem.objects.filter(value="10.0.0.1").exists())


class GraphTests(ScanViewFixture, TestCase):
    def test_graph_detail_renders(self):
        scan = Scan.objects.create(
            engagement=self.eng, filename="scan.xml",
            data=parse_nmap_xml(FIXTURE.read_text()), uploaded_by=self.pt)
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.get(reverse("scans:detail", args=[self.eng.code, scan.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "10.0.0.1")
        self.assertContains(resp, 'id="graph"')
