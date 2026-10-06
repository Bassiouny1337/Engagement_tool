"""Progress aggregation for an engagement's test cases."""
from collections import defaultdict

from apps.domains.constants import DOMAINS

from .models import TestCase


def _pct(done, total):
    return round(100 * done / total) if total else 0


def engagement_progress(engagement):
    """Return overall and per-domain progress for an engagement.

    {
      "overall": {"total", "done", "pct", "counts": {status: n}},
      "domains": [{"key", "label", "total", "done", "pct", "counts"}...],
    }
    """
    rows = engagement.test_cases.all()
    per_domain_total = defaultdict(int)
    per_domain_done = defaultdict(int)
    per_domain_counts = defaultdict(lambda: defaultdict(int))
    overall_counts = defaultdict(int)
    total = done = 0

    for tc in rows:
        total += 1
        per_domain_total[tc.domain_key] += 1
        overall_counts[tc.status] += 1
        per_domain_counts[tc.domain_key][tc.status] += 1
        if tc.is_done:
            done += 1
            per_domain_done[tc.domain_key] += 1

    domains = []
    for key in per_domain_total:
        d_total = per_domain_total[key]
        d_done = per_domain_done[key]
        domains.append({
            "key": key,
            "label": DOMAINS.get(key, key),
            "total": d_total,
            "done": d_done,
            "pct": _pct(d_done, d_total),
            "counts": dict(per_domain_counts[key]),
        })
    domains.sort(key=lambda d: d["label"])

    return {
        "overall": {
            "total": total,
            "done": done,
            "pct": _pct(done, total),
            "counts": dict(overall_counts),
        },
        "domains": domains,
    }
