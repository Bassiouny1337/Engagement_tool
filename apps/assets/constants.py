"""Per-asset-type field schemas for dynamic form rendering.

Core, child-table data (credentials, services, files) is modeled relationally;
these are the lightweight type-specific attributes stored on Asset.attributes.
"""
from apps.domains.constants import DOMAIN_CHOICES

ASSET_TYPE_CHOICES = DOMAIN_CHOICES  # same taxonomy as engagement domains

# asset_type -> list of (key, label, placeholder)
ASSET_ATTRIBUTES = {
    "web": [
        ("base_url", "Base URL", "https://app.example.com"),
        ("technologies", "Technologies", "nginx, Django, PostgreSQL"),
    ],
    "api": [
        ("base_url", "Base URL", "https://api.example.com/v1"),
        ("auth_type", "Auth type", "OAuth2 / JWT / API key"),
    ],
    "network": [
        ("ip_range", "IP / range", "10.0.0.0/24"),
    ],
    "wifi": [
        ("ssid", "SSID", "ACME-CORP"),
        ("bssid", "BSSID", "00:11:22:33:44:55"),
        ("encryption", "Encryption", "WPA2-Enterprise"),
        ("channel", "Channel", "36"),
    ],
    "ad": [
        ("domain", "Domain", "corp.acme.local"),
        ("dc_host", "Domain controller", "DC01 (10.0.0.10)"),
    ],
    "desktop": [
        ("platform", "Platform", "Windows 11 x64"),
        ("version", "App version", "3.4.1"),
        ("install_path", "Install path", r"C:\Program Files\App"),
    ],
    "atm": [
        ("model", "Model", "NCR SelfServ 34"),
        ("xfs_version", "XFS version", "CEN/XFS 3.40"),
    ],
    "ai_agents": [
        ("endpoint", "Endpoint", "https://chat.example.com/api"),
        ("model", "Model", "gpt-4o / claude / custom"),
    ],
    "ics_ot": [
        ("vendor", "Vendor / device", "Siemens S7-1500"),
        ("protocol", "Protocol", "Modbus / S7 / DNP3"),
        ("purdue_level", "Purdue level", "L1 / L2 / L3"),
    ],
}


def attribute_spec(asset_type):
    return ASSET_ATTRIBUTES.get(asset_type, [])
