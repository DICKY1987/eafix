#!/usr/bin/env python3
"""
Migration Strategy and Backward Compatibility Framework
Handles migration from basic to enhanced process framework
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Union
from enum import Enum
import yaml
import json
from datetime import datetime
import re
import logging

class MigrationLevel(Enum):
    BASIC_COMPATIBLE = "basic_compatible"  # Just load existing format
    ENHANCED_MINIMAL = "enhanced_minimal"  # Add registries, minimal enhancements
    ENHANCED_FULL = "enhanced_full"       # Full enterprise features
    ENTERPRISE_READY = "enterprise_ready" # Complete enterprise transformation

class MigrationPhase(Enum):
    ASSESSMENT = "assessment"
    BACKUP = "backup"
    SCHEMA_UPGRADE = "schema_upgrade"
    REGISTRY_EXTRACTION = "registry_extraction"
    STEP_ENHANCEMENT = "step_enhancement"
    VALIDATION = "validation"
    FINALIZATION = "finalization"

@dataclass
class MigrationResult:
    """Result of a migration operation"""
    success: bool
    level_achieved: MigrationLevel
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    backup_path: Optional[str] = None

@dataclass
class MigrationContext:
    """Context maintained during migration"""
    source_file: str
    target_level: MigrationLevel
    current_phase: MigrationPhase = MigrationPhase.ASSESSMENT
    
    # Original content
    original_content: str = ""
    original_format: str = "yaml"  # yaml or json
    
    # Extracted elements
    detected_actors: List[str] = field(default_factory=list)
    detected_systems: List[str] = field(default_factory=list)
    detected_artifacts: List[str] = field(default_factory=list)
    
    # Migration log
    log_entries: List[str] = field(default_factory=list)
    
    # Schema version tracking
    source_schema_version: str = "1.0"
    target_schema_version: str = "2.0"

class LegacyProcessLoader:
    """Loads and normalizes legacy process formats"""
    
    def load_legacy_format(self, content: str, format_type: str = "yaml") -> Dict[str, Any]:
        """Load legacy format and normalize to consistent structure"""
        
        if format_type.lower() == "yaml":
            data = yaml.safe_load(content)
        elif format_type.lower() == "json":
            data = json.loads(content)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
        
        # Normalize legacy structure
        return self._normalize_legacy_structure(data)
    
    def _normalize_legacy_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize various legacy formats to consistent structure"""
        
        # Handle different legacy schemas
        if "process" in data:
            # Already has some structure
            return data
        
        # Legacy format with direct fields
        normalized = {
            "schema_version": "1.0",
            "process": {
                "title": data.get("title", "Untitled Process"),
                "version": data.get("version", "1.0"),
                "date": data.get("date", datetime.now().strftime("%Y-%m-%d")),
                "description": data.get("legend", "")
            },
            "sections": data.get("sections", []),
            "subprocesses": data.get("subprocesses", []),
            "file_paths": data.get("file_paths", {}),
            "metadata": data.get("metadata", {})
        }
        
        return normalized

class RegistryExtractor:
    """Extracts canonical registries from existing process definitions"""
    
    def extract_registries(self, process_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """Extract roles, systems, and artifacts from process definition"""
        
        registries = {
            "roles": [],
            "systems": [],
            "artifacts": [],
            "data_models": []
        }
        
        # Extract from sections and steps
        actors_found = set()
        systems_found = set()
        artifacts_found = set()
        
        for section in process_data.get("sections", []):
            # Extract actors from section
            for actor in section.get("actors", []):
                actors_found.add(actor)
            
            # Extract from steps
            for step in section.get("steps", []):
                if "actor" in step:
                    actors_found.add(step["actor"])
                
                # Extract systems from file operations
                for file_op in step.get("file_operations", []):
                    if ":" in file_op:
                        operation, target = file_op.split(":", 1)
                        systems_found.add(self._infer_system_from_operation(operation, target))
                
                # Extract artifacts from file operations
                for file_op in step.get("file_operations", []):
                    artifact = self._extract_artifact_from_operation(file_op)
                    if artifact:
                        artifacts_found.add(artifact)
        
        # Convert to registry format
        registries["roles"] = [
            {
                "id": self._normalize_role_id(actor),
                "name": actor,
                "description": f"Role responsible for {actor.lower()} operations"
            }
            for actor in sorted(actors_found)
        ]
        
        registries["systems"] = [
            {
                "id": self._normalize_system_id(system),
                "name": system,
                "description": f"System handling {system.lower()} operations",
                "type": "service"
            }
            for system in sorted(systems_found)
        ]
        
        registries["artifacts"] = [
            {
                "id": self._normalize_artifact_id(artifact),
                "name": artifact,
                "description": f"Data artifact: {artifact}",
                "format": self._infer_format_from_name(artifact)
            }
            for artifact in sorted(artifacts_found)
        ]
        
        return registries
    
    def _normalize_role_id(self, actor: str) -> str:
        """Normalize actor name to role ID"""
        return f"ROLE.{actor.upper().replace(' ', '_')}"
    
    def _normalize_system_id(self, system: str) -> str:
        """Normalize system name to system ID"""
        return f"SYS.{system.upper().replace(' ', '_')}"
    
    def _normalize_artifact_id(self, artifact: str) -> str:
        """Normalize artifact name to artifact ID"""
        return f"ART.{artifact.upper().replace(' ', '_').replace('.', '_')}"
    
    def _infer_system_from_operation(self, operation: str, target: str) -> str:
        """Infer system from file operation"""
        if "READ" in operation or "WRITE" in operation:
            return "FILESYSTEM"
        elif "API" in operation or "HTTP" in operation:
            return "API_GATEWAY"
        elif "DATABASE" in operation or "DB" in operation:
            return "DATABASE"
        else:
            return "UNKNOWN_SYSTEM"
    
    def _extract_artifact_from_operation(self, file_op: str) -> Optional[str]:
        """Extract artifact name from file operation"""
        if ":" in file_op:
            _, target = file_op.split(":", 1)
            # Extract filename or path
            if "/" in target or "\\" in target:
                return target.split("/")[-1].split("\\")[-1]
            return target
        return None
    
    def _infer_format_from_name(self, name: str) -> str:
        """Infer file format from name"""
        if "." in name:
            ext = name.split(".")[-1].lower()
            return ext
        return "unknown"

class ProcessMigrator:
    """Main migration orchestrator"""
    
    def __init__(self):
        self.legacy_loader = LegacyProcessLoader()
        self.registry_extractor = RegistryExtractor()
        self.logger = logging.getLogger(__name__)
    
    def migrate_process(self, source_file: str, target_level: MigrationLevel,
                       backup: bool = True) -> MigrationResult:
        """Migrate a process file to enhanced format"""
        
        context = MigrationContext(
            source_file=source_file,
            target_level=target_level
        )
        
        try:
            # Phase 1: Assessment
            context.current_phase = MigrationPhase.ASSESSMENT
            self._assess_source_file(context)
            
            # Phase 2: Backup
            if backup:
                context.current_phase = MigrationPhase.BACKUP
                backup_path = self._create_backup(context)
            else:
                backup_path = None
            
            # Phase 3: Schema Upgrade
            context.current_phase = MigrationPhase.SCHEMA_UPGRADE
            upgraded_data = self._upgrade_schema(context)
            
            # Phase 4: Registry Extraction
            if target_level in [MigrationLevel.ENHANCED_MINIMAL, MigrationLevel.ENHANCED_FULL, 
                              MigrationLevel.ENTERPRISE_READY]:
                context.current_phase = MigrationPhase.REGISTRY_EXTRACTION
                registries = self._extract_registries(context, upgraded_data)
                upgraded_data.update(registries)
            
            # Phase 5: Step Enhancement
            if target_level in [MigrationLevel.ENHANCED_FULL, MigrationLevel.ENTERPRISE_READY]:
                context.current_phase = MigrationPhase.STEP_ENHANCEMENT
                self._enhance_steps(context, upgraded_data)
            
            # Phase 6: Enterprise Features
            if target_level == MigrationLevel.ENTERPRISE_READY:
                self._add_enterprise_features(context, upgraded_data)
            
            # Phase 7: Validation
            context.current_phase = MigrationPhase.VALIDATION
            validation_errors = self._validate_migrated_process(upgraded_data)
            
            # Phase 8: Finalization
            context.current_phase = MigrationPhase.FINALIZATION
            self._save_migrated_process(context, upgraded_data)
            
            return MigrationResult(
                success=True,
                level_achieved=target_level,
                warnings=context.log_entries,
                errors=validation_errors,
                backup_path=backup_path,
                metrics={
                    "steps_migrated": self._count_steps(upgraded_data),
                    "registries_extracted": len(registries) if 'registries' in locals() else 0,
                    "enhancements_applied": len([e for e in context.log_entries if "enhanced" in e.lower()])
                }
            )
            
        except Exception as e:
            return MigrationResult(
                success=False,
                level_achieved=MigrationLevel.BASIC_COMPATIBLE,
                errors=[f"Migration failed: {str(e)}"],
                backup_path=backup_path if 'backup_path' in locals() else None
            )
    
    def _assess_source_file(self, context: MigrationContext) -> None:
        """Assess the source file and determine migration strategy"""
        
        with open(context.source_file, 'r', encoding='utf-8') as f:
            context.original_content = f.read()
        
        # Detect format
        try:
            yaml.safe_load(context.original_content)
            context.original_format = "yaml"
        except:
            try:
                json.loads(context.original_content)
                context.original_format = "json"
            except:
                raise ValueError("Source file is neither valid YAML nor JSON")
        
        # Detect schema version
        data = self.legacy_loader.load_legacy_format(context.original_content, context.original_format)
        context.source_schema_version = data.get("schema_version", "1.0")
        
        context.log_entries.append(f"Detected format: {context.original_format}")
        context.log_entries.append(f"Source schema version: {context.source_schema_version}")
    
    def _create_backup(self, context: MigrationContext) -> str:
        """Create backup of original file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{context.source_file}.backup_{timestamp}"
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(context.original_content)
        
        context.log_entries.append(f"Created backup: {backup_path}")
        return backup_path
    
    def _upgrade_schema(self, context: MigrationContext) -> Dict[str, Any]:
        """Upgrade the schema to target version"""
        
        data = self.legacy_loader.load_legacy_format(context.original_content, context.original_format)
        
        # Add schema version
        data["schema_version"] = context.target_schema_version
        
        # Ensure process metadata exists
        if "process" not in data:
            data["process"] = {}
        
        process = data["process"]
        
        # Add missing required fields
        if "id" not in process:
            # Generate process ID from title
            title = process.get("title", "unknown_process")
            process["id"] = f"PROC.{self._slugify(title).upper()}"
        
        if "domain" not in process:
            process["domain"] = "general"
        
        if "owner" not in process:
            process["owner"] = "ROLE.PROCESS_OWNER"
        
        if "tags" not in process:
            process["tags"] = ["migrated"]
        
        # Add timestamps
        now = datetime.now().isoformat()
        process["migrated_at"] = now
        process["migrated_by"] = "migration_tool"
        
        context.log_entries.append(f"Upgraded schema from {context.source_schema_version} to {context.target_schema_version}")
        
        return data
    
    def _extract_registries(self, context: MigrationContext, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and add canonical registries"""
        
        registries = self.registry_extractor.extract_registries(data)
        
        context.log_entries.append(f"Extracted {len(registries['roles'])} roles")
        context.log_entries.append(f"Extracted {len(registries['systems'])} systems")
        context.log_entries.append(f"Extracted {len(registries['artifacts'])} artifacts")
        
        return registries
    
    def _enhance_steps(self, context: MigrationContext, data: Dict[str, Any]) -> None:
        """Enhance steps with additional enterprise fields"""
        
        enhanced_count = 0
        
        for section in data.get("sections", []):
            for step in section.get("steps", []):
                # Add intent field
                if "intent" not in step:
                    step["intent"] = self._generate_intent_from_description(step.get("description", ""))
                
                # Add owner from actor
                if "owner" not in step and "actor" in step:
                    step["owner"] = f"ROLE.{step['actor'].upper()}"
                
                # Add system inference
                if "system" not in step:
                    step["system"] = self._infer_system_from_step(step)
                
                # Enhance error handling
                if "on_error" not in step and step.get("goto_targets"):
                    # Convert simple GOTO to structured error handling
                    step["on_error"] = {
                        "policy": "halt",
                        "recovery_step": step["goto_targets"][0] if step["goto_targets"] else None
                    }
                
                # Add basic SLA if missing
                if "sla_ms" not in step:
                    step["sla_ms"] = self._estimate_sla_from_description(step.get("description", ""))
                
                enhanced_count += 1
        
        context.log_entries.append(f"Enhanced {enhanced_count} steps with enterprise fields")
    
    def _add_enterprise_features(self, context: MigrationContext, data: Dict[str, Any]) -> None:
        """Add full enterprise features"""
        
        # Add global validations
        if "validations" not in data:
            data["validations"] = [
                {
                    "id": "VAL.GLOBAL_SLA_COMPLIANCE",
                    "description": "All steps must have defined SLAs",
                    "rule": "all steps have sla_ms field",
                    "severity": "warning",
                    "scope": "global"
                }
            ]
        
        # Add named flows
        if "flows" not in data:
            data["flows"] = {
                "happy_path": self._extract_happy_path(data),
                "error_recovery": self._extract_error_paths(data)
            }
        
        # Add exit checks
        if "exit_checks" not in data:
            data["exit_checks"] = [
                {
                    "id": "EXIT.PROCESS_COMPLETION",
                    "description": "Process completed successfully",
                    "rule": "final_step_completed = true",
                    "severity": "error"
                }
            ]
        
        # Add compliance metadata
        process = data.get("process", {})
        if "compliance" not in process:
            process["compliance"] = {
                "data_classification": "internal",
                "retention_requirements": {
                    "process_data": "1 year",
                    "audit_logs": "7 years"
                }
            }
        
        context.log_entries.append("Added enterprise compliance and governance features")
    
    def _extract_happy_path(self, data: Dict[str, Any]) -> List[str]:
        """Extract the main happy path flow"""
        steps = []
        for section in data.get("sections", []):
            for step in section.get("steps", []):
                # Only include steps without error conditions
                if not step.get("conditions") or not any("fail" in c.lower() or "error" in c.lower() 
                                                        for c in step.get("conditions", [])):
                    steps.append(step["step_id"])
        return sorted(steps)
    
    def _extract_error_paths(self, data: Dict[str, Any]) -> List[str]:
        """Extract error handling paths"""
        error_steps = []
        for section in data.get("sections", []):
            for step in section.get("steps", []):
                if step.get("goto_targets") or step.get("error_codes"):
                    error_steps.append(step["step_id"])
        return error_steps
    
    def _generate_intent_from_description(self, description: str) -> str:
        """Generate intent statement from step description"""
        # Simple heuristic to create intent from description
        if not description:
            return "Perform operation"
        
        # Extract key action words
        action_words = re.findall(r'\b(?:validate|check|verify|send|read|write|load|save|process|execute|run|perform|generate|calculate|transform|filter|sort|merge|split)\b', description, re.IGNORECASE)
        
        if action_words:
            primary_action = action_words[0].capitalize()
            return f"{primary_action} to ensure proper {self._extract_purpose(description)}"
        else:
            return f"Execute step to {description.lower()}"
    
    def _extract_purpose(self, description: str) -> str:
        """Extract purpose from description"""
        # Look for purpose indicators
        purpose_patterns = [
            r"(?:so that|in order to|to ensure)\s+(.+?)(?:\.|$)",
            r"(?:for|because)\s+(.+?)(?:\.|$)"
        ]
        
        for pattern in purpose_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "operation completion"
    
    def _infer_system_from_step(self, step: Dict[str, Any]) -> str:
        """Infer system from step properties"""
        actor = step.get("actor", "").upper()
        
        if actor in ["PY", "PYTHON"]:
            return "SYS.PYTHON_SERVICE"
        elif actor in ["EA", "MT4"]:
            return "SYS.MT4_EA"
        elif actor in ["FS", "FILESYSTEM"]:
            return "SYS.FILESYSTEM"
        elif actor in ["DB", "DATABASE"]:
            return "SYS.DATABASE"
        else:
            return f"SYS.{actor}_SYSTEM"
    
    def _estimate_sla_from_description(self, description: str) -> int:
        """Estimate SLA from step description"""
        description_lower = description.lower()
        
        # Look for existing time indicators
        time_patterns = [
            (r'(\d+)\s*(?:milli)?seconds?', 1),
            (r'(\d+)\s*minutes?', 60000),
            (r'(\d+)\s*hours?', 3600000)
        ]
        
        for pattern, multiplier in time_patterns:
            match = re.search(pattern, description_lower)
            if match:
                return int(match.group(1)) * multiplier
        
        # Default SLA based on operation type
        if any(word in description_lower for word in ["validate", "check", "verify"]):
            return 1000  # 1 second for validation
        elif any(word in description_lower for word in ["read", "load"]):
            return 2000  # 2 seconds for reading
        elif any(word in description_lower for word in ["write", "save", "store"]):
            return 5000  # 5 seconds for writing
        elif any(word in description_lower for word in ["process", "transform", "calculate"]):
            return 10000  # 10 seconds for processing
        else:
            return 3000  # 3 seconds default
    
    def _validate_migrated_process(self, data: Dict[str, Any]) -> List[str]:
        """Validate the migrated process"""
        errors = []
        
        # Check required fields
        required_fields = ["schema_version", "process", "sections"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate process metadata
        process = data.get("process", {})
        if not process.get("id"):
            errors.append("Process must have an ID")
        if not process.get("title"):
            errors.append("Process must have a title")
        
        # Validate sections
        for i, section in enumerate(data.get("sections", [])):
            if not section.get("section_id"):
                errors.append(f"Section {i} missing section_id")
            if not section.get("steps"):
                errors.append(f"Section {section.get('section_id', i)} has no steps")
        
        return errors
    
    def _save_migrated_process(self, context: MigrationContext, data: Dict[str, Any]) -> None:
        """Save the migrated process"""
        
        # Generate output filename
        if context.target_level == MigrationLevel.BASIC_COMPATIBLE:
            output_file = context.source_file
        else:
            base_name = context.source_file.rsplit('.', 1)[0]
            output_file = f"{base_name}_migrated.yaml"
        
        # Save as YAML (standard format)
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        context.log_entries.append(f"Saved migrated process to: {output_file}")
    
    def _count_steps(self, data: Dict[str, Any]) -> int:
        """Count total steps in process"""
        count = 0
        for section in data.get("sections", []):
            count += len(section.get("steps", []))
        return count
    
    def _slugify(self, text: str) -> str:
        """Convert text to slug format"""
        return re.sub(r'[^a-zA-Z0-9_]', '_', text).strip('_')

# CLI interface for migration
def main():
    """CLI interface for process migration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate process files to enhanced format")
    parser.add_argument("source_file", help="Source process file to migrate")
    parser.add_argument("--level", choices=["basic", "minimal", "full", "enterprise"], 
                       default="minimal", help="Migration level")
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be migrated")
    
    args = parser.parse_args()
    
    # Map CLI level to enum
    level_map = {
        "basic": MigrationLevel.BASIC_COMPATIBLE,
        "minimal": MigrationLevel.ENHANCED_MINIMAL,
        "full": MigrationLevel.ENHANCED_FULL,
        "enterprise": MigrationLevel.ENTERPRISE_READY
    }
    
    migrator = ProcessMigrator()
    
    if args.dry_run:
        print(f"Would migrate {args.source_file} to {args.level} level")
        return
    
    result = migrator.migrate_process(
        source_file=args.source_file,
        target_level=level_map[args.level],
        backup=not args.no_backup
    )
    
    if result.success:
        print(f"✅ Migration successful!")
        print(f"   Level achieved: {result.level_achieved.value}")
        print(f"   Steps migrated: {result.metrics.get('steps_migrated', 0)}")
        if result.backup_path:
            print(f"   Backup created: {result.backup_path}")
        
        if result.warnings:
            print(f"\n⚠️ Warnings:")
            for warning in result.warnings[:5]:  # Show first 5
                print(f"   • {warning}")
    else:
        print(f"❌ Migration failed!")
        for error in result.errors:
            print(f"   • {error}")

if __name__ == "__main__":
    main()