# Pentesting Engagement Tool — Plan

A Django application to run and manage pentesting engagements across all
domains (Web, Network, Wi-Fi, Active Directory, Desktop, ATM/XFS, API,
AI Agents/LLM, ICS/OT), track per-domain test cases (done / not done),
record findings, and import & visualize Nmap output.

## Roles (RBAC) — 5 roles

Role gives **capabilities**; engagement membership gives **reach**. Both are
checked together for object-level actions.

| Role | Purpose | Key capabilities |
|------|---------|------------------|
| **Admin / Owner** | Platform + company config | everything, incl. users/roles, audit log |
| **Engagement Manager** | Scopes & leads projects | create/assign engagements, manage team, sign-off |
| **Pentester** | Performs testing | edit test cases / findings / evidence on *assigned* engagements |
| **Technical Reviewer / QA** | Quality gate | review, comment, request changes; no scope changes |
| **Read-only Auditor** | Oversight / compliance | read-only everywhere, export, view audit log |

(No external Client portal role in this build.)

## Stack

- Django 5.2 + Django REST Framework
- PostgreSQL in prod (JSONB), SQLite for dev
- Custom `accounts.User` + role capability matrix; **django-guardian** for
  per-engagement object permissions
- Django templates + **HTMX**; **Cytoscape.js** (Nmap graph) + **Chart.js**
  (dashboards)
- **defusedxml** for Nmap XML parsing (untrusted input)

## Apps

```
config/            settings, urls, wsgi/asgi
apps/accounts      custom User, 5 roles, capability matrix, permission helpers
apps/clients       customer organizations (engagement owners)
apps/engagements   engagement + lifecycle, scope, team assignment
apps/domains       9 domain keys + bundled bootstrap checklists (constants.py)
apps/catalog       DB-backed checklist templates + scenario library (super admin)
apps/notebook      per-engagement Markdown wiki (nested pages, Notion-like)
apps/assets        per-engagement typed assets (creds/services/files/functions)
apps/testcases     test cases, status, categories, evidence, comments
apps/findings      vulnerabilities, CVSS, remediation, report-ready
apps/scans         Nmap XML import, parsed hosts/ports/services
apps/reporting     export (MD/PDF/DOCX), sign-off workflow
apps/audit         append-only activity log
apps/dashboard     cross-engagement metrics & charts
```

## Milestones

- **M1 Foundations** ✅ — project, custom User + 5 roles, capability matrix,
  audit log, base templates, auth, dashboard shell, domain checklist data, tests.
- **M2 Engagements** ✅ — ClientOrg, Engagement + lifecycle state machine,
  scope items, domains in scope, team assignment, role+membership access
  control (`engagements/access.py`).
- **M3 Test cases** ✅ — checklists auto-seeded on domain add (signal),
  status tracking (not_started / in_progress / pass / fail / na / blocked),
  per-domain + overall progress bars, HTMX inline status board, filtering.
- **M3.5 Catalog & pentester workflow** ✅ — checklist templates and the
  scenario library moved to the database (`apps.catalog`), bootstrapped from
  the bundled constants via data migration. Super admin (`manage_catalog`
  capability) manages both through an in-app UI (`/catalog/`). Seeding now
  reads active ChecklistItems from the DB. Pentester board gained: add custom
  test case inline, pull a scenario from the library into the engagement
  (copying steps/payloads/references into notes), and inline HTMX notes.
- **M4 Nmap** ✅ — upload nmap `-oX` XML → safe parse with defusedxml (DTD /
  external entities / XXE rejected) → hosts/ports/services stored as JSON;
  Cytoscape network graph (scan → hosts → open services) with click-to-filter;
  host/service table with text filter; one-click "service → scope item" and
  "service → network test case" (auto-adds the network domain). import_scans
  gated; imports audit-logged.
- **M5 Findings & reporting** ✅ — findings with severity + CVSS (vector/score),
  status, affected/description/impact/remediation/references; create a finding
  pre-filled from a failed test case; reviewer sign-off (review capability +
  engagement membership); Markdown report (overview table, scope, coverage,
  detailed findings) with in-app preview and download. export_reports gated.
- **Notebook (Notion-like)** ✅ — per-engagement wiki of nested Markdown pages
  (`apps.notebook`): tree sidebar, breadcrumbs, create/edit/delete with cascade,
  live HTML preview (HTMX). Markdown rendered server-side and sanitized with nh3
  (ammonia) against an explicit allowlist — scripts, event handlers and
  javascript: URLs stripped — to prevent stored XSS. Same role+membership access
  as the rest of the engagement.
- **Assets & per-asset workspace** ✅ — an engagement holds many typed Assets
  (web/network/wifi/ad/desktop/atm/api/ai/ics-ot), each with type-specific
  fields, encrypted Credentials (masked + audit-logged reveal), Services,
  Files/binaries, Functions (components), and a Markdown walkthrough. The test
  board is per-asset (Asset → Function) with an "All" rollup; Nmap hosts import
  as network assets.
- **Personal checklists + promotion** ✅ — each pentester owns personal
  checklist items and scenarios ("My checklist"), can request promotion to the
  shared catalog; Admin/Manager approve in a review queue → a global copy is
  created (personal copy kept) and seeds all future engagements. Seeding uses
  global items only.
- **M6 Polish** — dashboard charts, hardening, full test suite, Docker, docs.

## Core data model (target)

- `User(role, title, phone)`
- `ClientOrg(name, contacts)`
- `Engagement(client, title, type, status, start, end, created_by)`
- `EngagementDomain(engagement, domain_key)`
- `ScopeItem(engagement, domain, kind, value, in_scope)`
- `TeamAssignment(user, engagement, engagement_role)`
- `TestCase(engagement, domain, category, title, status, assignee, notes)`
- `Finding(engagement, title, severity, cvss, description, remediation, status)`
- `Evidence(file, caption, testcase|finding)`
- `Comment(author, body, target)`
- `Scan(engagement, source_file, parsed_json)` → `Host → Port → Service`
- `AuditLog(actor, action, target, summary, metadata, ip)` — append-only
