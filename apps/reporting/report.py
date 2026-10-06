"""Build an engagement report as Markdown."""
from apps.findings.models import Finding
from apps.findings.query import by_severity, severity_counts
from apps.testcases.progress import engagement_progress


def _lines(block):
    return [ln for ln in (block or "").splitlines() if ln.strip()]


def build_markdown(engagement):
    eng = engagement
    prog = engagement_progress(eng)
    findings = list(by_severity(eng.findings.all()))
    counts = severity_counts(eng.findings.all())

    out = []
    w = out.append

    w(f"# {eng.title}")
    w("")
    w(f"**Engagement:** {eng.code}  ")
    w(f"**Client:** {eng.client.name}  ")
    w(f"**Status:** {eng.get_status_display()}  ")
    w(f"**Period:** {eng.start_date or '—'} to {eng.end_date or '—'}")
    w("")
    if eng.summary:
        w("## Summary")
        w(eng.summary)
        w("")

    # Findings overview
    w("## Findings overview")
    w("")
    w("| Severity | Count |")
    w("| --- | --- |")
    for sev, label in Finding.Severity.choices:
        w(f"| {label} | {counts.get(sev, 0)} |")
    w(f"| **Total** | **{len(findings)}** |")
    w("")

    # Scope
    scope = eng.scope_items.all()
    if scope:
        w("## Scope")
        w("")
        for s in scope:
            flag = "" if s.in_scope else " (OUT OF SCOPE)"
            dom = f" [{s.get_domain_key_display()}]" if s.domain_key else ""
            w(f"- `{s.value}` — {s.get_kind_display()}{dom}{flag}")
        w("")

    # Test-case coverage
    w("## Test coverage")
    w("")
    w(f"Overall: **{prog['overall']['done']}/{prog['overall']['total']}** "
      f"test cases completed ({prog['overall']['pct']}%).")
    w("")
    if prog["domains"]:
        w("| Domain | Done | Total | % |")
        w("| --- | --- | --- | --- |")
        for d in prog["domains"]:
            w(f"| {d['label']} | {d['done']} | {d['total']} | {d['pct']}% |")
        w("")

    # Detailed findings
    w("## Detailed findings")
    w("")
    if not findings:
        w("_No findings recorded._")
        w("")
    for i, f in enumerate(findings, 1):
        reviewed = " ✓ reviewed" if f.is_reviewed else ""
        w(f"### {i}. {f.title}")
        w("")
        cvss = f" · CVSS {f.cvss_score}" if f.cvss_score is not None else ""
        w(f"**Severity:** {f.get_severity_display()}{cvss} · "
          f"**Status:** {f.get_status_display()}{reviewed}")
        if f.cvss_vector:
            w(f"**CVSS vector:** `{f.cvss_vector}`")
        w("")
        if f.affected.strip():
            w("**Affected:**")
            for ln in _lines(f.affected):
                w(f"- `{ln}`")
            w("")
        if f.description.strip():
            w("**Description:**")
            w(f.description.strip())
            w("")
        if f.impact.strip():
            w("**Impact:**")
            w(f.impact.strip())
            w("")
        if f.remediation.strip():
            w("**Remediation:**")
            w(f.remediation.strip())
            w("")
        if f.references.strip():
            w("**References:**")
            for ln in _lines(f.references):
                w(f"- {ln}")
            w("")

    return "\n".join(out)
