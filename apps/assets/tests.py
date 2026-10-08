from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import Role, User
from apps.clients.models import ClientOrg
from apps.engagements.models import Engagement, TeamAssignment

from .crypto import decrypt, encrypt
from .models import Asset, Credential, Function, Service


class CryptoTests(TestCase):
    def test_roundtrip(self):
        self.assertEqual(decrypt(encrypt("hunter2!")), "hunter2!")

    def test_empty(self):
        self.assertEqual(encrypt(""), "")
        self.assertEqual(decrypt(""), "")

    def test_ciphertext_differs_from_plaintext(self):
        token = encrypt("supersecret")
        self.assertNotIn("supersecret", token)


class AssetModelTests(TestCase):
    def setUp(self):
        self.c = ClientOrg.objects.create(name="Acme")
        self.eng = Engagement.objects.create(client=self.c, title="T", code="A-1")

    def test_slug_unique_per_engagement(self):
        a1 = Asset.objects.create(engagement=self.eng, asset_type="web", name="Store")
        a2 = Asset.objects.create(engagement=self.eng, asset_type="web", name="Store")
        self.assertNotEqual(a1.slug, a2.slug)

    def test_credential_secret_encrypted(self):
        a = Asset.objects.create(engagement=self.eng, asset_type="network", name="DC01")
        cred = Credential(asset=a, label="da", username="admin")
        cred.secret = "P@ssw0rd!"
        cred.save()
        cred.refresh_from_db()
        self.assertEqual(cred.secret, "P@ssw0rd!")
        self.assertNotIn("P@ssw0rd!", cred.secret_encrypted)


class AssetFlowFixture:
    def setUp(self):
        self.c = ClientOrg.objects.create(name="Acme")
        self.pt = User.objects.create_user("pt", password="pw-123456789", role=Role.PENTESTER)
        self.aud = User.objects.create_user("aud", password="pw-123456789", role=Role.AUDITOR)
        self.eng = Engagement.objects.create(client=self.c, title="T", code="A-1")
        TeamAssignment.objects.create(user=self.pt, engagement=self.eng)


class AssetViewTests(AssetFlowFixture, TestCase):
    def test_member_creates_asset_with_type(self):
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.post(reverse("assets:create", args=[self.eng.code]), {
            "asset_type": "wifi", "name": "Corp WiFi",
            "primary_target": "ACME-CORP", "description": "",
        })
        self.assertEqual(resp.status_code, 302)
        a = Asset.objects.get(name="Corp WiFi")
        self.assertEqual(a.asset_type, "wifi")

    def test_edit_saves_type_attributes(self):
        a = Asset.objects.create(engagement=self.eng, asset_type="wifi", name="W")
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.post(reverse("assets:edit", args=[self.eng.code, a.slug]), {
            "asset_type": "wifi", "name": "W", "primary_target": "", "description": "",
            "ssid": "ACME", "bssid": "00:11:22:33:44:55", "encryption": "WPA2", "channel": "36",
        })
        self.assertEqual(resp.status_code, 302)
        a.refresh_from_db()
        self.assertEqual(a.attributes["ssid"], "ACME")
        self.assertEqual(a.attributes["bssid"], "00:11:22:33:44:55")

    def test_add_function_and_credential(self):
        a = Asset.objects.create(engagement=self.eng, asset_type="web", name="App")
        self.client.login(username="pt", password="pw-123456789")
        self.client.post(reverse("assets:add_function", args=[self.eng.code, a.slug]),
                         {"name": "Login", "description": ""})
        self.assertTrue(Function.objects.filter(asset=a, name="Login").exists())
        self.client.post(reverse("assets:add_credential", args=[self.eng.code, a.slug]),
                         {"label": "admin", "username": "root", "kind": "password",
                          "secret": "s3cr3t", "notes": ""})
        cred = Credential.objects.get(asset=a)
        self.assertEqual(cred.secret, "s3cr3t")

    def test_reveal_credential_is_audited(self):
        from apps.audit.models import AuditLog
        a = Asset.objects.create(engagement=self.eng, asset_type="web", name="App")
        cred = Credential(asset=a, label="x", username="u")
        cred.secret = "revealme"
        cred.save()
        self.client.login(username="pt", password="pw-123456789")
        resp = self.client.post(
            reverse("assets:reveal_credential", args=[self.eng.code, a.slug, cred.pk]))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "revealme")
        self.assertTrue(AuditLog.objects.filter(
            metadata__action="credential_reveal").exists())

    def test_auditor_cannot_create_asset(self):
        self.client.login(username="aud", password="pw-123456789")
        resp = self.client.post(reverse("assets:create", args=[self.eng.code]), {
            "asset_type": "web", "name": "X", "primary_target": "", "description": "",
        })
        self.assertEqual(resp.status_code, 403)
