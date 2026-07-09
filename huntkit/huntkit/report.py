from .checks.base import SEVERITY_ORDER
from .db import get_connection

SEVERITY_LABEL = {
    "critical": "🔴 Critique",
    "high": "🟠 Haute",
    "medium": "🟡 Moyenne",
    "low": "🔵 Basse",
    "info": "⚪ Info",
}


def generate(domain: str) -> str:
    conn = get_connection()
    try:
        subdomains = conn.execute(
            "SELECT hostname, ip, source FROM subdomains WHERE root_domain = ? ORDER BY hostname",
            (domain,),
        ).fetchall()
        ports = conn.execute(
            """
            SELECT hostname, port, banner FROM open_ports
            WHERE hostname IN (SELECT hostname FROM subdomains WHERE root_domain = ?) OR hostname = ?
            ORDER BY hostname, port
            """,
            (domain, domain),
        ).fetchall()
        findings = conn.execute(
            "SELECT hostname, check_name, severity, title, detail FROM findings WHERE root_domain = ?",
            (domain,),
        ).fetchall()
    finally:
        conn.close()

    findings = sorted(findings, key=lambda f: SEVERITY_ORDER.get(f["severity"], 99))

    lines = [f"# Rapport de reconnaissance : {domain}", ""]

    lines.append(f"## Résumé")
    lines.append("")
    lines.append(f"- Sous-domaines découverts : **{len(subdomains)}**")
    lines.append(f"- Ports ouverts détectés : **{len(ports)}**")
    lines.append(f"- Trouvailles de sécurité : **{len(findings)}**")
    lines.append("")

    if findings:
        lines.append("## Trouvailles")
        lines.append("")
        for f in findings:
            label = SEVERITY_LABEL.get(f["severity"], f["severity"])
            lines.append(f"### {label} — {f['title']}")
            lines.append(f"- Hôte : `{f['hostname']}`")
            lines.append(f"- Check : `{f['check_name']}`")
            if f["detail"]:
                lines.append(f"- Détail : `{f['detail']}`")
            lines.append("")

    if subdomains:
        lines.append("## Sous-domaines")
        lines.append("")
        lines.append("| Hôte | IP | Source |")
        lines.append("|---|---|---|")
        for s in subdomains:
            lines.append(f"| {s['hostname']} | {s['ip'] or '-'} | {s['source']} |")
        lines.append("")

    if ports:
        lines.append("## Ports ouverts")
        lines.append("")
        lines.append("| Hôte | Port | Bannière |")
        lines.append("|---|---|---|")
        for p in ports:
            lines.append(f"| {p['hostname']} | {p['port']} | {p['banner'] or '-'} |")
        lines.append("")

    return "\n".join(lines)
