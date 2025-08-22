from __future__ import annotations
from apf_core.models import ProcessFlow

def export_markdown(flow: ProcessFlow) -> str:
    """
    One line per step from YAML; no hallucinated content.
    Columns: Step ID | Actor | Action | Text | Next
    """
    lines = []
    title = flow.meta.get("title", "Process Flow")
    lines.append(f"# {title}")
    lines.append("")
    lines.append("| Step ID | Actor | Action | Text | Next |")
    lines.append("|---|---|---|---|---|")
    for s in flow.steps:
        nexts = ", ".join(s.next or [])
        text = (s.text or "").replace("|", "\\|")
        lines.append(f"| {s.id} | {s.actor} | {s.action} | {text} | {nexts} |")
    lines.append("")
    return "\n".join(lines)
