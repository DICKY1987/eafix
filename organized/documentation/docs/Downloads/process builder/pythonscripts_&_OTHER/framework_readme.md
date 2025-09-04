# Atomic Process Framework

A comprehensive solution for documenting, maintaining, and visualizing complex business processes with sub-process support and multi-format synchronization.

## 🎯 Overview

The Atomic Process Framework addresses the challenge of maintaining complex process documentation by:

- **Keeping multiple formats in sync**: YAML/JSON (machine-readable), Markdown (human-readable), XML (visual diagrams)
- **Supporting sub-processes**: Reusable components that can be injected into main processes at different points
- **Ensuring atomic documentation**: Each step represents a single, well-defined action
- **Tracking value flow**: Monitor how data moves between processes and sub-processes
- **Automatic validation**: Maintain process integrity and consistency
- **Version control friendly**: Git-ready with automatic backup and conflict resolution

## 🏗️ Architecture

The framework consists of several key components:

### Core Components

1. **`atomic_process_framework.py`** - Core data structures and process management
2. **`process_sync_manager.py`** - Multi-format synchronization and file watching
3. **`process_analysis_tools.py`** - Process analysis and optimization tools
4. **`process_cli_tool.py`** - Unified command-line interface
5. **`trading_system_demo.py`** - Complete working example

### Key Features

- **Multi-Format Synchronization**: One source of truth that generates all other formats
- **Sub-Process Management**: Define reusable components once, use everywhere
- **Automatic Validation**: Catch errors before they become problems
- **Performance Analysis**: Identify bottlenecks and optimization opportunities
- **Visual Diagrams**: Auto-generated draw.io compatible flowcharts
- **Version Control**: Git-friendly with intelligent conflict resolution

## 🚀 Quick Start

### Installation

```bash
# Clone or download the framework files
git clone <repository_url>
cd atomic-process-framework

# Install Python dependencies (recommended: Python 3.8+)
pip install pyyaml networkx matplotlib pandas watchdog
```

### Initialize a New Project

```bash
# Basic project
python process_cli_tool.py init my_process_project

# Trading system template
python process_cli_tool.py init trading_system --template trading

cd my_process_project
```

### Start Development

```bash
# Edit the process (opens in your default editor)
python process_cli_tool.py edit

# Start auto-sync (watches for changes)
python process_cli_tool.py sync --watch
```

### Analyze Your Process

```bash
# Run comprehensive analysis
python process_cli_tool.py analyze

# Check project status
python process_cli_tool.py status

# Validate for errors
python process_cli_tool.py validate
```

## 📖 Core Concepts

### Atomic Steps

Each process step represents a single, indivisible action:

```yaml
- step_id: "1.001"
  actor: "SERVICE"
  description: "Validate input data against schema"
  input_variables: ["user_data", "validation_schema"]
  output_variables: ["is_valid", "validation_errors"]
  sla_ms: 100
  validation_rules: ["Schema exists", "Data not empty"]
```

### Sub-Processes

Reusable components that solve specific problems:

```yaml
subprocesses:
  - subprocess_id: "VALIDATE_FILE"
    name: "File Validation"
    description: "Validate file integrity and format"
    inputs:
      inputs:
        - name: "file_path"
          data_type: "string"
          description: "Path to file to validate"
          required: true
    outputs:
      outputs:
        - name: "is_valid"
          data_type: "boolean"
          description: "Whether file is valid"
          required: true
    steps:
      - step_id: "FV.001"
        actor: "SYSTEM"
        description: "Check file exists and compute hash"
        # ... step details
```

### Sub-Process Calls

How main steps use sub-processes:

```yaml
- step_id: "2.003"
  actor: "API"
  description: "Process uploaded file"
  subprocess_calls:
    - subprocess_id: "VALIDATE_FILE"
      input_mapping:
        uploaded_file_path: "file_path"
      output_mapping:
        is_valid: "file_validation_passed"
      description: "Validate uploaded file before processing"
```

### Value Flow

Track how data moves through your process:

```yaml
- step_id: "1.001"
  input_variables: ["raw_data", "config"]
  output_variables: ["processed_data", "metrics"]

- step_id: "1.002"
  input_variables: ["processed_data"]  # Consumes output from 1.001
  output_variables: ["final_result"]
```

## 🔧 Framework Components

### 1. Core Framework (`atomic_process_framework.py`)

The heart of the system with data structures for:

- **ProcessFlow**: Complete process documentation
- **ProcessSection**: Major process sections (e.g., "Initialization", "Processing")
- **ProcessStep**: Individual atomic actions
- **SubProcess**: Reusable process components
- **SubProcessCall**: Integration points between main and sub-processes

Key methods:
- `create_reentry_system_flow()` - Example implementation
- `save_machine_readable(flow, format)` - Export to YAML/JSON
- `load_machine_readable(content, format)` - Import from YAML/JSON
- `generate_human_readable(flow)` - Create Markdown documentation
- `generate_drawio_xml(flow)` - Create visual diagrams
- `validate_flow(flow)` - Check for errors and inconsistencies

### 2. Sync Manager (`process_sync_manager.py`)

Maintains synchronization between all formats:

- **File watching**: Automatic sync when files change
- **Conflict resolution**: Intelligent handling of simultaneous edits
- **Backup management**: Automatic backups with retention policies
- **Hash tracking**: Detect changes efficiently

Configuration example:
```json
{
  "sync_strategy": "yaml_primary",
  "auto_backup": true,
  "validation_on_sync": true,
  "files": {
    "machine_yaml": "process_flow.yaml",
    "machine_json": "process_flow.json", 
    "human_md": "process_flow.md",
    "visual_xml": "process_flow.drawio"
  }
}
```

### 3. Analysis Tools (`process_analysis_tools.py`)

Comprehensive process analysis capabilities:

- **Performance Analysis**: Identify bottlenecks and SLA violations
- **Complexity Analysis**: Measure maintainability and complexity
- **Quality Analysis**: Assess documentation and error handling
- **Optimization Recommendations**: Actionable improvement suggestions
- **Visual Analytics**: Process graphs and flow charts

Example analysis output:
```json
{
  "performance_metrics": {
    "total_estimated_time_ms": 15420,
    "critical_path_time_ms": 8900,
    "bottleneck_steps": [...]
  },
  "complexity_metrics": {
    "total_steps": 47,
    "cyclomatic_complexity": 12,
    "maintainability_score": 7.8
  }
}
```

### 4. CLI Tool (`process_cli_tool.py`)

Unified command-line interface:

```bash
# Project management
process-doc init <project>              # Initialize new project
process-doc status                      # Show project status
process-doc validate                    # Check for errors

# Content management  
process-doc edit                        # Edit process file
process-doc sync [--watch]             # Synchronize formats
process-doc analyze                     # Run analysis

# Export
process-doc export --format html       # Export to HTML
process-doc export --format zip        # Create archive
```

## 🎨 Working with the Framework

### Project Structure

A typical project looks like:

```
my_process_project/
├── process_flow.yaml           # Primary source (edit this)
├── process_flow.json           # Auto-generated JSON
├── process_flow.md             # Auto-generated documentation
├── process_flow.drawio         # Auto-generated diagram
├── sync_config.json            # Synchronization settings
├── backups/                    # Automatic backups
├── logs/                       # Sync and error logs
└── analysis_reports/           # Analysis outputs
    ├── analysis_report.json
    ├── analysis_summary.md
    └── process_graph.png
```

### Recommended Workflow

1. **Initialize**: Create new project with appropriate template
2. **Edit**: Modify the YAML file (primary source)
3. **Sync**: Keep all formats synchronized automatically
4. **Analyze**: Regularly check for optimization opportunities
5. **Version Control**: Use git to track changes over time

### Best Practices

#### Process Design
- **Keep steps atomic**: One action per step
- **Use meaningful IDs**: Sequential numbering (1.001, 1.002, etc.)
- **Document SLAs**: Include realistic performance targets
- **Plan for errors**: Include error handling and GOTO targets

#### Sub-Process Design
- **Make them reusable**: Design for multiple use cases
- **Clear interfaces**: Well-defined inputs and outputs
- **Single responsibility**: Each sub-process should do one thing well
- **Version carefully**: Track changes to sub-process interfaces

#### Value Flow
- **Explicit variables**: Clearly name input/output variables
- **Minimize coupling**: Reduce dependencies between steps
- **Validate early**: Check inputs at process boundaries
- **Document transformations**: Explain how values change

#### Maintenance
- **Use YAML as primary**: Most human-readable for editing
- **Enable auto-sync**: Use watch mode during active development
- **Regular backups**: Keep retention policy appropriate
- **Validate frequently**: Run validation after major changes

## 📊 Analysis and Optimization

### Performance Analysis

The framework provides detailed performance insights:

- **Critical Path**: Longest execution path through the process
- **Bottleneck Detection**: Steps taking longer than expected
- **Parallel Potential**: Opportunities for concurrent execution
- **Actor Utilization**: Workload distribution across actors

### Quality Metrics

Assess the quality of your process documentation:

- **Documentation Completeness**: How well-documented are your steps?
- **Validation Coverage**: Do you validate inputs and outputs?
- **Error Handling**: Are failure scenarios properly handled?
- **SLA Completeness**: Do you have performance targets?

### Optimization Recommendations

Get actionable suggestions:

- **Performance Improvements**: Speed up slow operations
- **Complexity Reduction**: Simplify overly complex workflows
- **Modularity Enhancement**: Extract reusable sub-processes
- **Documentation Gaps**: Improve process clarity

## 🔍 Advanced Features

### Custom Validation Rules

Add domain-specific validations:

```python
def custom_validation(flow: ProcessFlow) -> List[str]:
    errors = []
    
    # Example: Ensure file operations have backups
    for section in flow.sections:
        for step in section.steps:
            if any("WRITE" in op for op in step.file_operations):
                if not any("BACKUP" in op for op in step.file_operations):
                    errors.append(f"Step {step.step_id} writes files but has no backup")
    
    return errors
```

### Programmatic Process Editing

Modify processes programmatically:

```python
# Load existing process
framework = AtomicProcessFramework()
flow = framework.load_machine_readable(yaml_content, "yaml")

# Add new validation step
new_step = ProcessStep(
    step_id="2.005",
    actor="VALIDATOR",
    description="Additional security check",
    sla_ms=50
)

# Inject into appropriate section
for section in flow.sections:
    if section.section_id == "2.000":
        section.steps.append(new_step)
        section.steps.sort(key=lambda s: s.step_id)

# Save updated process
updated_yaml = framework.save_machine_readable(flow, "yaml")
```

### Sub-Process Injection

Dynamically add sub-process calls:

```python
# Create new sub-process call
validation_call = SubProcessCall(
    subprocess_id="SECURITY_CHECK",
    input_mapping={"user_data": "data_to_check"},
    output_mapping={"is_secure": "security_validated"},
    description="Validate data security"
)

# Inject into existing step
framework.inject_subprocess("1.003", validation_call)
```

### Custom Output Formats

Extend the framework with new output formats:

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
    return "\\n".join(output)
```

## 🎯 Use Cases

### 1. Software Development Pipeline

Document CI/CD processes with atomic steps:

```yaml
title: "Continuous Integration Pipeline"
sections:
  - section_id: "1.000"
    title: "Code Integration"
    steps:
      - step_id: "1.001"
        actor: "GIT"
        description: "Receive code push trigger"
        subprocess_calls:
          - subprocess_id: "VALIDATE_COMMIT"
            description: "Validate commit message and content"
```

### 2. Customer Onboarding

Track customer journey with validation points:

```yaml
title: "Customer Onboarding Process"
sections:
  - section_id: "1.000"
    title: "Initial Registration"
    steps:
      - step_id: "1.001"
        actor: "WEB_PORTAL"
        description: "Collect customer information"
        subprocess_calls:
          - subprocess_id: "KYC_VALIDATION"
            description: "Know Your Customer validation"
```

### 3. Financial Processing

Document complex financial workflows:

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
            description: "Assess trade risk parameters"
```

### 4. Manufacturing Process

Document production workflows:

```yaml
title: "Product Manufacturing Process"
sections:
  - section_id: "1.000"
    title: "Quality Control"
    steps:
      - step_id: "1.001"
        actor: "QC_SYSTEM"
        description: "Inspect raw materials"
        subprocess_calls:
          - subprocess_id: "MATERIAL_TEST"
            description: "Test material specifications"
```

## 🔧 Extending the Framework

### Adding New Analysis Types

```python
class CustomAnalyzer:
    def analyze_security(self, flow: ProcessFlow):
        """Custom security analysis"""
        security_score = 0
        
        for section in flow.sections:
            for step in section.steps:
                # Check for security-related validations
                if any("security" in rule.lower() for rule in step.validation_rules):
                    security_score += 1
        
        return {"security_steps": security_score}
```

### Creating Custom Templates

```python
def create_custom_template():
    """Create industry-specific template"""
    
    # Define industry-specific sub-processes
    compliance_check = SubProcess(
        subprocess_id="COMPLIANCE_CHECK",
        name="Regulatory Compliance Validation",
        # ... implementation
    )
    
    # Define template structure
    template_flow = ProcessFlow(
        title="Industry-Specific Process",
        subprocesses=[compliance_check],
        # ... rest of template
    )
    
    return template_flow
```

### Integration with External Tools

```python
def export_to_external_tool(flow: ProcessFlow):
    """Export to external process management tool"""
    
    # Convert to external format
    external_format = {
        "process_name": flow.title,
        "version": flow.version,
        "steps": []
    }
    
    for section in flow.sections:
        for step in section.steps:
            external_format["steps"].append({
                "id": step.step_id,
                "name": step.description,
                "actor": step.actor,
                "duration_ms": step.sla_ms
            })
    
    return external_format
```

## 🤝 Contributing

### Framework Extension Points

1. **New Output Formats**: Add generators for other diagram types
2. **Additional Validations**: Implement domain-specific checks  
3. **Performance Metrics**: Add new analysis capabilities
4. **Integration Hooks**: Connect with other tools and systems

### Development Setup

```bash
# Clone repository
git clone <repository_url>
cd atomic-process-framework

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Run example
python trading_system_demo.py
```

### Code Structure

- `atomic_process_framework.py` - Core data structures and logic
- `process_sync_manager.py` - File synchronization and watching
- `process_analysis_tools.py` - Analysis and optimization tools
- `process_cli_tool.py` - Command-line interface
- `trading_system_demo.py` - Complete working example
- `tests/` - Unit tests and integration tests
- `docs/` - Additional documentation and examples

## 📚 Examples and Templates

### Basic Template

Simple process with minimal complexity:

```yaml
title: "Basic Process Flow"
sections:
  - section_id: "1.000"
    title: "Main Process"
    steps:
      - step_id: "1.001"
        actor: "SYSTEM"
        description: "Initialize process"
```

### Trading System Template

Complete financial trading system (included in demo):

- Complex sub-process integration
- Performance-critical SLAs
- Error handling and recovery
- Multi-actor coordination

### Manufacturing Template

Production process with quality control:

- Quality gates and inspections
- Material flow tracking
- Compliance validations
- Equipment coordination

## 🆘 Troubleshooting

### Common Issues

**Sync Errors**
```bash
# Reset sync state
python process_cli_tool.py sync --force

# Check file permissions
ls -la *.yaml *.json *.md
```

**Validation Failures**
```bash
# Run detailed validation
python process_cli_tool.py validate

# Check for common issues:
# - Duplicate step IDs
# - Invalid GOTO targets
# - Missing sub-process references
```

**Performance Issues**
```bash
# Analyze process complexity
python process_cli_tool.py analyze

# Look for:
# - High cyclomatic complexity
# - Long SLA times
# - Too many actors
```

### Getting Help

1. **Check the examples**: Review `trading_system_demo.py`
2. **Validate your process**: Use built-in validation
3. **Check logs**: Look in `logs/` directory
4. **Use analysis tools**: Identify common problems
5. **Review documentation**: Check this README and usage guide

## 📄 License

MIT License - see LICENSE file for details.

## 🙏 Acknowledgments

This framework was built to solve real-world process documentation challenges, particularly in complex financial trading systems. It emphasizes:

- **Maintainability**: Keep documentation in sync automatically
- **Modularity**: Reuse common patterns through sub-processes
- **Clarity**: Atomic steps make processes easy to understand
- **Quality**: Built-in analysis and validation tools

---

*The Atomic Process Framework provides a solid foundation for documenting and maintaining complex business processes. Start simple with basic templates and gradually add complexity as your needs evolve.*