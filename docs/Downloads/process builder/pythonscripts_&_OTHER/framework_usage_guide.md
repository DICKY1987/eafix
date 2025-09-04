# Atomic Process Framework - Complete Usage Guide

## Overview

The Atomic Process Framework is a comprehensive solution for documenting, maintaining, and visualizing complex business processes with sub-process support and multi-format synchronization.

## 🎯 Key Features

- **Multi-Format Synchronization**: YAML/JSON (machine-readable), Markdown (human-readable), XML (visual diagrams)
- **Sub-Process Management**: Reusable components that can be injected into main processes
- **Atomic Step Documentation**: Each step is a single, well-defined action
- **Value Flow Tracking**: Track how data flows between processes and sub-processes
- **Automatic Validation**: Ensure process integrity and consistency
- **Version Control Ready**: Git-friendly with automatic backup and conflict resolution

## 🚀 Quick Start

### 1. Installation and Setup

```bash
# Create project directory
mkdir my_process_docs
cd my_process_docs

# Copy framework files
cp atomic_process_framework.py .
cp process_sync_manager.py .
cp trading_system_demo.py .

# Initialize the framework
python process_sync_manager.py --init
```

### 2. Basic Usage

```python
from atomic_process_framework import AtomicProcessFramework
from process_sync_manager import ProcessSyncManager

# Create framework instance
framework = AtomicProcessFramework("./docs")
sync_manager = ProcessSyncManager("./docs")

# Create initial files
sync_manager.create_initial_files()

# Start watching for changes
sync_manager.watch_files()  # Runs continuously
```

### 3. Configuration

The framework uses `sync_config.json` for configuration:

```json
{
  "version": "1.0",
  "sync_strategy": "yaml_primary",
  "auto_backup": true,
  "backup_retention_days": 30,
  "validation_on_sync": true,
  "files": {
    "machine_yaml": "process_flow.yaml",
    "machine_json": "process_flow.json",
    "human_md": "process_flow_human.md",
    "visual_xml": "process_flow_visual.drawio"
  }
}
```

## 📖 Core Concepts

### Atomic Steps

Each process step represents a single, indivisible action:

```python
ProcessStep(
    step_id="1.001",
    actor="PY",
    description="Load configuration file and validate format",
    input_variables=["config_path"],
    output_variables=["config_data", "is_valid"],
    sla_ms=500,
    validation_rules=["File exists", "Valid JSON format"]
)
```

### Sub-Processes

Reusable components that can be called from multiple main process steps:

```python
SubProcess(
    subprocess_id="VALIDATE_FILE",
    name="File Validation",
    description="Validate file integrity and format",
    inputs=ProcessInput(inputs=[
        ValueSpec("file_path", "string", "Path to file", True)
    ]),
    outputs=ProcessOutput(outputs=[
        ValueSpec("is_valid", "boolean", "Validation result", True)
    ]),
    steps=[...] # Sub-process steps
)
```

### Sub-Process Calls

How main process steps call sub-processes:

```python
SubProcessCall(
    subprocess_id="VALIDATE_FILE",
    input_mapping={"user_file": "file_path"},
    output_mapping={"is_valid": "file_ok"},
    description="Validate user-uploaded file"
)
```

## 🔧 Advanced Usage

### 1. Creating Custom Process Flows

```python
def create_my_process_flow():
    # Define sub-processes
    validation_subprocess = SubProcess(
        subprocess_id="DATA_VALIDATE",
        name="Data Validation",
        description="Validate input data against schema",
        version="1.0",
        inputs=ProcessInput(inputs=[
            ValueSpec("data", "object", "Data to validate", True),
            ValueSpec("schema", "object", "Validation schema", True)
        ]),
        outputs=ProcessOutput(outputs=[
            ValueSpec("is_valid", "boolean", "Validation result", True),
            ValueSpec("errors", "array", "Validation errors", False, [])
        ]),
        steps=[
            ProcessStep(
                step_id="DV.001",
                actor="SERVICE",
                description="Apply schema validation rules",
                input_variables=["data", "schema"],
                output_variables=["is_valid", "errors"],
                sla_ms=100
            )
        ]
    )
    
    # Define main process sections
    main_section = ProcessSection(
        section_id="1.000",
        title="Data Processing Pipeline",
        description="Main data processing workflow",
        actors=["SERVICE"],
        transport="API",
        steps=[
            ProcessStep(
                step_id="1.001",
                actor="SERVICE",
                description="Receive and validate input data",
                subprocess_calls=[
                    SubProcessCall(
                        subprocess_id="DATA_VALIDATE",
                        input_mapping={"input_data": "data", "input_schema": "schema"},
                        output_mapping={"is_valid": "data_valid", "errors": "validation_errors"}
                    )
                ],
                input_variables=["input_data", "input_schema"],
                output_variables=["data_valid", "validation_errors"],
                sla_ms=200
            )
        ]
    )
    
    # Create complete flow
    return ProcessFlow(
        title="My Custom Process",
        version="1.0",
        date=datetime.now().strftime("%Y-%m-%d"),
        sections=[main_section],
        subprocesses=[validation_subprocess]
    )
```

### 2. Programmatic Process Editing

```python
# Load existing process
framework = AtomicProcessFramework()
with open("process.yaml", "r") as f:
    flow = framework.load_machine_readable(f.read(), "yaml")

# Add new step
new_step = ProcessStep(
    step_id="2.005",
    actor="API",
    description="New validation step",
    sla_ms=100
)

# Find section and insert step
for section in flow.sections:
    if section.section_id == "2.000":
        section.steps.append(new_step)
        section.steps.sort(key=lambda s: s.step_id)
        break

# Save updated flow
yaml_content = framework.save_machine_readable(flow, "yaml")
with open("process.yaml", "w") as f:
    f.write(yaml_content)
```

### 3. Value Flow Analysis

```python
def analyze_value_flow(flow: ProcessFlow):
    """Analyze how values flow through the process"""
    
    value_producers = {}  # variable -> list of steps that produce it
    value_consumers = {}  # variable -> list of steps that consume it
    
    for section in flow.sections:
        for step in section.steps:
            # Track producers
            for var in step.output_variables:
                if var not in value_producers:
                    value_producers[var] = []
                value_producers[var].append(step.step_id)
            
            # Track consumers
            for var in step.input_variables:
                if var not in value_consumers:
                    value_consumers[var] = []
                value_consumers[var].append(step.step_id)
    
    # Find orphaned variables
    orphaned = []
    for var in value_consumers:
        if var not in value_producers:
            orphaned.append(var)
    
    return {
        "producers": value_producers,
        "consumers": value_consumers,
        "orphaned_variables": orphaned
    }
```

## 🔄 Synchronization Workflow

### Primary Source Strategy

1. **YAML Primary** (Recommended):
   - Edit `process_flow.yaml` as the master source
   - All other formats auto-generate from YAML
   - Human-readable and version-control friendly

2. **JSON Primary**:
   - Edit `process_flow.json` as master
   - More compact but less human-readable

### Sync Commands

```bash
# One-time sync check
python process_sync_manager.py --sync

# Continuous watching (auto-sync)
python process_sync_manager.py --watch

# Force rebuild all formats
python process_sync_manager.py --force-rebuild

# Check sync status
python process_sync_manager.py --status

# Clean old backups
python process_sync_manager.py --cleanup
```

### Conflict Resolution

When multiple files change simultaneously:

1. **Primary source changed**: Regenerate all secondary formats
2. **Only secondary files changed**: Warning issued, recommend editing primary
3. **Multiple primaries changed**: Manual intervention required

## 📊 Process Analysis and Optimization

### Performance Analysis

```python
def analyze_performance(flow: ProcessFlow):
    """Analyze process performance characteristics"""
    
    total_sla = 0
    step_count = 0
    sla_by_actor = {}
    
    for section in flow.sections:
        for step in section.steps:
            if step.sla_ms:
                total_sla += step.sla_ms
                step_count += 1
                
                if step.actor not in sla_by_actor:
                    sla_by_actor[step.actor] = []
                sla_by_actor[step.actor].append(step.sla_ms)
    
    return {
        "total_estimated_time_ms": total_sla,
        "average_step_time_ms": total_sla / step_count if step_count > 0 else 0,
        "step_count": step_count,
        "performance_by_actor": {
            actor: {
                "total_ms": sum(times),
                "average_ms": sum(times) / len(times),
                "step_count": len(times)
            }
            for actor, times in sla_by_actor.items()
        }
    }
```

### Complexity Analysis

```python
def analyze_complexity(flow: ProcessFlow):
    """Analyze process complexity metrics"""
    
    metrics = {
        "total_steps": 0,
        "total_sections": len(flow.sections),
        "total_subprocesses": len(flow.subprocesses),
        "subprocess_calls": 0,
        "goto_statements": 0,
        "actors": set(),
        "max_section_size": 0,
        "branching_factor": 0
    }
    
    for section in flow.sections:
        metrics["total_steps"] += len(section.steps)
        metrics["max_section_size"] = max(metrics["max_section_size"], len(section.steps))
        
        for step in section.steps:
            metrics["actors"].add(step.actor)
            metrics["subprocess_calls"] += len(step.subprocess_calls)
            metrics["goto_statements"] += len(step.goto_targets)
            
            if len(step.goto_targets) > 1:
                metrics["branching_factor"] += len(step.goto_targets) - 1
    
    metrics["actors"] = list(metrics["actors"])
    
    return metrics
```

## 🎨 Visual Diagram Customization

### Draw.io Integration

The framework generates draw.io compatible XML that you can:

1. Import into draw.io web app or desktop
2. Customize colors, shapes, and layout
3. Add additional annotations
4. Export to various formats (PNG, PDF, SVG)

### Custom Visual Properties

```python
ProcessStep(
    step_id="1.001",
    actor="API",
    description="Process request",
    visual_properties={
        "color": "#FFE6CC",
        "shape": "rectangle",
        "icon": "🔧",
        "position": {"x": 100, "y": 200}
    }
)
```

## 🔍 Validation and Quality Assurance

### Built-in Validations

1. **Structural Validation**:
   - No duplicate step IDs
   - Valid GOTO targets
   - Sub-process references exist

2. **Flow Validation**:
   - No orphaned steps
   - Proper dependencies
   - Value flow consistency

3. **Performance Validation**:
   - SLA targets reasonable
   - No excessive complexity

### Custom Validation Rules

```python
def custom_validation(flow: ProcessFlow) -> List[str]:
    """Add custom validation rules"""
    errors = []
    
    # Example: Ensure all file operations have backups
    for section in flow.sections:
        for step in section.steps:
            if any("WRITE" in op for op in step.file_operations):
                if not any("BACKUP" in op for op in step.file_operations):
                    errors.append(f"Step {step.step_id} writes files but has no backup")
    
    return errors
```

## 🚀 Best Practices

### 1. Process Design

- **Keep steps atomic**: One action per step
- **Use meaningful IDs**: Sequential numbering (1.001, 1.002)
- **Document SLAs**: Include realistic performance targets
- **Plan for errors**: Include error handling and retry logic

### 2. Sub-Process Design

- **Make them reusable**: Design for multiple use cases
- **Clear interfaces**: Well-defined inputs and outputs
- **Single responsibility**: Each sub-process should do one thing well
- **Version carefully**: Track changes to sub-process interfaces

### 3. Value Flow

- **Explicit variables**: Clearly name input/output variables
- **Minimize coupling**: Reduce dependencies between steps
- **Validate early**: Check inputs at process boundaries
- **Document transformations**: Explain how values change

### 4. Maintenance

- **Use YAML as primary**: Most human-readable for editing
- **Enable auto-sync**: Use watch mode during active development
- **Regular backups**: Keep retention policy appropriate
- **Validate frequently**: Run validation after major changes

## 🔧 Extending the Framework

### Adding New Output Formats

```python
def generate_plantuml(flow: ProcessFlow) -> str:
    """Generate PlantUML sequence diagram"""
    
    output = ["@startuml"]
    
    for section in flow.sections:
        output.append(f"== {section.title} ==")
        
        for step in section.steps:
            if step.subprocess_calls:
                for call in step.subprocess_calls:
                    output.append(f"{step.actor} -> {call.subprocess_id}: {call.description}")
            else:
                output.append(f"{step.actor} -> {step.actor}: {step.description}")
    
    output.append("@enduml")
    return "\n".join(output)
```

### Custom Metrics

```python
class ProcessMetrics:
    """Custom metrics collection for process analysis"""
    
    def __init__(self, flow: ProcessFlow):
        self.flow = flow
        
    def calculate_critical_path(self) -> List[str]:
        """Find the longest execution path through the process"""
        # Implementation for critical path analysis
        pass
        
    def identify_bottlenecks(self) -> List[Dict]:
        """Identify potential performance bottlenecks"""
        bottlenecks = []
        
        for section in self.flow.sections:
            for step in section.steps:
                if step.sla_ms and step.sla_ms > 1000:  # > 1 second
                    bottlenecks.append({
                        "step_id": step.step_id,
                        "sla_ms": step.sla_ms,
                        "description": step.description,
                        "severity": "high" if step.sla_ms > 5000 else "medium"
                    })
        
        return bottlenecks
```

## 📚 Example Use Cases

### 1. Software Development Pipeline

```yaml
title: "CI/CD Pipeline Process"
sections:
  - section_id: "1.000"
    title: "Code Integration"
    steps:
      - step_id: "1.001"
        actor: "GIT"
        description: "Receive code push trigger"
        subprocess_calls:
          - subprocess_id: "VALIDATE_COMMIT"
```

### 2. Customer Onboarding

```yaml
title: "Customer Onboarding Process"
sections:
  - section_id: "1.000"
    title: "Initial Registration"
    steps:
      - step_id: "1.001"
        actor: "WEB"
        description: "Collect customer information"
        subprocess_calls:
          - subprocess_id: "VALIDATE_KYC"
```

### 3. Financial Trade Processing

```yaml
title: "Trade Processing Pipeline"
sections:
  - section_id: "1.000"
    title: "Order Validation"
    steps:
      - step_id: "1.001"
        actor: "OMS"
        description: "Validate order parameters"
        subprocess_calls:
          - subprocess_id: "RISK_CHECK"
```

## 🤝 Contributing and Support

### Framework Extension Points

1. **New Output Formats**: Add generators for other diagram types
2. **Additional Validations**: Implement domain-specific checks
3. **Performance Metrics**: Add new analysis capabilities
4. **Integration Hooks**: Connect with other tools and systems

### Getting Help

1. Review the example implementations
2. Check the validation error messages
3. Use the status report for debugging
4. Enable verbose logging for troubleshooting

---

*This framework provides a solid foundation for documenting and maintaining complex business processes. The key is to start simple and gradually add complexity as your needs evolve.*