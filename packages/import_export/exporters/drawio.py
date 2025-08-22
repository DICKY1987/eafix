from __future__ import annotations

import html
from apf_core.models import ProcessFlow

# Minimal Draw.io (mxGraph) generator with vertical layout.
# Each step is a rounded rectangle; edges follow `next` relationships.

def _header():
    return ('<mxfile host="app.diagrams.net">'
            '<diagram name="Process">'
            '<mxGraphModel><root>'
            '<mxCell id="0"/><mxCell id="1" parent="0"/>')

def _footer():
    return '</root></mxGraphModel></diagram></mxfile>'

def _vertex_xml(id_num: int, label: str, x: int, y: int, w: int=220, h: int=60) -> str:
    style = "rounded=1;whiteSpace=wrap;html=1;"
    lbl = html.escape(label, quote=True)
    return (f'<mxCell id="{id_num}" value="{lbl}" style="{style}" vertex="1" parent="1">'
            f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')

def _edge_xml(id_num: int, src: int, dst: int) -> str:
    style = "endArrow=block;html=1;rounded=0;"
    return (f'<mxCell id="{id_num}" style="{style}" edge="1" parent="1" source="{src}" target="{dst}">'
            f'<mxGeometry relative="1" as="geometry"/></mxCell>')

def export_drawio(flow: ProcessFlow) -> str:
    # Simple vertical layout with fixed spacing; branches fan out horizontally for the first level only.
    # Map step ids to sequential numeric node ids for mxGraph.
    node_ids = {s.id: i+2 for i, s in enumerate(flow.steps)}  # start at 2 (0,1 reserved)
    # Layout: stack vertically, x depends on branch depth (naive using order of appearance)
    x, y = 40, 40
    x_step, y_step = 260, 100

    xml_parts = [_header()]
    # Create vertices
    positions = {}
    for idx, s in enumerate(flow.steps):
        # position: rows by idx; basic deterministic layout
        vx = x + (idx % 3) * x_step  # stagger every 3 to reduce overlap
        vy = y + idx * y_step
        positions[s.id] = (vx, vy)
        label = f"{s.id}\\n{s.actor}:{s.action}\\n{s.text}"
        xml_parts.append(_vertex_xml(node_ids[s.id], label, vx, vy))

    # Create edges
    eid = max(node_ids.values()) + 1
    for s in flow.steps:
        for n in s.next or []:
            if n in node_ids:
                xml_parts.append(_edge_xml(eid, node_ids[s.id], node_ids[n]))
                eid += 1

    xml_parts.append(_footer())
    return "".join(xml_parts)
