"""Render user-authored Markdown to sanitized HTML.

Markdown content is written by authenticated team members, but it is still
user input rendered into other users' browsers, so the output is sanitized
with nh3 (ammonia) against an explicit tag/attribute allowlist to prevent
stored XSS. The raw Markdown is what we persist; this is display-only.
"""
import markdown as _md
import nh3

_ALLOWED_TAGS = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "br", "hr", "blockquote", "pre", "code",
    "ul", "ol", "li", "strong", "em", "del", "a",
    "table", "thead", "tbody", "tr", "th", "td",
    "img", "span", "div",
}
_ALLOWED_ATTRS = {
    "a": {"href", "title"},  # nh3 manages rel via link_rel below
    "img": {"src", "alt", "title"},
    "td": {"align"},
    "th": {"align"},
    "code": {"class"},
    "span": {"class"},
    "div": {"class"},
}


def render_markdown(text):
    if not text:
        return ""
    html = _md.markdown(
        text,
        extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
        output_format="html5",
    )
    # nh3 strips scripts, event handlers, and dangerous URL schemes
    # (javascript:) by default, and rewrites links with rel/noopener.
    return nh3.clean(
        html,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRS,
        link_rel="nofollow noopener noreferrer",
    )
