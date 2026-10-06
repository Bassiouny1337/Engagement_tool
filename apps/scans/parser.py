"""Parse nmap XML (-oX) into a plain dict, safely.

Uses defusedxml to reject DTDs, external entities and entity-expansion bombs,
because the XML is attacker-influenced (it describes hosts the client scanned,
and may be a file an untrusted party produced). Never use stdlib xml here.
"""
from defusedxml.ElementTree import fromstring
from defusedxml.common import DefusedXmlException


class NmapParseError(ValueError):
    """Raised when the uploaded file is not valid/safe nmap XML."""


def _addr(host_el):
    ip = mac = None
    for a in host_el.findall("address"):
        kind = a.get("addrtype")
        if kind in ("ipv4", "ipv6"):
            ip = a.get("addr")
        elif kind == "mac":
            mac = a.get("addr")
    return ip, mac


def _hostnames(host_el):
    names = []
    hn = host_el.find("hostnames")
    if hn is not None:
        for n in hn.findall("hostname"):
            if n.get("name"):
                names.append(n.get("name"))
    return names


def _ports(host_el):
    ports = []
    ports_el = host_el.find("ports")
    if ports_el is None:
        return ports
    for p in ports_el.findall("port"):
        state_el = p.find("state")
        svc_el = p.find("service")
        service = {}
        if svc_el is not None:
            service = {
                "name": svc_el.get("name", ""),
                "product": svc_el.get("product", ""),
                "version": svc_el.get("version", ""),
                "extrainfo": svc_el.get("extrainfo", ""),
            }
        ports.append({
            "port": int(p.get("portid")) if p.get("portid", "").isdigit() else p.get("portid"),
            "protocol": p.get("protocol", ""),
            "state": state_el.get("state", "") if state_el is not None else "",
            "reason": state_el.get("reason", "") if state_el is not None else "",
            "service": service,
        })
    return ports


def _os_guess(host_el):
    os_el = host_el.find("os")
    if os_el is None:
        return ""
    best = None
    best_acc = -1
    for m in os_el.findall("osmatch"):
        acc = int(m.get("accuracy", "0") or 0)
        if acc > best_acc:
            best_acc = acc
            best = m.get("name", "")
    return best or ""


def parse_nmap_xml(content):
    """Parse nmap XML bytes/str into a dict. Raises NmapParseError on bad input."""
    if isinstance(content, bytes):
        try:
            content = content.decode("utf-8", errors="replace")
        except Exception as exc:  # pragma: no cover - defensive
            raise NmapParseError("Could not decode file as text.") from exc

    try:
        root = fromstring(content)
    except DefusedXmlException as exc:
        raise NmapParseError("Refused unsafe XML (DTD/entities not allowed).") from exc
    except Exception as exc:
        raise NmapParseError("File is not valid XML.") from exc

    if root.tag != "nmaprun":
        raise NmapParseError("Not an nmap XML file (missing <nmaprun> root).")

    meta = {
        "scanner": root.get("scanner", ""),
        "args": root.get("args", ""),
        "version": root.get("version", ""),
        "start": root.get("startstr", ""),
    }

    hosts = []
    for host_el in root.findall("host"):
        status_el = host_el.find("status")
        ip, mac = _addr(host_el)
        ports = _ports(host_el)
        hosts.append({
            "ip": ip or "",
            "mac": mac or "",
            "hostnames": _hostnames(host_el),
            "state": status_el.get("state", "") if status_el is not None else "",
            "os": _os_guess(host_el),
            "ports": ports,
            "open_ports": [p for p in ports if p.get("state") == "open"],
        })

    return {"meta": meta, "hosts": hosts}
