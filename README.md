# Engagement Tool

A Django application to run and manage pentesting engagements across multiple
domains — Web, Network, Wi-Fi, Active Directory, Desktop, ATM/XFS, API,
AI Agents/LLM, and ICS/OT — with per-domain test-case tracking, findings
management, and Nmap import & visualization.

See [`docs/PLAN.md`](docs/PLAN.md) for the full architecture and roadmap.

## Status

**M1 (Foundations) complete.** Project skeleton, custom user model with 5
roles and a capability matrix, append-only audit log, authentication, a
dashboard shell, and the per-domain checklist data are in place.

## Quick start (dev)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt -r requirements-dev.txt
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```

Then open http://127.0.0.1:8000/ and sign in.

## Roles

Admin · Engagement Manager · Pentester · Technical Reviewer/QA · Read-only
Auditor. Roles grant capabilities; engagement membership grants reach. See
`apps/accounts/models.py`.

## Tests

```bash
.venv/bin/python manage.py test
```

## Configuration

Dev uses SQLite with insecure defaults. For production set at least:
`DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS`, and the
`POSTGRES_*` variables (see `config/settings.py`).
