"""Build Cytoscape.js graph elements from a parsed scan."""


def build_elements(scan):
    """Return a list of Cytoscape elements: engagement -> hosts -> open services."""
    elements = []
    root_id = f"scan-{scan.pk}"
    elements.append({"data": {"id": root_id, "label": scan.filename, "kind": "scan"}})

    for hi, host in enumerate(scan.hosts):
        host_id = f"h{hi}"
        label = host.get("ip") or (host.get("hostnames") or ["?"])[0]
        open_ports = host.get("open_ports", [])
        elements.append({"data": {
            "id": host_id,
            "label": label,
            "kind": "host",
            "state": host.get("state", ""),
            "os": host.get("os", ""),
            "openports": len(open_ports),
        }})
        elements.append({"data": {"source": root_id, "target": host_id}})

        for pi, port in enumerate(open_ports):
            svc = port.get("service", {}) or {}
            name = svc.get("name") or "unknown"
            port_id = f"{host_id}-p{pi}"
            elements.append({"data": {
                "id": port_id,
                "label": f"{port.get('port')}/{name}",
                "kind": "service",
                "service": name,
            }})
            elements.append({"data": {"source": host_id, "target": port_id}})

    return elements
