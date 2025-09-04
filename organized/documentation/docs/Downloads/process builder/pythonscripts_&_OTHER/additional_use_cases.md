# Additional Industry Use Case Examples

## Use Case 2: Healthcare Patient Care Protocol

### Scenario: Emergency Department Triage Process

**Enhanced Framework Benefits**:

```yaml
schema_version: 2.0
process:
  id: PROC.HEALTHCARE.ED_TRIAGE
  name: "Emergency Department Patient Triage Protocol"
  compliance_frameworks: ["HIPAA", "HITECH", "Joint_Commission"]

# Reusable clinical assessments
subprocesses:
  - subprocess_id: VITAL_SIGNS_ASSESSMENT
    name: "Standard Vital Signs Assessment"
    inputs:
      - name: patient_id
        data_type: string
        required: true
    outputs:
      - name: acuity_score
        data_type: number
        required: true
      - name: critical_flags
        data_type: array
        required: true

# Clinical decision flows
flows:
  critical_pathway:
    - "1.001"  # Patient registration
    - "1.002"  # Immediate assessment
    - "2.001"  # Critical care activation
  
  standard_pathway:
    - "1.001"  # Patient registration  
    - "1.002"  # Triage assessment
    - "1.003"  # Queue assignment
    - "1.004"  # Provider notification

steps:
  - id: "1.002"
    name: "Perform Triage Assessment"
    intent: "Assess patient acuity and determine appropriate care pathway"
    owner: ROLE.TRIAGE_NURSE
    system: SYS.EMR
    
    subprocess_calls:
      - subprocess_id: VITAL_SIGNS_ASSESSMENT
        description: "Standard triage vital signs protocol"
    
    # Clinical validations
    validations:
      - id: VAL.COMPLETE_ASSESSMENT
        description: "All required triage elements completed"
        rule: "vital_signs and pain_scale and chief_complaint completed"
        severity: error
      
      - id: VAL.ACUITY_ASSIGNMENT
        description: "Acuity level assigned based on protocols"
        rule: "acuity_level in [1,2,3,4,5] and justification provided"
        severity: error
    
    # Time-critical SLAs
    sla_ms: 300000  # 5 minutes maximum
    
    # Clinical escalation
    on_error:
      policy: escalate
      escalation_role: ROLE.CHARGE_NURSE
      recovery_step: "9.001"  # Clinical supervisor review
    
    # Patient safety metrics
    metrics:
      - name: "triage_completion_time_ms"
        type: timer
        threshold_critical: 600000  # 10 minutes
      
      - name: "high_acuity_identification_rate"
        type: gauge
        description: "Percentage of ESI 1-2 patients correctly identified"
    
    # HIPAA compliance
    audit:
      events: ["triage.completed", "acuity.assigned", "pathway.selected"]
      required_fields: ["patient_id", "nurse_id", "acuity_score", "timestamp"]
      retention_days: 2555  # 7 years
      compliance_tags: ["HIPAA_audit", "clinical_decision"]
```

**Benefits**:
- **Clinical Safety**: Standardized protocols reduce variation and errors
- **Compliance Ready**: Built-in HIPAA and Joint Commission requirements
- **Performance Monitoring**: Track triage times and accuracy metrics
- **Escalation Procedures**: Automatic clinical supervisor involvement for complex cases

---

## Use Case 3: Manufacturing Quality Control

### Scenario: Pharmaceutical Batch Release Testing

**Enhanced Framework Application**:

```yaml
schema_version: 2.0
process:
  id: PROC.PHARMA.BATCH_RELEASE
  name: "Pharmaceutical Batch Quality Control and Release"
  compliance_frameworks: ["FDA_21CFR211", "ICH_Q7", "EU_GMP"]

# Laboratory testing sub-processes
subprocesses:
  - subprocess_id: HPLC_ASSAY
    name: "High Performance Liquid Chromatography Assay"
    inputs:
      - name: sample_id
        validation_rules: ["valid_batch_format"]
      - name: test_method
        validation_rules: ["validated_method"]
    outputs:
      - name: assay_result
        data_type: number
        validation_rules: ["result >= 95.0 and result <= 105.0"]

flows:
  standard_release:
    - "1.001"  # Sample preparation
    - "1.002"  # Identity testing
    - "1.003"  # Assay testing
    - "1.004"  # Impurity testing
    - "1.005"  # Microbiological testing
    - "2.001"  # Results review
    - "2.002"  # Batch disposition
  
  ooo_investigation:  # Out of Specification
    - "1.003"  # Assay testing (fails)
    - "3.001"  # OOS investigation
    - "3.002"  # Root cause analysis
    - "3.003"  # Corrective action

steps:
  - id: "1.003"
    name: "Perform Assay Testing"
    intent: "Quantitate active pharmaceutical ingredient content"
    owner: ROLE.QC_ANALYST
    system: SYS.LIMS
    
    subprocess_calls:
      - subprocess_id: HPLC_ASSAY
        input_mapping:
          batch_sample: sample_id
          sop_method: test_method
        output_mapping:
          content_result: assay_result
        description: "HPLC assay per validated method"
    
    # FDA validation requirements
    validations:
      - id: VAL.METHOD_VALIDATED
        description: "Test method is currently validated"
        rule: "method_validation_status = 'CURRENT'"
        severity: error
      
      - id: VAL.ANALYST_QUALIFIED
        description: "Analyst is qualified for this test"
        rule: "analyst_id in qualified_analysts_list"
        severity: error
      
      - id: VAL.SPECIFICATION_LIMITS
        description: "Result within specification limits"
        rule: "assay_result >= 95.0 and assay_result <= 105.0"
        severity: error
        remediation: "Initiate out-of-specification investigation"
    
    # Conditional flow for OOS results
    on_success:
      next: "1.004"  # Continue to impurity testing
    
    on_error:
      policy: halt
      recovery_step: "3.001"  # OOS investigation
      escalation_role: ROLE.QC_SUPERVISOR
    
    # 21 CFR Part 11 compliance
    audit:
      events: ["test.started", "test.completed", "result.recorded"]
      required_fields: ["analyst_id", "method_id", "result_value", "electronic_signature"]
      retention_days: 10950  # 30 years for pharmaceutical records
      compliance_tags: ["21CFR11", "GMP_records", "batch_record"]
    
    # Quality metrics
    metrics:
      - name: "assay_test_duration_minutes"
        type: timer
        threshold_warning: 240  # 4 hours
      
      - name: "assay_first_pass_rate"
        type: gauge
        description: "Percentage of assays passing on first attempt"
```

**Benefits**:
- **Regulatory Compliance**: Built-in FDA, ICH, and EU GMP requirements
- **Quality Assurance**: Standardized testing protocols and validations
- **Investigation Workflows**: Automatic OOS investigation procedures
- **Electronic Records**: 21 CFR Part 11 compliant audit trails

---

## Use Case 4: Software Development CI/CD Pipeline

### Scenario: Automated Build, Test, and Deployment

**Enhanced Framework Integration**:

```yaml
schema_version: 2.0
process:
  id: PROC.SOFTWARE.CICD_PIPELINE
  name: "Continuous Integration and Deployment Pipeline"
  compliance_frameworks: ["SOC2", "PCI_DSS", "GDPR"]

# Reusable testing sub-processes
subprocesses:
  - subprocess_id: SECURITY_SCAN
    name: "Comprehensive Security Scanning"
    inputs:
      - name: artifact_location
        validation_rules: ["valid_s3_path"]
    outputs:
      - name: vulnerability_count
        data_type: number
      - name: compliance_score
        data_type: number

# Deployment strategies
flows:
  feature_deployment:
    - "1.001"  # Code checkout
    - "1.002"  # Build artifacts
    - "1.003"  # Unit testing
    - "1.004"  # Integration testing
    - "1.005"  # Security scanning
    - "2.001"  # Deploy to staging
    - "2.002"  # Acceptance testing
    - "3.001"  # Production deployment
  
  hotfix_deployment:
    - "1.001"  # Code checkout
    - "1.002"  # Build artifacts
    - "1.003"  # Unit testing
    - "1.005"  # Security scanning
    - "3.001"  # Direct to production (emergency)

steps:
  - id: "1.005"
    name: "Security and Compliance Scanning"
    intent: "Ensure code meets security and compliance requirements"
    owner: ROLE.SECURITY_ENGINEER
    system: SYS.SECURITY_SCANNER
    
    subprocess_calls:
      - subprocess_id: SECURITY_SCAN
        input_mapping:
          build_artifact: artifact_location
        output_mapping:
          vuln_count: vulnerability_count
          compliance_score: compliance_score
        description: "SAST, DAST, and dependency scanning"
    
    # Security gates
    validations:
      - id: VAL.NO_CRITICAL_VULNS
        description: "No critical vulnerabilities detected"
        rule: "critical_vulnerabilities = 0"
        severity: error
        remediation: "Block deployment until vulnerabilities resolved"
      
      - id: VAL.COMPLIANCE_THRESHOLD
        description: "Compliance score meets minimum threshold"
        rule: "compliance_score >= 85"
        severity: warning
    
    # Security metrics
    metrics:
      - name: "security_scan_duration_ms"
        type: timer
      
      - name: "vulnerabilities_by_severity"
        type: gauge
        labels: ["severity_level", "vulnerability_type"]
    
    # SOC2 audit requirements
    audit:
      events: ["scan.started", "vulnerabilities.detected", "scan.completed"]
      required_fields: ["scan_id", "vulnerability_summary", "compliance_status"]
      compliance_tags: ["SOC2_security", "change_management"]
```

**Benefits**:
- **Security Integration**: Automated security scanning with compliance gates
- **Audit Trails**: Complete deployment history for SOC2/PCI compliance
- **Quality Gates**: Prevent deployment of non-compliant code
- **Process Visibility**: Real-time pipeline status and metrics

---

## Cross-Industry Framework Benefits

### Universal Advantages

1. **Standardization**: Common approach across all industries and use cases
2. **Compliance Ready**: Built-in support for industry-specific regulations
3. **Observability**: Consistent metrics and audit trails regardless of domain
4. **Error Handling**: Standardized retry, escalation, and recovery patterns
5. **Integration**: Easy integration with existing tools and systems

### Industry-Specific Adaptations

| Industry | Key Focus Areas | Compliance Frameworks | Specialized Features |
|----------|----------------|----------------------|---------------------|
| **Financial Services** | Risk management, real-time processing | MiFID2, BASEL3, SOX | Position tracking, limit monitoring |
| **Healthcare** | Patient safety, clinical protocols | HIPAA, Joint Commission | Clinical decision support, escalation |
| **Pharmaceutical** | Quality control, batch integrity | FDA 21CFR211, ICH Q7 | Laboratory workflows, OOS investigations |
| **Software Development** | Code quality, security | SOC2, PCI DSS | Security scanning, deployment gates |
| **Manufacturing** | Process control, safety | ISO 9001, OSHA | Quality gates, safety interlocks |

### Implementation Patterns

**Common Success Factors**:
- Start with most critical processes (high risk/high frequency)
- Use industry templates to accelerate adoption
- Implement observability from day one
- Build compliance requirements into process design
- Train teams on standardized approaches

**Scaling Strategies**:
- Begin with pilot team/department
- Create center of excellence for process engineering
- Develop organization-specific templates
- Implement governance and approval workflows
- Measure and communicate benefits to drive adoption