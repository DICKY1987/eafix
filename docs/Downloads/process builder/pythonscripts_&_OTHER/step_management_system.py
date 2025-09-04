#!/usr/bin/env python3
"""
Advanced Step Management and Sequencing System
Addresses step insertion, renumbering, and reference management challenges
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set, Any
from enum import Enum
import re
import uuid
from decimal import Decimal, ROUND_HALF_UP
import networkx as nx

class StepIDFormat(Enum):
    DECIMAL = "decimal"  # 1.001, 1.002, 1.003
    SEMANTIC = "semantic"  # INIT.001, VALIDATE.001, EXPORT.001
    UUID = "uuid"  # Globally unique identifiers
    HYBRID = "hybrid"  # Combines semantic and numeric: INIT.001

class InsertionStrategy(Enum):
    DECIMAL_GAPS = "decimal_gaps"  # Use decimal places: 1.0015 between 1.001 and 1.002
    RENUMBER_SEQUENCE = "renumber_sequence"  # Renumber all subsequent steps
    SPARSE_NUMBERING = "sparse_numbering"  # Leave gaps: 1.010, 1.020, 1.030
    SEMANTIC_VERSIONING = "semantic_versioning"  # Use alphabetic suffixes: 1.001a, 1.001b

@dataclass
class StepReference:
    """Represents a reference from one step to another"""
    source_step_id: str
    target_step_id: str
    reference_type: str  # "dependency", "goto", "subprocess_call", "error_recovery"
    field_path: str  # e.g., "dependencies[0]", "on_error.recovery_step"
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class StepIDMapping:
    """Mapping between old and new step IDs"""
    old_id: str
    new_id: str
    reason: str
    timestamp: str
    affected_references: List[StepReference] = field(default_factory=list)

@dataclass
class StepInsertionPoint:
    """Defines where and how to insert a new step"""
    target_step_id: str
    position: str  # "before", "after"
    new_step_id: Optional[str] = None
    strategy: InsertionStrategy = InsertionStrategy.DECIMAL_GAPS

class StepSequenceManager:
    """Manages step sequencing, insertion, and reference integrity"""
    
    def __init__(self, id_format: StepIDFormat = StepIDFormat.DECIMAL):
        self.id_format = id_format
        self.reference_graph = nx.DiGraph()
        self.step_registry: Dict[str, Any] = {}
        self.id_mappings: List[StepIDMapping] = []
        
    def register_step(self, step: Any) -> None:
        """Register a step in the sequence manager"""
        self.step_registry[step.step_id] = step
        self._update_reference_graph(step)
    
    def _update_reference_graph(self, step: Any) -> None:
        """Update the reference graph with step relationships"""
        step_id = step.step_id
        
        # Add node for this step
        self.reference_graph.add_node(step_id, step=step)
        
        # Add dependency edges
        for dep in getattr(step, 'dependencies', []):
            self.reference_graph.add_edge(dep, step_id, type='dependency')
        
        # Add GOTO edges
        for goto in getattr(step, 'goto_targets', []):
            self.reference_graph.add_edge(step_id, goto, type='goto')
        
        # Add subprocess call edges
        for call in getattr(step, 'subprocess_calls', []):
            self.reference_graph.add_edge(step_id, call.subprocess_id, type='subprocess')
        
        # Add success/error flow edges
        if hasattr(step, 'on_success') and step.on_success:
            self.reference_graph.add_edge(step_id, step.on_success, type='success_flow')
        
        if hasattr(step, 'on_error') and step.on_error and hasattr(step.on_error, 'recovery_step'):
            if step.on_error.recovery_step:
                self.reference_graph.add_edge(step_id, step.on_error.recovery_step, type='error_recovery')
    
    def find_all_references(self, step_id: str) -> List[StepReference]:
        """Find all references to a specific step"""
        references = []
        
        # Direct references in graph
        for source, target, data in self.reference_graph.edges(data=True):
            if target == step_id:
                references.append(StepReference(
                    source_step_id=source,
                    target_step_id=target,
                    reference_type=data.get('type', 'unknown'),
                    field_path=self._get_field_path(source, target, data.get('type'))
                ))
        
        return references
    
    def _get_field_path(self, source: str, target: str, ref_type: str) -> str:
        """Determine the field path for a reference"""
        field_map = {
            'dependency': 'dependencies',
            'goto': 'goto_targets',
            'subprocess': 'subprocess_calls',
            'success_flow': 'on_success',
            'error_recovery': 'on_error.recovery_step'
        }
        return field_map.get(ref_type, 'unknown')
    
    def generate_step_id(self, section_id: str, sequence_number: int, 
                        context: str = "") -> str:
        """Generate step ID according to configured format"""
        
        if self.id_format == StepIDFormat.DECIMAL:
            base = section_id.split('.')[0] if '.' in section_id else section_id
            return f"{base}.{sequence_number:03d}"
        
        elif self.id_format == StepIDFormat.SEMANTIC:
            if context:
                return f"{context.upper()}.{sequence_number:03d}"
            else:
                return f"STEP.{sequence_number:03d}"
        
        elif self.id_format == StepIDFormat.UUID:
            return str(uuid.uuid4())
        
        elif self.id_format == StepIDFormat.HYBRID:
            base = context.upper() if context else "STEP"
            section_num = section_id.split('.')[0] if '.' in section_id else "1"
            return f"{base}.{section_num}.{sequence_number:03d}"
    
    def insert_step(self, section: Any, insertion_point: StepInsertionPoint, 
                   new_step: Any) -> Tuple[bool, List[str]]:
        """Insert a step at the specified position with automatic management"""
        
        try:
            # Find target step position
            target_index = self._find_step_index(section, insertion_point.target_step_id)
            if target_index is None:
                return False, [f"Target step {insertion_point.target_step_id} not found"]
            
            # Determine insertion index
            if insertion_point.position == "after":
                insert_index = target_index + 1
            else:  # "before"
                insert_index = target_index
            
            # Apply insertion strategy
            if insertion_point.strategy == InsertionStrategy.DECIMAL_GAPS:
                return self._insert_with_decimal_gaps(section, insert_index, new_step)
            
            elif insertion_point.strategy == InsertionStrategy.RENUMBER_SEQUENCE:
                return self._insert_with_renumbering(section, insert_index, new_step)
            
            elif insertion_point.strategy == InsertionStrategy.SPARSE_NUMBERING:
                return self._insert_with_sparse_numbering(section, insert_index, new_step)
            
            elif insertion_point.strategy == InsertionStrategy.SEMANTIC_VERSIONING:
                return self._insert_with_semantic_versioning(section, insert_index, new_step)
            
            else:
                return False, [f"Unknown insertion strategy: {insertion_point.strategy}"]
                
        except Exception as e:
            return False, [f"Insertion failed: {str(e)}"]
    
    def _find_step_index(self, section: Any, step_id: str) -> Optional[int]:
        """Find the index of a step in the section"""
        for i, step in enumerate(section.steps):
            if step.step_id == step_id:
                return i
        return None
    
    def _insert_with_decimal_gaps(self, section: Any, insert_index: int, 
                                 new_step: Any) -> Tuple[bool, List[str]]:
        """Insert step using decimal gap strategy (1.0015 between 1.001 and 1.002)"""
        
        # Get neighboring step IDs
        prev_step_id = section.steps[insert_index - 1].step_id if insert_index > 0 else None
        next_step_id = section.steps[insert_index].step_id if insert_index < len(section.steps) else None
        
        # Generate decimal gap ID
        if prev_step_id and next_step_id:
            new_id = self._generate_decimal_gap_id(prev_step_id, next_step_id)
        elif prev_step_id:
            new_id = self._increment_step_id(prev_step_id, 0.001)
        elif next_step_id:
            new_id = self._decrement_step_id(next_step_id, 0.001)
        else:
            # First step in section
            section_base = self._extract_section_base(section.section_id)
            new_id = f"{section_base}.001"
        
        new_step.step_id = new_id
        section.steps.insert(insert_index, new_step)
        self.register_step(new_step)
        
        return True, [f"Inserted step {new_id} using decimal gap"]
    
    def _generate_decimal_gap_id(self, prev_id: str, next_id: str) -> str:
        """Generate ID between two existing IDs using decimal places"""
        
        # Parse step IDs (e.g., "1.001" and "1.002")
        prev_match = re.match(r'(\d+)\.(\d+)', prev_id)
        next_match = re.match(r'(\d+)\.(\d+)', next_id)
        
        if not prev_match or not next_match:
            raise ValueError(f"Cannot parse step IDs: {prev_id}, {next_id}")
        
        section_num = prev_match.group(1)
        prev_seq = Decimal(prev_match.group(2))
        next_seq = Decimal(next_match.group(2))
        
        # Find midpoint
        gap = (next_seq - prev_seq) / 2
        new_seq = prev_seq + gap
        
        # Format with appropriate precision
        if gap >= 1:
            # Room for integer
            new_seq_str = f"{int(new_seq):03d}"
        else:
            # Need decimal places
            new_seq_str = f"{float(new_seq):07.3f}".replace('.', '')[:6]
        
        return f"{section_num}.{new_seq_str}"
    
    def _insert_with_renumbering(self, section: Any, insert_index: int, 
                                new_step: Any) -> Tuple[bool, List[str]]:
        """Insert step and renumber all subsequent steps"""
        
        # Generate new step ID
        section_base = self._extract_section_base(section.section_id)
        new_sequence = insert_index + 1
        new_step_id = f"{section_base}.{new_sequence:03d}"
        new_step.step_id = new_step_id
        
        # Create ID mappings for renumbering
        mappings = []
        
        # Renumber subsequent steps
        for i in range(insert_index, len(section.steps)):
            old_step = section.steps[i]
            old_id = old_step.step_id
            new_id = f"{section_base}.{i + 2:03d}"  # +2 because we're inserting
            
            mappings.append(StepIDMapping(
                old_id=old_id,
                new_id=new_id,
                reason="renumbering_for_insertion",
                timestamp=str(datetime.now()),
                affected_references=self.find_all_references(old_id)
            ))
            
            old_step.step_id = new_id
        
        # Insert new step
        section.steps.insert(insert_index, new_step)
        
        # Update all references
        warnings = self._update_all_references(mappings)
        
        # Register steps
        self.register_step(new_step)
        for step in section.steps[insert_index + 1:]:
            self.register_step(step)
        
        self.id_mappings.extend(mappings)
        
        return True, [f"Inserted step {new_step_id} with renumbering"] + warnings
    
    def _insert_with_sparse_numbering(self, section: Any, insert_index: int, 
                                     new_step: Any) -> Tuple[bool, List[str]]:
        """Insert step using sparse numbering (gaps of 10: 1.010, 1.020, 1.030)"""
        
        section_base = self._extract_section_base(section.section_id)
        
        # Check if we need to convert to sparse numbering first
        if not self._is_sparse_numbered(section):
            warnings = self._convert_to_sparse_numbering(section)
        else:
            warnings = []
        
        # Find appropriate sparse number
        if insert_index == 0:
            # Insert at beginning
            new_seq = 5  # Between 0 and 10
        elif insert_index >= len(section.steps):
            # Insert at end
            last_step = section.steps[-1]
            last_seq = int(last_step.step_id.split('.')[1])
            new_seq = last_seq + 10
        else:
            # Insert between steps
            prev_step = section.steps[insert_index - 1]
            next_step = section.steps[insert_index]
            prev_seq = int(prev_step.step_id.split('.')[1])
            next_seq = int(next_step.step_id.split('.')[1])
            
            if next_seq - prev_seq > 1:
                new_seq = prev_seq + ((next_seq - prev_seq) // 2)
            else:
                # Need to renumber to create space
                return self._insert_with_renumbering(section, insert_index, new_step)
        
        new_step.step_id = f"{section_base}.{new_seq:03d}"
        section.steps.insert(insert_index, new_step)
        self.register_step(new_step)
        
        return True, [f"Inserted step {new_step.step_id} using sparse numbering"] + warnings
    
    def _is_sparse_numbered(self, section: Any) -> bool:
        """Check if section uses sparse numbering"""
        if len(section.steps) < 2:
            return True
        
        # Check for gaps between consecutive steps
        for i in range(len(section.steps) - 1):
            curr_seq = int(section.steps[i].step_id.split('.')[1])
            next_seq = int(section.steps[i + 1].step_id.split('.')[1])
            if next_seq - curr_seq < 5:  # Less than 5 gap = not sparse
                return False
        
        return True
    
    def _convert_to_sparse_numbering(self, section: Any) -> List[str]:
        """Convert section to sparse numbering"""
        section_base = self._extract_section_base(section.section_id)
        mappings = []
        
        for i, step in enumerate(section.steps):
            old_id = step.step_id
            new_id = f"{section_base}.{(i + 1) * 10:03d}"
            
            if old_id != new_id:
                mappings.append(StepIDMapping(
                    old_id=old_id,
                    new_id=new_id,
                    reason="converting_to_sparse_numbering",
                    timestamp=str(datetime.now()),
                    affected_references=self.find_all_references(old_id)
                ))
                
                step.step_id = new_id
        
        # Update references
        warnings = self._update_all_references(mappings)
        self.id_mappings.extend(mappings)
        
        return [f"Converted to sparse numbering"] + warnings
    
    def _extract_section_base(self, section_id: str) -> str:
        """Extract base number from section ID (e.g., '1.000' -> '1')"""
        return section_id.split('.')[0]
    
    def _update_all_references(self, mappings: List[StepIDMapping]) -> List[str]:
        """Update all references based on ID mappings"""
        warnings = []
        mapping_dict = {m.old_id: m.new_id for m in mappings}
        
        for step in self.step_registry.values():
            # Update dependencies
            step.dependencies = [mapping_dict.get(dep, dep) for dep in step.dependencies]
            
            # Update GOTO targets
            step.goto_targets = [mapping_dict.get(target, target) for target in step.goto_targets]
            
            # Update success flow
            if hasattr(step, 'on_success') and step.on_success in mapping_dict:
                step.on_success = mapping_dict[step.on_success]
            
            # Update error recovery
            if (hasattr(step, 'on_error') and step.on_error and 
                hasattr(step.on_error, 'recovery_step') and 
                step.on_error.recovery_step in mapping_dict):
                step.on_error.recovery_step = mapping_dict[step.on_error.recovery_step]
        
        # Check for broken references
        for mapping in mappings:
            for ref in mapping.affected_references:
                if ref.target_step_id not in self.step_registry:
                    warnings.append(f"Reference to {ref.target_step_id} may be broken after renumbering")
        
        return warnings
    
    def delete_step(self, section: Any, step_id: str) -> Tuple[bool, List[str]]:
        """Delete a step and handle reference cleanup"""
        
        # Find step
        step_index = self._find_step_index(section, step_id)
        if step_index is None:
            return False, [f"Step {step_id} not found"]
        
        # Find all references to this step
        references = self.find_all_references(step_id)
        
        if references:
            warnings = [f"Step {step_id} is referenced by:"]
            for ref in references:
                warnings.append(f"  - {ref.source_step_id} ({ref.reference_type})")
            warnings.append("Consider updating references before deletion")
        else:
            warnings = []
        
        # Remove step
        deleted_step = section.steps.pop(step_index)
        
        # Remove from registry
        if step_id in self.step_registry:
            del self.step_registry[step_id]
        
        # Remove from reference graph
        if self.reference_graph.has_node(step_id):
            self.reference_graph.remove_node(step_id)
        
        return True, [f"Deleted step {step_id}"] + warnings
    
    def validate_flow_integrity(self, section: Any) -> List[str]:
        """Validate that all flow references are valid"""
        errors = []
        all_step_ids = {step.step_id for step in section.steps}
        
        for step in section.steps:
            # Check dependencies
            for dep in step.dependencies:
                if dep not in all_step_ids:
                    errors.append(f"Step {step.step_id} depends on non-existent step {dep}")
            
            # Check GOTO targets
            for target in step.goto_targets:
                if target not in all_step_ids and not target.startswith(('END_', 'EXIT_', 'REJECT_')):
                    errors.append(f"Step {step.step_id} has GOTO to non-existent step {target}")
            
            # Check success flow
            if hasattr(step, 'on_success') and step.on_success:
                if step.on_success not in all_step_ids:
                    errors.append(f"Step {step.step_id} has invalid success target {step.on_success}")
            
            # Check error recovery
            if (hasattr(step, 'on_error') and step.on_error and 
                hasattr(step.on_error, 'recovery_step') and step.on_error.recovery_step):
                if step.on_error.recovery_step not in all_step_ids:
                    errors.append(f"Step {step.step_id} has invalid error recovery target {step.on_error.recovery_step}")
        
        return errors
    
    def optimize_step_numbering(self, section: Any) -> Tuple[bool, List[str]]:
        """Optimize step numbering for better maintainability"""
        
        # Analyze current numbering pattern
        if self._has_decimal_gaps(section):
            # Convert decimal gaps to clean sequence
            return self._clean_decimal_gaps(section)
        
        elif not self._is_sparse_numbered(section):
            # Convert to sparse numbering for future insertions
            warnings = self._convert_to_sparse_numbering(section)
            return True, [f"Converted to sparse numbering for better maintainability"] + warnings
        
        else:
            return True, ["Step numbering is already optimized"]
    
    def _has_decimal_gaps(self, section: Any) -> bool:
        """Check if section has decimal gap IDs (like 1.0015)"""
        for step in section.steps:
            if '.' in step.step_id:
                numeric_part = step.step_id.split('.', 1)[1]
                if len(numeric_part) > 3:  # More than standard 3-digit format
                    return True
        return False
    
    def _clean_decimal_gaps(self, section: Any) -> Tuple[bool, List[str]]:
        """Clean up decimal gap IDs to standard sequence"""
        section_base = self._extract_section_base(section.section_id)
        mappings = []
        
        # Sort steps by current ID to maintain order
        section.steps.sort(key=lambda s: float(s.step_id.split('.', 1)[1]))
        
        # Renumber with clean sequence
        for i, step in enumerate(section.steps):
            old_id = step.step_id
            new_id = f"{section_base}.{i + 1:03d}"
            
            if old_id != new_id:
                mappings.append(StepIDMapping(
                    old_id=old_id,
                    new_id=new_id,
                    reason="cleaning_decimal_gaps",
                    timestamp=str(datetime.now()),
                    affected_references=self.find_all_references(old_id)
                ))
                
                step.step_id = new_id
        
        # Update references
        warnings = self._update_all_references(mappings)
        self.id_mappings.extend(mappings)
        
        return True, [f"Cleaned decimal gaps in section {section.section_id}"] + warnings

# Example usage and testing
def main():
    """Demo the step management system"""
    from datetime import datetime
    
    # Mock step class for testing
    @dataclass
    class MockStep:
        step_id: str
        description: str
        dependencies: List[str] = field(default_factory=list)
        goto_targets: List[str] = field(default_factory=list)
        on_success: Optional[str] = None
    
    @dataclass 
    class MockSection:
        section_id: str
        steps: List[MockStep] = field(default_factory=list)
    
    # Create test section
    section = MockSection(section_id="1.000")
    section.steps = [
        MockStep("1.001", "First step", on_success="1.002"),
        MockStep("1.002", "Second step", dependencies=["1.001"], on_success="1.003"),
        MockStep("1.003", "Third step", dependencies=["1.002"])
    ]
    
    # Create step manager
    manager = StepSequenceManager(StepIDFormat.DECIMAL)
    
    # Register existing steps
    for step in section.steps:
        manager.register_step(step)
    
    print("=== Original Steps ===")
    for step in section.steps:
        print(f"{step.step_id}: {step.description}")
    
    # Test insertion
    new_step = MockStep("", "New validation step")
    insertion_point = StepInsertionPoint(
        target_step_id="1.002",
        position="before",
        strategy=InsertionStrategy.DECIMAL_GAPS
    )
    
    success, messages = manager.insert_step(section, insertion_point, new_step)
    
    print(f"\n=== After Insertion ===")
    print(f"Success: {success}")
    for msg in messages:
        print(f"  {msg}")
    
    print("\nUpdated steps:")
    for step in section.steps:
        print(f"{step.step_id}: {step.description}")
    
    # Test validation
    print(f"\n=== Flow Validation ===")
    errors = manager.validate_flow_integrity(section)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
    else:
        print("Flow integrity validated successfully")
    
    # Test optimization
    print(f"\n=== Optimization ===")
    success, messages = manager.optimize_step_numbering(section)
    for msg in messages:
        print(f"  {msg}")

if __name__ == "__main__":
    main()