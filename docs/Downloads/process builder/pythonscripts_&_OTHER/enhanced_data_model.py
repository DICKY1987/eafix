#!/usr/bin/env python3
"""
Enhanced Atomic Process Framework - Data Model
Addresses step sequencing, standardization, and enterprise requirements
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any
from enum import Enum
import uuid
from datetime import datetime

# ===== Enhanced Enums and Types =====

class ErrorPolicy(Enum):
    RETRY = "retry"
    HALT = "halt"
    ESCALATE = "escalate"
    SKIP = "skip"
    CONTINUE = "continue"

class TriggerType(Enum):
    FILE_WATCH = "file_watch"
    TIMER = "timer"
    EVENT = "event"
    API_CALL = "api_call"
    MANUAL = "manual"

class ValidationSeverity(Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class MetricType(Enum):
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    TIMER = "timer"

# ===== Registry Definitions =====

@dataclass
class Role:
    """Canonical role definition"""
    id: str  # ROLE.OPS, ROLE.DEVOPS, etc.
    name: str
    description: str = ""
    permissions: List[str] = field(default_factory=list)
    contact_info: Dict[str, str] = field(default_factory=dict)

@dataclass
class System:
    """Canonical system definition"""
    id: str  # SYS.PY_INGEST, SYS.MT4_EA, etc.
    name: str
    description: str = ""
    type: str = ""  # service, database, external_api, etc.
    endpoints: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)

@dataclass
class Artifact:
    """Canonical artifact/data definition"""
    id: str  # ART.RAW_CAL, ART.NORM_CAL, etc.
    name: str
    description: str = ""
    format: str = ""  # csv, json, xml, binary, etc.
    schema: Dict[str, Any] = field(default_factory=dict)
    location_pattern: str = ""
    retention_policy: str = ""

@dataclass
class DataModel:
    """Shared data model definition"""
    id: str  # DM.CALENDAR_ROW, DM.TRADE_SIGNAL, etc.
    description: str
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)

# ===== Enhanced Step Definitions =====

@dataclass
class Trigger:
    """Step trigger definition"""
    type: TriggerType
    config: Dict[str, Any] = field(default_factory=dict)
    description: str = ""

@dataclass
class Validation:
    """Validation rule definition"""
    id: str
    description: str
    rule: str  # Executable validation logic
    severity: ValidationSeverity = ValidationSeverity.ERROR
    remediation: str = ""

@dataclass
class ErrorHandling:
    """Comprehensive error handling specification"""
    policy: ErrorPolicy = ErrorPolicy.HALT
    retries: int = 0
    backoff_strategy: str = "linear:30s"  # linear:Xs, exponential:Xs..Ym
    timeout_ms: Optional[int] = None
    escalation_role: Optional[str] = None
    recovery_step: Optional[str] = None
    cleanup_actions: List[str] = field(default_factory=list)

@dataclass
class Metric:
    """Observability metric definition"""
    name: str
    type: MetricType
    description: str = ""
    labels: List[str] = field(default_factory=list)
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None

@dataclass
class AuditSpec:
    """Audit and compliance specification"""
    events: List[str] = field(default_factory=list)  # Audit events to log
    required_fields: List[str] = field(default_factory=list)  # Required audit fields
    retention_days: int = 90
    compliance_tags: List[str] = field(default_factory=list)

@dataclass
class TraceabilitySpec:
    """Traceability and testing specification"""
    spec_refs: List[str] = field(default_factory=list)  # Links to specs
    test_refs: List[str] = field(default_factory=list)  # Links to tests
    change_history: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class StepIO:
    """Enhanced input/output specification"""
    artifact: str  # Reference to artifact ID
    location: str = ""  # Specific location/path
    required: bool = True
    validation: Optional[str] = None  # Validation rule reference
    transformation: Optional[str] = None  # Data transformation spec

# ===== Enhanced ProcessStep =====

@dataclass
class EnhancedProcessStep:
    """Enterprise-grade process step definition"""
    
    # Core identification
    step_id: str
    name: str
    intent: str  # What this step accomplishes
    description: str = ""
    
    # Ownership and execution
    owner: str  # Role reference (ROLE.OPS)
    system: str  # System reference (SYS.PY_INGEST) 
    actor: str = ""  # Backward compatibility
    
    # Flow control and triggers
    trigger: Optional[Trigger] = None
    preconditions: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    postconditions: List[str] = field(default_factory=list)
    
    # Enhanced I/O
    inputs: List[StepIO] = field(default_factory=list)
    outputs: List[StepIO] = field(default_factory=list)
    
    # Flow control
    on_success: Optional[str] = None  # Next step ID
    on_error: Optional[ErrorHandling] = None
    conditions: List[str] = field(default_factory=list)  # Backward compatibility
    
    # Sub-process integration (enhanced)
    subprocess_calls: List['SubProcessCall'] = field(default_factory=list)
    
    # Quality and validation
    validations: List[Validation] = field(default_factory=list)
    sla_ms: Optional[int] = None
    timeout_ms: Optional[int] = None
    
    # Observability
    metrics: List[Metric] = field(default_factory=list)
    audit: Optional[AuditSpec] = None
    trace: Optional[TraceabilitySpec] = None
    
    # Legacy compatibility
    dependencies: List[str] = field(default_factory=list)
    goto_targets: List[str] = field(default_factory=list)
    file_operations: List[str] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    error_codes: List[str] = field(default_factory=list)
    input_variables: List[str] = field(default_factory=list)
    output_variables: List[str] = field(default_factory=list)
    notes: str = ""
    
    # Metadata
    created_by: str = ""
    created_at: Optional[datetime] = None
    updated_by: str = ""
    updated_at: Optional[datetime] = None
    version: str = "1.0"
    
    # Visual properties for diagram generation
    visual_properties: Dict[str, Any] = field(default_factory=dict)

# ===== Process Flow Organization =====

@dataclass
class NamedFlow:
    """Named path through the process"""
    id: str
    name: str
    description: str
    step_sequence: List[str]
    conditions: List[str] = field(default_factory=list)

@dataclass
class ProcessValidation:
    """Process-level validation"""
    id: str
    description: str
    rule: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    scope: str = "global"  # global, section, step

@dataclass
class ExitCheck:
    """Quality gate at process completion"""
    id: str
    description: str
    rule: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    required_artifacts: List[str] = field(default_factory=list)

# ===== Enhanced ProcessSection =====

@dataclass
class EnhancedProcessSection:
    """Enhanced process section with registries"""
    section_id: str
    title: str
    description: str
    
    # Step management
    steps: List[EnhancedProcessStep] = field(default_factory=list)
    
    # Flow definitions
    default_flow: List[str] = field(default_factory=list)  # Default step sequence
    named_flows: List[NamedFlow] = field(default_factory=list)
    
    # Section-level specifications
    owner: str = ""  # Primary section owner
    systems: List[str] = field(default_factory=list)  # Systems involved
    sla_target_ms: Optional[int] = None  # Total section SLA
    
    # Legacy compatibility
    actors: List[str] = field(default_factory=list)
    transport: str = ""
    
    # Advanced step management methods
    def insert_step_after(self, target_step_id: str, new_step: EnhancedProcessStep) -> bool:
        """Insert step after target with automatic sequencing"""
        # Implementation for intelligent step insertion
        pass
        
    def insert_step_before(self, target_step_id: str, new_step: EnhancedProcessStep) -> bool:
        """Insert step before target with automatic sequencing"""
        # Implementation for intelligent step insertion
        pass
        
    def renumber_steps(self, start_index: int = 0) -> Dict[str, str]:
        """Renumber steps and return old_id -> new_id mapping"""
        # Implementation for automatic renumbering
        pass
        
    def validate_flow_integrity(self) -> List[str]:
        """Validate that all flow references are valid"""
        # Implementation for flow validation
        pass

# ===== Enhanced ProcessFlow =====

@dataclass
class EnhancedProcessFlow:
    """Enterprise-grade process flow definition"""
    
    # Core metadata
    schema_version: str = "2.0"
    process_id: str = ""  # Stable, machine-friendly ID
    title: str = ""
    version: str = "1.0"
    date: str = ""
    description: str = ""
    domain: str = ""
    owner: str = ""
    stakeholders: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Canonical registries
    roles: List[Role] = field(default_factory=list)
    systems: List[System] = field(default_factory=list)
    artifacts: List[Artifact] = field(default_factory=list)
    data_models: List[DataModel] = field(default_factory=list)
    enums: Dict[str, List[str]] = field(default_factory=dict)
    
    # Process structure
    sections: List[EnhancedProcessSection] = field(default_factory=list)
    subprocesses: List['EnhancedSubProcess'] = field(default_factory=list)
    
    # Named flows and patterns
    flows: Dict[str, List[str]] = field(default_factory=dict)
    
    # Quality framework
    validations: List[ProcessValidation] = field(default_factory=list)
    exit_checks: List[ExitCheck] = field(default_factory=list)
    
    # Global specifications
    global_inputs: List[StepIO] = field(default_factory=list)
    global_outputs: List[StepIO] = field(default_factory=list)
    
    # Legacy compatibility
    id_conventions: str = ""
    legend: str = ""
    file_paths: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Process lifecycle
    created_by: str = ""
    created_at: Optional[datetime] = None
    updated_by: str = ""
    updated_at: Optional[datetime] = None

# ===== Enhanced SubProcess =====

@dataclass
class EnhancedSubProcess:
    """Enhanced reusable sub-process"""
    subprocess_id: str
    name: str
    description: str
    version: str = "1.0"
    
    # Enhanced I/O with registries
    inputs: List[StepIO] = field(default_factory=list)
    outputs: List[StepIO] = field(default_factory=list)
    
    # Implementation
    steps: List[EnhancedProcessStep] = field(default_factory=list)
    flows: Dict[str, List[str]] = field(default_factory=dict)
    
    # Quality and governance
    validations: List[Validation] = field(default_factory=list)
    error_handling: Optional[ErrorHandling] = None
    
    # Metadata and tracking
    tags: List[str] = field(default_factory=list)
    complexity_score: Optional[int] = None
    reuse_count: int = 0
    owner: str = ""
    
    # Lifecycle tracking
    created_by: str = ""
    created_at: Optional[datetime] = None
    updated_by: str = ""
    updated_at: Optional[datetime] = None
    
    # Visual properties
    visual_properties: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EnhancedSubProcessCall:
    """Enhanced sub-process invocation"""
    subprocess_id: str
    call_id: str = ""  # Unique call identifier
    input_mapping: Dict[str, str] = field(default_factory=dict)
    output_mapping: Dict[str, str] = field(default_factory=dict)
    description: str = ""
    
    # Enhanced call configuration
    timeout_override_ms: Optional[int] = None
    retry_override: Optional[ErrorHandling] = None
    async_execution: bool = False
    
    # Call-specific validations
    precall_validations: List[Validation] = field(default_factory=list)
    postcall_validations: List[Validation] = field(default_factory=list)