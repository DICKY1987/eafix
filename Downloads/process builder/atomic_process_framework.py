#!/usr/bin/env python3
"""
Atomic Process Documentation Framework
Maintains synchronized human-readable, machine-readable, and visual formats
with support for sub-processes and value injection
"""

import json
import yaml
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Union, Any
from datetime import datetime
from pathlib import Path
import hashlib
import uuid

@dataclass
class ValueSpec:
    """Specification for values passed between processes"""
    name: str
    data_type: str  # "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    default_value: Any = None
    validation_rules: List[str] = field(default_factory=list)

@dataclass
class ProcessInput:
    """Input specification for a process or sub-process"""
    inputs: List[ValueSpec] = field(default_factory=list)
    
@dataclass
class ProcessOutput:
    """Output specification for a process or sub-process"""
    outputs: List[ValueSpec] = field(default_factory=list)

@dataclass
class SubProcessCall:
    """Reference to a sub-process within a main process step"""
    subprocess_id: str
    input_mapping: Dict[str, str] = field(default_factory=dict)  # main_var -> subprocess_input
    output_mapping: Dict[str, str] = field(default_factory=dict)  # subprocess_output -> main_var
    description: str = ""

@dataclass
class ProcessStep:
    """Enhanced atomic process step with sub-process support"""
    step_id: str
    actor: str
    description: str
    
    # Flow control
    dependencies: List[str] = field(default_factory=list)
    goto_targets: List[str] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    
    # Sub-process integration
    subprocess_calls: List[SubProcessCall] = field(default_factory=list)
    
    # Performance and validation
    sla_ms: Optional[int] = None
    file_operations: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    error_codes: List[str] = field(default_factory=list)
    
    # Value handling
    input_variables: List[str] = field(default_factory=list)  # Variables consumed
    output_variables: List[str] = field(default_factory=list)  # Variables produced
    
    notes: str = ""
    visual_properties: Dict[str, Any] = field(default_factory=dict)  # For diagram rendering

@dataclass
class ProcessSection:
    """Major process section with enhanced metadata"""
    section_id: str
    title: str
    description: str
    actors: List[str]
    transport: str
    steps: List[ProcessStep] = field(default_factory=list)
    
    # Section-level I/O
    section_inputs: ProcessInput = field(default_factory=ProcessInput)
    section_outputs: ProcessOutput = field(default_factory=ProcessOutput)
    
    visual_properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SubProcess:
    """Reusable sub-process definition"""
    subprocess_id: str
    name: str
    description: str
    version: str
    
    # I/O specification
    inputs: ProcessInput
    outputs: ProcessOutput
    
    # Implementation
    steps: List[ProcessStep] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)  # For categorization
    complexity_score: Optional[int] = None  # 1-10 scale
    reuse_count: int = 0  # Track how often it's used
    
    visual_properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProcessFlow:
    """Complete process flow with sub-process support"""
    title: str
    version: str
    date: str
    id_conventions: str
    legend: str
    
    # Main process structure
    sections: List[ProcessSection] = field(default_factory=list)
    
    # Sub-process library
    subprocesses: List[SubProcess] = field(default_factory=list)
    
    # Global specifications
    global_inputs: ProcessInput = field(default_factory=ProcessInput)
    global_outputs: ProcessOutput = field(default_factory=ProcessOutput)
    
    # Metadata
    file_paths: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

class AtomicProcessFramework:
    """Framework for managing atomic process documentation"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.process_flow = None
        
    def create_trading_system_flow(self) -> ProcessFlow:
        """Create enhanced trading system flow with sub-processes"""
        
        # Define reusable sub-processes first
        subprocesses = self._create_trading_subprocesses()
        
        # Main process sections
        sections = self._create_main_sections()
        
        # Global I/O
        global_inputs = ProcessInput(inputs=[
            ValueSpec("market_session", "string", "Current trading session", True),
            ValueSpec("economic_calendar", "object", "Economic calendar data", True),
            ValueSpec("risk_parameters", "object", "Global risk settings", True)
        ])
        
        global_outputs = ProcessOutput(outputs=[
            ValueSpec("trade_signals", "array", "Generated trading signals", True),
            ValueSpec("system_health", "object", "System status information", True)
        ])
        
        return ProcessFlow(
            title="Atomic Process Flow — Reentry Trading System",
            version="v3.0",
            date="2025-08-21",
            id_conventions="See Matrix Grammar in Canonical Spec (Canvas)",
            legend="Each step is atomic (one action). Conditional flow uses IF/ELSE with explicit GOTO targets.",
            sections=sections,
            subprocesses=subprocesses,
            global_inputs=global_inputs,
            global_outputs=global_outputs,
            file_paths={
                "trading_signals": "bridge\\trading_signals.csv",
                "trade_responses": "bridge\\trade_responses.csv",
                "parameter_log": "logs\\parameter_log.csv"
            }
        )
    
    def _create_trading_subprocesses(self) -> List[SubProcess]:
        """Create reusable sub-processes for the trading system"""
        
        # Risk calculation sub-process
        risk_calc_inputs = ProcessInput(inputs=[
            ValueSpec("base_risk_percent", "number", "Base risk percentage", True),
            ValueSpec("volatility_multiplier", "number", "Market volatility adjustment", True, 1.0),
            ValueSpec("symbol_info", "object", "Symbol contract specifications", True)
        ])
        
        risk_calc_outputs = ProcessOutput(outputs=[
            ValueSpec("effective_risk", "number", "Calculated effective risk", True),
            ValueSpec("lot_size", "number", "Position size in lots", True),
            ValueSpec("risk_warnings", "array", "Risk validation warnings", False, [])
        ])
        
        risk_calc_steps = [
            ProcessStep(
                step_id="RC.001",
                actor="PY",
                description="Multiply base risk by volatility multiplier",
                input_variables=["base_risk_percent", "volatility_multiplier"],
                output_variables=["adjusted_risk"],
                sla_ms=5
            ),
            ProcessStep(
                step_id="RC.002",
                actor="PY", 
                description="Cap effective risk at 3.50% maximum",
                input_variables=["adjusted_risk"],
                output_variables=["effective_risk"],
                validation_rules=["effective_risk <= 3.50"],
                sla_ms=5
            ),
            ProcessStep(
                step_id="RC.003",
                actor="PY",
                description="Calculate lot size from effective risk and symbol contract size",
                input_variables=["effective_risk", "symbol_info"],
                output_variables=["lot_size"],
                sla_ms=10
            )
        ]
        
        risk_calculation = SubProcess(
            subprocess_id="RISK_CALC",
            name="Risk Calculation",
            description="Calculate effective risk and position sizing",
            version="1.0",
            inputs=risk_calc_inputs,
            outputs=risk_calc_outputs,
            steps=risk_calc_steps,
            tags=["risk", "calculation", "validation"],
            complexity_score=3
        )
        
        # File validation sub-process
        file_validation = SubProcess(
            subprocess_id="FILE_VALIDATE",
            name="File Integrity Validation",
            description="Validate file integrity with hash checking and atomic operations",
            version="1.0",
            inputs=ProcessInput(inputs=[
                ValueSpec("file_path", "string", "Path to file to validate", True),
                ValueSpec("expected_hash", "string", "Expected SHA-256 hash", False)
            ]),
            outputs=ProcessOutput(outputs=[
                ValueSpec("is_valid", "boolean", "File validation result", True),
                ValueSpec("actual_hash", "string", "Computed file hash", True),
                ValueSpec("file_size", "number", "File size in bytes", True)
            ]),
            steps=[
                ProcessStep(
                    step_id="FV.001",
                    actor="PY",
                    description="Compute SHA-256 hash of file",
                    input_variables=["file_path"],
                    output_variables=["actual_hash", "file_size"],
                    sla_ms=300
                ),
                ProcessStep(
                    step_id="FV.002", 
                    actor="PY",
                    description="Compare with expected hash if provided",
                    input_variables=["actual_hash", "expected_hash"],
                    output_variables=["is_valid"],
                    conditions=["If expected_hash provided"],
                    sla_ms=5
                )
            ],
            tags=["file", "validation", "integrity"],
            complexity_score=2
        )
        
        return [risk_calculation, file_validation]
    
    def _create_main_sections(self) -> List[ProcessSection]:
        """Create main process sections with sub-process integration"""
        
        # Bootstrap section with sub-process calls
        bootstrap_steps = [
            ProcessStep(
                step_id="0.001",
                actor="PY",
                description="Load parameters.schema.json into memory",
                subprocess_calls=[
                    SubProcessCall(
                        subprocess_id="FILE_VALIDATE",
                        input_mapping={"parameters_schema_path": "file_path"},
                        output_mapping={"is_valid": "schema_file_valid", "actual_hash": "schema_hash"},
                        description="Validate schema file integrity"
                    )
                ],
                output_variables=["schema_content", "schema_file_valid"],
                sla_ms=500,
                file_operations=["READ: parameters.schema.json"],
                conditions=["If schema_file_valid == false"],
                goto_targets=["11.010"]
            ),
            ProcessStep(
                step_id="0.002",
                actor="PY",
                description="Validate schema self-integrity",
                input_variables=["schema_content"],
                validation_rules=["$id field present", "$schema field present"],
                conditions=["If fail"],
                goto_targets=["11.010"],
                sla_ms=200
            )
        ]
        
        bootstrap_section = ProcessSection(
            section_id="0.000",
            title="System Bootstrap (One-Time on Service Start)",
            description="Initialize system components and validate configuration",
            actors=["PY"],
            transport="Filesystem",
            steps=bootstrap_steps
        )
        
        # Signal generation section with risk calculation sub-process
        signal_steps = [
            ProcessStep(
                step_id="3.006",
                actor="PY",
                description="Compute effective risk and position sizing",
                subprocess_calls=[
                    SubProcessCall(
                        subprocess_id="RISK_CALC",
                        input_mapping={
                            "global_risk_percent": "base_risk_percent",
                            "volatility_factor": "volatility_multiplier",
                            "symbol_contract_info": "symbol_info"
                        },
                        output_mapping={
                            "effective_risk": "calculated_risk",
                            "lot_size": "position_size"
                        },
                        description="Calculate risk-adjusted position size"
                    )
                ],
                input_variables=["global_risk_percent", "volatility_factor", "symbol_contract_info"],
                output_variables=["calculated_risk", "position_size"],
                sla_ms=50
            )
        ]
        
        signal_section = ProcessSection(
            section_id="3.000",
            title="Matrix Routing & Parameter Resolution",
            description="Route signals and calculate parameters with risk management",
            actors=["PY"],
            transport="Memory",
            steps=signal_steps
        )
        
        return [bootstrap_section, signal_section]
    
    def save_machine_readable(self, flow: ProcessFlow, format_type: str = "yaml") -> str:
        """Enhanced save with sub-process support"""
        data = asdict(flow)
        
        if format_type.lower() == "json":
            return json.dumps(data, indent=2, ensure_ascii=False, default=str)
        elif format_type.lower() == "yaml":
            return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        else:
            raise ValueError("Format must be 'json' or 'yaml'")
    
    def load_machine_readable(self, content: str, format_type: str = "yaml") -> ProcessFlow:
        """Enhanced load with sub-process support"""
        if format_type.lower() == "json":
            data = json.loads(content)
        elif format_type.lower() == "yaml":
            data = yaml.safe_load(content)
        else:
            raise ValueError("Format must be 'json' or 'yaml'")
        
        # Convert back to dataclass structure (with sub-processes)
        sections = self._rebuild_sections(data.get('sections', []))
        subprocesses = self._rebuild_subprocesses(data.get('subprocesses', []))
        
        flow_data = {**data, 'sections': sections, 'subprocesses': subprocesses}
        
        # Handle optional fields
        if 'global_inputs' in flow_data:
            flow_data['global_inputs'] = ProcessInput(**flow_data['global_inputs'])
        if 'global_outputs' in flow_data:
            flow_data['global_outputs'] = ProcessOutput(**flow_data['global_outputs'])
            
        return ProcessFlow(**flow_data)
    
    def _rebuild_sections(self, sections_data: List[Dict]) -> List[ProcessSection]:
        """Rebuild sections from serialized data"""
        sections = []
        for section_data in sections_data:
            steps = []
            for step_data in section_data.get('steps', []):
                # Rebuild subprocess calls
                subprocess_calls = []
                for call_data in step_data.get('subprocess_calls', []):
                    subprocess_calls.append(SubProcessCall(**call_data))
                
                step = ProcessStep(**{**step_data, 'subprocess_calls': subprocess_calls})
                steps.append(step)
            
            section = ProcessSection(**{**section_data, 'steps': steps})
            sections.append(section)
        
        return sections
    
    def _rebuild_subprocesses(self, subprocess_data: List[Dict]) -> List[SubProcess]:
        """Rebuild sub-processes from serialized data"""
        subprocesses = []
        for sp_data in subprocess_data:
            steps = []
            for step_data in sp_data.get('steps', []):
                step = ProcessStep(**step_data)
                steps.append(step)
            
            inputs = ProcessInput(**sp_data.get('inputs', {}))
            outputs = ProcessOutput(**sp_data.get('outputs', {}))
            
            subprocess = SubProcess(**{
                **sp_data, 
                'steps': steps, 
                'inputs': inputs, 
                'outputs': outputs
            })
            subprocesses.append(subprocess)
        
        return subprocesses
    
    def generate_human_readable(self, flow: ProcessFlow) -> str:
        """Generate enhanced human-readable document with sub-process documentation"""
        output = []
        
        # Header
        output.append(f"# {flow.title} ({flow.version})")
        output.append("")
        output.append(f"**Date:** {flow.date}")
        output.append(f"**ID Conventions:** {flow.id_conventions}")
        output.append("")
        output.append(f"**Legend:** {flow.legend}")
        output.append("")
        
        # Global I/O
        if flow.global_inputs.inputs or flow.global_outputs.outputs:
            output.append("## Global Process Interface")
            
            if flow.global_inputs.inputs:
                output.append("### Inputs")
                for inp in flow.global_inputs.inputs:
                    output.append(f"- **{inp.name}** ({inp.data_type}): {inp.description}")
                    if not inp.required:
                        output.append(f"  - Optional (default: {inp.default_value})")
            
            if flow.global_outputs.outputs:
                output.append("### Outputs")
                for out in flow.global_outputs.outputs:
                    output.append(f"- **{out.name}** ({out.data_type}): {out.description}")
            
            output.append("")
        
        # Sub-processes library
        if flow.subprocesses:
            output.append("## Sub-Process Library")
            output.append("*Reusable components that can be called from main process steps*")
            output.append("")
            
            for subprocess in flow.subprocesses:
                output.append(f"### {subprocess.subprocess_id}: {subprocess.name}")
                output.append(f"**Description:** {subprocess.description}")
                output.append(f"**Complexity:** {subprocess.complexity_score}/10")
                output.append(f"**Tags:** {', '.join(subprocess.tags)}")
                
                # Sub-process I/O
                if subprocess.inputs.inputs:
                    output.append("**Inputs:**")
                    for inp in subprocess.inputs.inputs:
                        req_str = "Required" if inp.required else f"Optional (default: {inp.default_value})"
                        output.append(f"- {inp.name} ({inp.data_type}): {inp.description} - {req_str}")
                
                if subprocess.outputs.outputs:
                    output.append("**Outputs:**")
                    for out in subprocess.outputs.outputs:
                        output.append(f"- {out.name} ({out.data_type}): {out.description}")
                
                # Sub-process steps
                output.append("**Steps:**")
                for step in subprocess.steps:
                    step_line = f"  - **{step.step_id}** ({step.actor}): {step.description}"
                    if step.sla_ms:
                        step_line += f" *[SLA: {step.sla_ms}ms]*"
                    output.append(step_line)
                
                output.append("")
        
        # Main process sections
        output.append("## Main Process Flow")
        output.append("")
        
        for section in flow.sections:
            output.append(f"### {section.section_id} — {section.title}")
            output.append(f"**Actors:** {', '.join(section.actors)} | **Transport:** {section.transport}")
            output.append("")
            
            for step in section.steps:
                # Main step description
                step_line = f"- **{step.step_id}** ({step.actor}) — {step.description}"
                
                # Add SLA
                if step.sla_ms:
                    step_line += f" *[SLA: {step.sla_ms}ms]*"
                
                output.append(step_line)
                
                # Sub-process calls
                if step.subprocess_calls:
                    for call in step.subprocess_calls:
                        output.append(f"  - 🔄 **Calls:** `{call.subprocess_id}` - {call.description}")
                        if call.input_mapping:
                            mappings = [f"{k}→{v}" for k, v in call.input_mapping.items()]
                            output.append(f"    - *Input mapping:* {', '.join(mappings)}")
                        if call.output_mapping:
                            mappings = [f"{k}→{v}" for k, v in call.output_mapping.items()]
                            output.append(f"    - *Output mapping:* {', '.join(mappings)}")
                
                # Conditions and flow control
                if step.conditions:
                    for condition in step.conditions:
                        output.append(f"  - 🔀 **{condition}**")
                
                if step.goto_targets:
                    output.append(f"  - ➡️ **GOTO:** {', '.join(step.goto_targets)}")
                
                # Variables
                if step.input_variables:
                    output.append(f"  - 📥 **Consumes:** {', '.join(step.input_variables)}")
                if step.output_variables:
                    output.append(f"  - 📤 **Produces:** {', '.join(step.output_variables)}")
            
            output.append("")
        
        # File paths appendix
        if flow.file_paths:
            output.append("## Appendix: File Paths")
            for name, path in flow.file_paths.items():
                output.append(f"- **{name}:** `{path}`")
            output.append("")
        
        return "\n".join(output)
    
    def generate_drawio_xml(self, flow: ProcessFlow) -> str:
        """Generate draw.io compatible XML diagram"""
        
        # Create root mxGraphModel
        root = ET.Element("mxGraphModel")
        root.set("dx", "1426")
        root.set("dy", "827")
        root.set("grid", "1")
        root.set("gridSize", "10")
        
        # Root diagram element
        diagram = ET.SubElement(root, "root")
        
        # Create default parent cells
        cell0 = ET.SubElement(diagram, "mxCell")
        cell0.set("id", "0")
        
        cell1 = ET.SubElement(diagram, "mxCell") 
        cell1.set("id", "1")
        cell1.set("parent", "0")
        
        # Position tracking
        y_pos = 50
        x_base = 50
        
        # Generate cells for each section
        for section in flow.sections:
            # Section header
            section_id = f"section_{section.section_id.replace('.', '_')}"
            section_cell = ET.SubElement(diagram, "mxCell")
            section_cell.set("id", section_id)
            section_cell.set("value", f"{section.section_id} — {section.title}")
            section_cell.set("style", "rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366;fontStyle=1;fontSize=14;")
            section_cell.set("vertex", "1")
            section_cell.set("parent", "1")
            
            # Section geometry
            section_geom = ET.SubElement(section_cell, "mxGeometry")
            section_geom.set("x", str(x_base))
            section_geom.set("y", str(y_pos))
            section_geom.set("width", "600")
            section_geom.set("height", "40")
            
            y_pos += 60
            
            # Steps in this section
            for i, step in enumerate(section.steps):
                step_id = f"step_{step.step_id.replace('.', '_')}"
                step_cell = ET.SubElement(diagram, "mxCell")
                step_cell.set("id", step_id)
                
                # Create step label with sub-process info
                step_label = f"{step.step_id} ({step.actor})\\n{step.description[:50]}..."
                if step.subprocess_calls:
                    step_label += f"\\n🔄 Calls: {', '.join([call.subprocess_id for call in step.subprocess_calls])}"
                
                step_cell.set("value", step_label)
                step_cell.set("style", "rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656;")
                step_cell.set("vertex", "1")
                step_cell.set("parent", "1")
                
                # Step geometry
                step_geom = ET.SubElement(step_cell, "mxGeometry")
                step_geom.set("x", str(x_base + 20))
                step_geom.set("y", str(y_pos))
                step_geom.set("width", "200")
                step_geom.set("height", "80")
                
                # Draw arrows to next step
                if i < len(section.steps) - 1:
                    next_step_id = f"step_{section.steps[i+1].step_id.replace('.', '_')}"
                    arrow_id = f"arrow_{step_id}_to_{next_step_id}"
                    arrow_cell = ET.SubElement(diagram, "mxCell")
                    arrow_cell.set("id", arrow_id)
                    arrow_cell.set("style", "endArrow=classic;html=1;")
                    arrow_cell.set("edge", "1")
                    arrow_cell.set("parent", "1")
                    arrow_cell.set("source", step_id)
                    arrow_cell.set("target", next_step_id)
                    
                    arrow_geom = ET.SubElement(arrow_cell, "mxGeometry")
                    arrow_geom.set("relative", "1")
                
                # Add sub-process boxes if present
                if step.subprocess_calls:
                    for j, call in enumerate(step.subprocess_calls):
                        sp_id = f"subprocess_{step_id}_{call.subprocess_id}"
                        sp_cell = ET.SubElement(diagram, "mxCell")
                        sp_cell.set("id", sp_id)
                        sp_cell.set("value", f"📦 {call.subprocess_id}\\n{call.description}")
                        sp_cell.set("style", "rounded=1;whiteSpace=wrap;html=1;fillColor=#e1d5e7;strokeColor=#9673a6;dashed=1;")
                        sp_cell.set("vertex", "1")
                        sp_cell.set("parent", "1")
                        
                        sp_geom = ET.SubElement(sp_cell, "mxGeometry")
                        sp_geom.set("x", str(x_base + 250 + j * 150))
                        sp_geom.set("y", str(y_pos))
                        sp_geom.set("width", "140")
                        sp_geom.set("height", "80")
                        
                        # Arrow to sub-process
                        sp_arrow_id = f"arrow_to_sp_{sp_id}"
                        sp_arrow_cell = ET.SubElement(diagram, "mxCell")
                        sp_arrow_cell.set("id", sp_arrow_id)
                        sp_arrow_cell.set("style", "endArrow=classic;html=1;dashed=1;")
                        sp_arrow_cell.set("edge", "1")
                        sp_arrow_cell.set("parent", "1")
                        sp_arrow_cell.set("source", step_id)
                        sp_arrow_cell.set("target", sp_id)
                        
                        sp_arrow_geom = ET.SubElement(sp_arrow_cell, "mxGeometry")
                        sp_arrow_geom.set("relative", "1")
                
                y_pos += 100
            
            y_pos += 30  # Space between sections
        
        # Convert to string
        ET.indent(root, space="  ")
        return ET.tostring(root, encoding='unicode')
    
    def validate_flow(self, flow: ProcessFlow) -> List[str]:
        """Enhanced validation with sub-process checking"""
        errors = []
        all_step_ids = set()
        subprocess_ids = {sp.subprocess_id for sp in flow.subprocesses}
        
        # Collect all step IDs
        for section in flow.sections:
            for step in section.steps:
                if step.step_id in all_step_ids:
                    errors.append(f"Duplicate step ID: {step.step_id}")
                all_step_ids.add(step.step_id)
        
        # Validate GOTO targets exist
        for section in flow.sections:
            for step in section.steps:
                for goto_target in step.goto_targets:
                    if goto_target not in all_step_ids and not goto_target.startswith(('REJECT_', 'END_')):
                        errors.append(f"Step {step.step_id} references non-existent GOTO target: {goto_target}")
                
                # Validate sub-process calls
                for call in step.subprocess_calls:
                    if call.subprocess_id not in subprocess_ids:
                        errors.append(f"Step {step.step_id} calls non-existent sub-process: {call.subprocess_id}")
        
        # Validate sub-process definitions
        for subprocess in flow.subprocesses:
            subprocess_step_ids = {step.step_id for step in subprocess.steps}
            for step in subprocess.steps:
                for goto_target in step.goto_targets:
                    if goto_target not in subprocess_step_ids and not goto_target.startswith(('RETURN', 'ERROR')):
                        errors.append(f"Sub-process {subprocess.subprocess_id} step {step.step_id} references invalid GOTO: {goto_target}")
        
        return errors
    
    def inject_subprocess(self, main_step_id: str, subprocess_call: SubProcessCall):
        """Inject a sub-process call into an existing main process step"""
        if not self.process_flow:
            return False
        
        for section in self.process_flow.sections:
            for step in section.steps:
                if step.step_id == main_step_id:
                    step.subprocess_calls.append(subprocess_call)
                    return True
        return False
    
    def generate_sync_report(self, flow: ProcessFlow) -> Dict[str, Any]:
        """Generate synchronization report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "main_process_stats": {
                "sections": len(flow.sections),
                "total_steps": sum(len(section.steps) for section in flow.sections),
                "actors": list(set(step.actor for section in flow.sections for step in section.steps))
            },
            "subprocess_stats": {
                "total_subprocesses": len(flow.subprocesses),
                "subprocess_calls": sum(len(step.subprocess_calls) for section in flow.sections for step in section.steps),
                "complexity_distribution": {}
            },
            "validation_status": {
                "errors": self.validate_flow(flow),
                "valid": len(self.validate_flow(flow)) == 0
            }
        }
        
        # Complexity distribution
        if flow.subprocesses:
            complexity_counts = {}
            for sp in flow.subprocesses:
                score = sp.complexity_score or 0
                complexity_counts[score] = complexity_counts.get(score, 0) + 1
            report["subprocess_stats"]["complexity_distribution"] = complexity_counts
        
        return report

# Example usage and testing
def main():
    """Demo the enhanced atomic process framework"""
    
    framework = AtomicProcessFramework()
    
    # Create the enhanced process flow
    flow = framework.create_trading_system_flow()
    framework.process_flow = flow
    
    # Save in multiple formats
    yaml_content = framework.save_machine_readable(flow, "yaml")
    with open("enhanced_reentry_process.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_content)
    
    json_content = framework.save_machine_readable(flow, "json")
    with open("enhanced_reentry_process.json", "w", encoding="utf-8") as f:
        f.write(json_content)
    
    # Generate human-readable
    human_doc = framework.generate_human_readable(flow)
    with open("enhanced_reentry_process_human.md", "w", encoding="utf-8") as f:
        f.write(human_doc)
    
    # Generate draw.io XML
    xml_content = framework.generate_drawio_xml(flow)
    with open("enhanced_reentry_process.drawio", "w", encoding="utf-8") as f:
        f.write(xml_content)
    
    # Validation and reporting
    errors = framework.validate_flow(flow)
    if errors:
        print("❌ Validation errors found:")
        for error in errors:
            print(f"   • {error}")
    else:
        print("✅ Process flow is valid!")
    
    # Generate sync report
    report = framework.generate_sync_report(flow)
    with open("sync_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Sync Report:")
    print(f"   • Main process: {report['main_process_stats']['sections']} sections, {report['main_process_stats']['total_steps']} steps")
    print(f"   • Sub-processes: {report['subprocess_stats']['total_subprocesses']} defined, {report['subprocess_stats']['subprocess_calls']} calls")
    print(f"   • Validation: {'✅ Valid' if report['validation_status']['valid'] else '❌ Errors found'}")
    
    # Demo: Inject a new sub-process call
    new_call = SubProcessCall(
        subprocess_id="FILE_VALIDATE",
        input_mapping={"config_file": "file_path"},
        output_mapping={"is_valid": "config_valid"},
        description="Validate configuration file before loading"
    )
    
    if framework.inject_subprocess("0.001", new_call):
        print("\n✅ Successfully injected FILE_VALIDATE sub-process into step 0.001")
    
    print("\n🚀 Enhanced Atomic Process Framework Demo Complete!")
    print("Generated files:")
    print("   • enhanced_reentry_process.yaml (machine-readable)")
    print("   • enhanced_reentry_process.json (machine-readable)")  
    print("   • enhanced_reentry_process_human.md (human-readable)")
    print("   • enhanced_reentry_process.drawio (visual diagram)")
    print("   • sync_report.json (synchronization report)")

if __name__ == "__main__":
    main()