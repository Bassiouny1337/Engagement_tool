"""Domain definitions and default checklist templates (seed data).

Templates are copied into an engagement when a domain is added, so edits to an
engagement's test cases never mutate these shared templates. Checklists draw on
OWASP WSTG / API Top 10, PTES, NIST, and field practice.
"""

DOMAINS = {
    "web": "Web Application",
    "network": "Network / Infrastructure",
    "wifi": "Wi-Fi",
    "ad": "Active Directory",
    "desktop": "Desktop Application",
    "atm": "ATM / XFS",
    "api": "API",
    "ai_agents": "AI Agents / LLM",
    "ics_ot": "ICS / OT",
}

# domain -> {category: [test case titles]}
CHECKLISTS = {
    "web": {
        "Recon & Mapping": [
            "Enumerate subdomains and virtual hosts",
            "Fingerprint server, framework, and components",
            "Spider application and map all endpoints",
            "Review robots.txt, sitemap, and metafiles",
            "Identify entry points and user roles",
        ],
        "Authentication": [
            "Test for weak / default credentials",
            "Test password policy and account lockout",
            "Test for username enumeration",
            "Test credential recovery / reset flow",
            "Test MFA bypass",
        ],
        "Authorization": [
            "Test for IDOR / broken object-level authorization",
            "Test for privilege escalation (horizontal/vertical)",
            "Test for forced browsing to restricted functions",
        ],
        "Session Management": [
            "Test session token entropy and handling",
            "Test session fixation",
            "Test logout and session timeout",
            "Test CSRF protections",
        ],
        "Input Validation": [
            "Test for SQL injection",
            "Test for XSS (reflected, stored, DOM)",
            "Test for command injection",
            "Test for SSRF",
            "Test for XXE",
            "Test for SSTI",
            "Test for path traversal / LFI",
            "Test for open redirect",
        ],
        "Business Logic": [
            "Test for workflow bypass",
            "Test for race conditions",
            "Test for parameter tampering on pricing/quantity",
        ],
        "Client-Side": [
            "Review CORS configuration",
            "Review security headers and CSP",
            "Test for sensitive data in client storage",
        ],
    },
    "network": {
        "Discovery": [
            "Host discovery across in-scope ranges",
            "Full TCP port scan on live hosts",
            "Top UDP port scan",
            "Service and version enumeration",
            "OS fingerprinting",
        ],
        "Service Assessment": [
            "Enumerate SMB shares and permissions",
            "Enumerate SNMP (community strings)",
            "Enumerate SMTP (VRFY/EXPN, open relay)",
            "Enumerate DNS (zone transfer, records)",
            "Test for default/weak service credentials",
        ],
        "Vulnerabilities": [
            "Identify unpatched / EOL services",
            "Check for anonymous FTP",
            "Check for exposed admin interfaces",
            "Test TLS/SSL configuration",
            "Check for known CVEs on identified versions",
        ],
    },
    "wifi": {
        "Recon": [
            "Enumerate SSIDs and BSSIDs in scope",
            "Identify encryption and auth types",
            "Map clients to access points",
            "Identify hidden SSIDs",
        ],
        "Attacks": [
            "Capture WPA/WPA2 handshake and crack",
            "Test for WPS PIN vulnerability",
            "Test for PMKID attack",
            "Evil twin / rogue AP test",
            "Test for deauthentication resilience",
            "Test guest / corporate network segmentation",
        ],
        "Enterprise": [
            "Test 802.1X / EAP configuration",
            "Test for certificate validation bypass",
        ],
    },
    "ad": {
        "Recon": [
            "Enumerate domain users and groups",
            "Enumerate computers and OUs",
            "Map domain trusts",
            "Collect data with BloodHound",
            "Identify privileged accounts",
        ],
        "Credential Attacks": [
            "AS-REP roasting",
            "Kerberoasting",
            "Password spraying",
            "LLMNR / NBT-NS poisoning",
            "Test for credentials in SYSVOL / GPP",
        ],
        "Privilege Escalation": [
            "Identify ACL-based escalation paths",
            "Test for unconstrained / constrained delegation",
            "Test for DCSync rights",
            "Test for ADCS misconfigurations (ESC1-ESC8)",
        ],
        "Lateral Movement & Persistence": [
            "Test Pass-the-Hash / Pass-the-Ticket",
            "Test for Golden / Silver ticket viability",
            "Review local admin reuse across hosts",
        ],
    },
    "desktop": {
        "Analysis": [
            "Identify tech stack and frameworks",
            "Review installed services and privileges",
            "Analyze binary protections (ASLR, DEP, signing)",
            "Review file and registry permissions (DACLs)",
        ],
        "Attacks": [
            "Test for DLL hijacking",
            "Test for insecure IPC / named pipes",
            "Test for hardcoded secrets in binary",
            "Test local storage / config encryption",
            "Test for privilege escalation via service",
            "Fuzz file / network input parsers",
        ],
    },
    "atm": {
        "Physical & Peripheral": [
            "Inspect physical access to cables and ports",
            "Test USB / peripheral device access",
            "Test cash dispenser isolation",
        ],
        "XFS / Middleware": [
            "Analyze XFS middleware communication",
            "Test for unauthorized dispense commands",
            "Test CEN/XFS access control",
            "Review PIN pad (EPP) communication",
        ],
        "OS & Network": [
            "Test OS lockdown / kiosk escape",
            "Review disk encryption",
            "Test network segmentation from bank network",
            "Check for exposed management interfaces",
        ],
    },
    "api": {
        "Recon": [
            "Discover API endpoints and documentation",
            "Identify API versions and deprecated routes",
            "Map authentication scheme (OAuth, JWT, key)",
        ],
        "OWASP API Top 10": [
            "Test Broken Object Level Authorization (BOLA)",
            "Test Broken Authentication",
            "Test Broken Object Property Level Authorization",
            "Test Unrestricted Resource Consumption (rate limits)",
            "Test Broken Function Level Authorization",
            "Test Unrestricted Access to Sensitive Business Flows",
            "Test Server Side Request Forgery",
            "Test Security Misconfiguration",
            "Test Improper Inventory Management",
            "Test Unsafe Consumption of APIs",
        ],
        "Tokens": [
            "Test JWT signature validation and alg confusion",
            "Test token expiry and revocation",
        ],
    },
    "ai_agents": {
        "Prompt & Input": [
            "Test for direct prompt injection",
            "Test for indirect / stored prompt injection",
            "Test for jailbreaks and guardrail bypass",
            "Test system prompt extraction",
        ],
        "Tooling & Agency": [
            "Enumerate agent tools and permissions",
            "Test for excessive agency / unsafe tool calls",
            "Test for SSRF / data exfil via tools",
            "Test sandbox / code-execution escape",
        ],
        "Data": [
            "Test for training / RAG data leakage",
            "Test for sensitive data in context window",
            "Test output handling (XSS via model output)",
        ],
        "Supply Chain": [
            "Review model and plugin provenance",
            "Test for insecure model deserialization",
        ],
    },
    "ics_ot": {
        "Recon (Passive First)": [
            "Passive network traffic capture and asset inventory",
            "Identify protocols (Modbus, DNP3, S7, EtherNet/IP)",
            "Map Purdue model levels and zones",
            "Identify PLCs, HMIs, historians, engineering stations",
        ],
        "Assessment": [
            "Review network segmentation and conduits",
            "Test for default credentials on HMI/PLC",
            "Identify unpatched / EOL control devices",
            "Review remote access paths (VPN, jump hosts)",
        ],
        "Protocol Security": [
            "Test for unauthenticated protocol commands",
            "Test for replay of control messages",
            "Review Safety Instrumented System (SIS) isolation",
        ],
    },
}

DOMAIN_CHOICES = [(k, v) for k, v in DOMAINS.items()]


def seed_test_cases(domain_key):
    """Return a flat list of (category, title) tuples for a domain."""
    out = []
    for category, titles in CHECKLISTS.get(domain_key, {}).items():
        for title in titles:
            out.append((category, title))
    return out
