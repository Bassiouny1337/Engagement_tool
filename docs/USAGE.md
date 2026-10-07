# Engagement Tool — Functions, Use Cases & Reporting

A guide to what the tool does, who uses each part, and how the data it captures
turns into a report with little extra effort.

## Roles (who logs in)

The tool uses a **role + membership** model: your *role* decides what kinds of
actions you may perform; your *membership* on an engagement decides which
projects you may touch. An unassigned pentester is denied (403); auditors are
read-only everywhere.

| Role | What they can do |
| --- | --- |
| **Admin / Owner** | Everything: users, roles, the catalog, all engagements, audit log |
| **Engagement Manager** | Create/scope engagements, assign team, change lifecycle, sign off, see all |
| **Pentester** | Test assigned engagements: board, notes, findings, scans, notebook |
| **Technical Reviewer / QA** | Read assigned engagements, review & sign off findings |
| **Read-only Auditor** | Read everything + export; never edits |

Supported domains: Web, Network, Wi-Fi, Active Directory, Desktop, ATM/XFS,
API, AI Agents/LLM, ICS/OT.

## Functions, by module

### Engagements
The container for a project. Unique code (e.g. `ACME-2026-01`), a client,
dates, and a lifecycle with guarded transitions:
`Scoping → Active → Review → Delivered → Closed`. You attach **domains**,
define **scope items** (IP/CIDR, host, URL, SSID, AD domain, device — in or out
of scope), and assign a **team** (lead / tester / reviewer).

### Test-case board
The pentester's main workspace. Adding a domain auto-seeds its checklist from
the catalog. Each test case tracks a status
(not started / in progress / pass / fail / N/A / blocked), inline notes, and an
assignee. Progress bars per domain and overall. Pentesters can add **custom
test cases** and **pull scenarios** from the library.

### Catalog (super admin)
The reusable knowledge base: **checklist templates** (per-domain items that seed
engagements) and a **scenario library** — "scenarios faced before" with steps,
payloads, references and tags. Curated in-app, not in code.

### Findings
Vulnerabilities with severity, CVSS (vector + score), status, affected assets,
description, impact, remediation and references. A failed test case escalates to
a finding in one click. Reviewers sign findings off.

### Scans (Nmap)
Upload `nmap -oX` XML (parsed safely — DTDs/external entities/XXE rejected). An
interactive network graph (hosts → open services), filterable tables, and
one-click conversion of a discovered service into a **scope item** or a
**network test case**.

### Notebook
Per-engagement Notion-like wiki: nested Markdown pages with a live preview, for
running notes and methodology. Rendered server-side and sanitized against XSS.

### Audit log
Append-only record of who did what, when — every create/update/import/export/
sign-off.

## End-to-end use cases

1. **Kick off** — Manager creates the engagement, attaches Web + Network, adds
   scope, assigns the team. Checklists seed automatically.
2. **Test** — Pentester works the board, imports an Nmap scan, converts open
   services into test cases, and writes methodology in the notebook.
3. **Record & review** — Failed tests become findings with CVSS and
   remediation; the reviewer signs them off.
4. **Deliver** — Manager moves to Review, exports the report, moves to Delivered.
5. **Capture knowledge** — Admin adds new techniques to the scenario library for
   reuse next time.

## User stories

- As a **manager**, I want to scope an engagement and assign a team, so each
  tester only sees their projects.
- As a **pentester**, I want a seeded checklist per domain, so I don't miss
  standard tests.
- As a **pentester**, I want to pull a past scenario into my engagement, so I
  reuse proven techniques.
- As a **pentester**, I want to turn a failed test into a finding in one click,
  so nothing gets lost.
- As a **pentester**, I want to import Nmap and see the network visually, so I
  prioritize targets fast.
- As a **reviewer**, I want to sign off findings, so quality is gated before
  delivery.
- As a **manager**, I want a one-click report, so I deliver without reformatting
  notes.
- As an **admin**, I want to curate checklists and scenarios in-app, so the
  team's methodology stays current.
- As an **auditor**, I want read-only access plus the audit log, so I can verify
  activity without risk.

## How this helps with reporting

The report is not a separate writing task at the end — it is a **by-product of
the structured data captured during the engagement**. Because every piece of
work is recorded in a typed, queryable form, the tool assembles the deliverable
automatically.

### The report writes itself from captured data
`Report → Preview / Download` generates a Markdown report built from:

- **Header** — engagement code, client, status, period.
- **Findings overview** — a severity table (Critical → Info counts) plus the
  total, straight from the findings' `severity` field.
- **Scope** — the in-scope (and explicitly out-of-scope) targets you defined.
- **Test coverage** — overall and per-domain "done / total / %", computed from
  test-case statuses, so the report *proves what was tested*, not just what was
  found.
- **Detailed findings** — every finding, most-severe first, with CVSS,
  affected assets, description, impact, remediation and references — the exact
  fields you filled in while testing.

### Why that matters
- **No copy-paste, no reformatting.** Marking a test `fail` and filling the
  finding form *is* writing the report. Export is one click.
- **Consistency across a team.** Every pentester's findings use the same fields
  and severity scale, so reports look the same regardless of who tested.
- **Coverage you can defend.** The coverage table shows the client exactly which
  checks ran per domain — evidence of thoroughness, and a quick way to spot gaps
  before delivery (e.g. a domain stuck at 40%).
- **Reuse raises quality.** Pulling scenarios from the library carries proven
  steps/payloads/references into the engagement, which then flow into the
  finding and the report — institutional knowledge compounding over time.
- **Severity-ranked, decision-ready.** Findings sort most-severe first in both
  the UI and the report, so the client reads what matters first.
- **Traceable & auditable.** Findings can link to the test case they came from,
  and exports are recorded in the audit log — useful for QA and for client or
  compliance scrutiny.
- **Review gate baked in.** Reviewer sign-off happens on the same findings that
  the report renders, so the delivered document reflects reviewed work.

### Roadmap items that extend reporting
- PDF / DOCX export (currently Markdown) with a branded template.
- Pulling **notebook** pages (methodology, host write-ups) into the report.
- Embedding **evidence** (screenshots/files) under each finding.
- An **executive summary** section with charts (severity distribution, coverage).
