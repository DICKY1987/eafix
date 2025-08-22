#!/usr/bin/env python3
"""
Synchronized Human-Readable and Machine-Readable Process Flow System
Maintains a machine-editable data structure and auto-generates human docs
"""

import json
import yaml
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Union
from datetime import datetime
import re

@dataclass
class ProcessStep:
    """Single atomic process step"""
    step_id: str  # e.g., "0.001", "1.004"
    actor: str    # PY, EA, FS, BR, TEST
    description: str
    dependencies: List[str] = field(default_factory=list)  # Other step IDs this depends on
    goto_targets: List[str] = field(default_factory=list)  # Steps this can GOTO
    conditions: List[str] = field(default_factory=list)    # IF conditions
    sla_ms: Optional[int] = None  # SLA in milliseconds
    file_operations: List[str] = field(default_factory=list)  # Files read/written
    validation_rules: List[str] = field(default_factory=list)
    error_codes: List[str] = field(default_factory=list)  # e.g., ["E1001", "E1012"]
    notes: str = ""

@dataclass
class ProcessSection:
    """Major process section (e.g., Bootstrap, Calendar Ingestion)"""
    section_id: str  # e.g., "0.000", "1.000"
    title: str
    description: str
    actors: List[str]  # Primary actors involved
    transport: str     # Communication method
    steps: List[ProcessStep] = field(default_factory=list)

@dataclass
class ProcessFlow:
    """Complete process flow document"""
    title: str
    version: str
    date: str
    id_conventions: str
    legend: str
    sections: List[ProcessSection] = field(default_factory=list)
    file_paths: Dict[str, str] = field(default_factory=dict)  # Appendix A
    metadata: Dict[str, Union[str, int, List[str]]] = field(default_factory=dict)

class ProcessFlowManager:
    """Manages synchronization between machine and human readable formats"""
    
    def __init__(self):
        self.process_flow = None
    
    def create_reentry_system_flow(self) -> ProcessFlow:
        """Create the complete Reentry Trading System process flow"""
        
        # Bootstrap section
        bootstrap_steps = [
            ProcessStep(
                step_id="0.001",
                actor="PY",
                description="Load Common\\Files\\reentry\\config\\parameters.schema.json into memory.",
                sla_ms=500,
                file_operations=["READ: parameters.schema.json"]
            ),
            ProcessStep(
                step_id="0.002",
                actor="PY",
                description="Validate schema self-integrity ($id, $schema fields present).",
                conditions=["If fail"],
                goto_targets=["11.010"],
                sla_ms=200,
                validation_rules=["$id field present", "$schema field present"]
            ),
            ProcessStep(
                step_id="0.003",
                actor="PY",
                description="Ensure directories exist: Common\\Files\\reentry\\bridge, ...\\logs, ...\\config, ...\\data. Create if missing.",
                dependencies=["0.002"],
                sla_ms=1000,
                file_operations=["CREATE_DIR: bridge/", "CREATE_DIR: logs/", "CREATE_DIR: config/", "CREATE_DIR: data/"]
            ),
            # Add more bootstrap steps...
        ]
        
        bootstrap_section = ProcessSection(
            section_id="0.000",
            title="System Bootstrap (One-Time on Service Start)",
            description="Initialize system components and validate configuration",
            actors=["PY"],
            transport="Filesystem",
            steps=bootstrap_steps
        )
        
        # Calendar Ingestion section
        calendar_steps = [
            ProcessStep(
                step_id="1.001",
                actor="PY",
                description="At scheduler tick, scan %USERPROFILE%\\Downloads for newest economic_calendar*.csv/.xlsx.",
                sla_ms=1000,
                file_operations=["SCAN: %USERPROFILE%\\Downloads"]
            ),
            ProcessStep(
                step_id="1.002",
                actor="PY",
                description="If none found GOTO 1.010. Else copy-as-new to data\\economic_calendar_raw_YYYYMMDD_HHMMSS.ext (write→fsync→rename atomic).",
                conditions=["If none found"],
                goto_targets=["1.010"],
                dependencies=["1.001"],
                sla_ms=500,
                file_operations=["WRITE_ATOMIC: data/economic_calendar_raw_*.ext"]
            ),
            # Add more calendar steps...
        ]
        
        calendar_section = ProcessSection(
            section_id="1.000",
            title="Economic Calendar Ingestion (Hourly From Sunday 12:00 Local)",
            description="Ingest and process economic calendar data",
            actors=["PY", "FS"],
            transport="CSV-only",
            steps=calendar_steps
        )
        
        # Create main process flow
        process_flow = ProcessFlow(
            title="Atomic Process Flow — Reentry Trading System",
            version="v3.0",
            date="2025-08-21",
            id_conventions="See Matrix Grammar in Canonical Spec (Canvas)",
            legend="Each step is atomic (one action). Conditional flow uses IF/ELSE with explicit GOTO targets.",
            sections=[bootstrap_section, calendar_section],
            file_paths={
                "trading_signals": "bridge\\trading_signals.csv",
                "trade_responses": "bridge\\trade_responses.csv",
                "parameter_log": "logs\\parameter_log.csv"
            }
        )
        
        return process_flow
    
    def save_machine_readable(self, flow: ProcessFlow, format_type: str = "yaml") -> str:
        """Save process flow in machine-readable format"""
        data = asdict(flow)
        
        if format_type.lower() == "json":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format_type.lower() == "yaml":
            return yaml.dump(data, default_flow_style=False, allow_unicode=True, sort_keys=False)
        else:
            raise ValueError("Format must be 'json' or 'yaml'")
    
    def load_machine_readable(self, content: str, format_type: str = "yaml") -> ProcessFlow:
        """Load process flow from machine-readable format"""
        if format_type.lower() == "json":
            data = json.loads(content)
        elif format_type.lower() == "yaml":
            data = yaml.safe_load(content)
        else:
            raise ValueError("Format must be 'json' or 'yaml'")
        
        # Convert back to dataclass structure
        sections = []
        for section_data in data.get('sections', []):
            steps = []
            for step_data in section_data.get('steps', []):
                step = ProcessStep(**step_data)
                steps.append(step)
            
            section = ProcessSection(**{**section_data, 'steps': steps})
            sections.append(section)
        
        flow_data = {**data, 'sections': sections}
        return ProcessFlow(**flow_data)
    
    def generate_human_readable(self, flow: ProcessFlow) -> str:
        """Generate human-readable document from machine data"""
        output = []
        
        # Header
        output.append(f"{flow.title} ({flow.version})")
        output.append("")
        output.append(f"Date: {flow.date}")
        output.append(f"ID Conventions: {flow.id_conventions}")
        output.append("")
        output.append(f"Legend: {flow.legend}")
        output.append("")
        output.append("⸻")
        output.append("")
        
        # Sections
        for section in flow.sections:
            output.append(f"{section.section_id} — {section.title}")
            
            for step in section.steps:
                # Format step line
                step_line = f"\t• {step.step_id} ({step.actor}) — {step.description}"
                
                # Add conditions and GOTO targets
                if step.conditions:
                    for condition in step.conditions:
                        step_line += f" {condition}"
                
                if step.goto_targets:
                    step_line += f" → GOTO {', '.join(step.goto_targets)}."
                
                output.append(step_line)
            
            output.append("⸻")
            output.append("")
        
        # File paths appendix
        if flow.file_paths:
            output.append("Appendix A — File Paths & Headers")
            for name, path in flow.file_paths.items():
                output.append(f"\t• {path}")
            output.append("⸻")
            output.append("")
        
        return "\n".join(output)
    
    def add_step(self, section_id: str, step: ProcessStep):
        """Add a step to a specific section"""
        if not self.process_flow:
            return
        
        for section in self.process_flow.sections:
            if section.section_id == section_id:
                section.steps.append(step)
                # Re-sort steps by step_id
                section.steps.sort(key=lambda s: s.step_id)
                break
    
    def update_step(self, step_id: str, **updates):
        """Update a specific step"""
        if not self.process_flow:
            return
        
        for section in self.process_flow.sections:
            for step in section.steps:
                if step.step_id == step_id:
                    for key, value in updates.items():
                        if hasattr(step, key):
                            setattr(step, key, value)
                    break
    
    def validate_flow(self, flow: ProcessFlow) -> List[str]:
        """Validate process flow for consistency"""
        errors = []
        all_step_ids = set()
        
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
                    if goto_target not in all_step_ids:
                        errors.append(f"Step {step.step_id} references non-existent GOTO target: {goto_target}")
        
        return errors

# Usage example
def main():
    """Example usage of the synchronized process flow system"""
    
    manager = ProcessFlowManager()
    
    # Create the process flow
    flow = manager.create_reentry_system_flow()
    manager.process_flow = flow
    
    # Save machine-readable version
    yaml_content = manager.save_machine_readable(flow, "yaml")
    with open("reentry_process_flow.yaml", "w", encoding="utf-8") as f:
        f.write(yaml_content)
    
    # Generate human-readable version
    human_doc = manager.generate_human_readable(flow)
    with open("reentry_process_flow_human.md", "w", encoding="utf-8") as f:
        f.write(human_doc)
    
    # Example of programmatic editing
    new_step = ProcessStep(
        step_id="0.008",
        actor="PY", 
        description="Initialize monitoring dashboard endpoints.",
        sla_ms=100,
        file_operations=["BIND: http://localhost:8080/health"]
    )
    manager.add_step("0.000", new_step)
    
    # Validate
    errors = manager.validate_flow(flow)
    if errors:
        print("Validation errors:", errors)
    else:
        print("Process flow is valid!")
    
    # Re-generate human doc after changes
    updated_human_doc = manager.generate_human_readable(flow)
    print("\nGenerated human-readable document preview:")
    print(updated_human_doc[:1000] + "...")

if __name__ == "__main__":
    main()
