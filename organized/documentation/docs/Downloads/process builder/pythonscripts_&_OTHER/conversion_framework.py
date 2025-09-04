#!/usr/bin/env python3
"""
Standardized Prose-to-Atomic Conversion Framework
Systematic approach for converting natural language process descriptions into atomic YAML
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
import re
import spacy
from abc import ABC, abstractmethod

class ConversionPhase(Enum):
    SCOPE_DEFINITION = "scope_definition"
    ACTOR_EXTRACTION = "actor_extraction"
    ARTIFACT_COLLECTION = "artifact_collection"
    TRIGGER_IDENTIFICATION = "trigger_identification"
    ATOMIC_DECOMPOSITION = "atomic_decomposition"
    FLOW_ORDERING = "flow_ordering"
    OWNERSHIP_ASSIGNMENT = "ownership_assignment"
    CONDITION_DEFINITION = "condition_definition"
    VALIDATION_SPECIFICATION = "validation_specification"
    FAILURE_MAPPING = "failure_mapping"
    INSTRUMENTATION = "instrumentation"
    ID_ASSIGNMENT = "id_assignment"
    EXAMPLE_CREATION = "example_creation"
    CONSISTENCY_VALIDATION = "consistency_validation"

@dataclass
class ConversionContext:
    """Context maintained throughout conversion process"""
    source_prose: str
    domain: str = ""
    existing_registries: Dict[str, List[Any]] = field(default_factory=dict)
    conversion_log: List[str] = field(default_factory=list)
    current_phase: ConversionPhase = ConversionPhase.SCOPE_DEFINITION
    
    # Extracted elements
    actors: Dict[str, str] = field(default_factory=dict)
    systems: Dict[str, str] = field(default_factory=dict)
    artifacts: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    triggers: List[Dict[str, Any]] = field(default_factory=list)
    atomic_actions: List[Dict[str, Any]] = field(default_factory=list)
    validations: List[Dict[str, Any]] = field(default_factory=list)
    error_scenarios: List[Dict[str, Any]] = field(default_factory=list)

class ConversionRule:
    """Rule for prose-to-atomic conversion"""
    def __init__(self, pattern: str, action: str, examples: List[str] = None):
        self.pattern = re.compile(pattern, re.IGNORECASE)
        self.action = action
        self.examples = examples or []
    
    def matches(self, text: str) -> Optional[re.Match]:
        return self.pattern.search(text)

class ConversionRuleSet:
    """Standard conversion rules for different linguistic patterns"""
    
    # Trigger identification rules
    TRIGGER_RULES = [
        ConversionRule(
            r"when\s+(.+?)\s+(?:happens?|occurs?)",
            "trigger_event",
            ["When a new file arrives", "When the timer expires"]
        ),
        ConversionRule(
            r"(?:every|each)\s+(\d+)\s*(minute|hour|day|week)s?",
            "trigger_timer",
            ["Every 5 minutes", "Each hour"]
        ),
        ConversionRule(
            r"if\s+(.+?)\s+(?:then|,)",
            "trigger_condition",
            ["If the validation fails", "If no data is found"]
        ),
        ConversionRule(
            r"upon\s+(.+)",
            "trigger_event",
            ["Upon completion", "Upon receipt of signal"]
        )
    ]
    
    # Action extraction rules
    ACTION_RULES = [
        ConversionRule(
            r"(?:do|perform|execute|run)\s+(.+?)(?:\.|$|\n)",
            "action_imperative",
            ["Do the validation", "Execute the transformation"]
        ),
        ConversionRule(
            r"(?:validate|check|verify)\s+(.+?)(?:\.|$|\n)",
            "action_validation",
            ["Validate the input", "Check the file exists"]
        ),
        ConversionRule(
            r"(?:send|transmit|notify|alert)\s+(.+?)(?:\.|$|\n)",
            "action_communication",
            ["Send alert to operations", "Notify the administrator"]
        ),
        ConversionRule(
            r"(?:read|load|fetch|retrieve)\s+(.+?)(?:\.|$|\n)",
            "action_input",
            ["Read the configuration", "Load the data file"]
        ),
        ConversionRule(
            r"(?:write|save|store|output|generate)\s+(.+?)(?:\.|$|\n)",
            "action_output",
            ["Write to the database", "Generate the report"]
        )
    ]
    
    # Actor identification rules
    ACTOR_RULES = [
        ConversionRule(
            r"(\w+(?:\s+\w+)*)\s+(?:handles?|manages?|processes?|owns?)",
            "actor_responsibility",
            ["Operations handles", "The system processes"]
        ),
        ConversionRule(
            r"(?:by|from)\s+(\w+(?:\s+\w+)*)",
            "actor_agent",
            ["by the operator", "from the API"]
        ),
        ConversionRule(
            r"(\w+(?:\s+\w+)*)\s+(?:must|should|will)\s+",
            "actor_obligation",
            ["The administrator must", "DevOps will"]
        )
    ]
    
    # Condition extraction rules
    CONDITION_RULES = [
        ConversionRule(
            r"only\s+if\s+(.+?)(?:\.|$|\n)",
            "condition_prerequisite",
            ["Only if validation passes", "Only if file exists"]
        ),
        ConversionRule(
            r"(?:provided|assuming)\s+that\s+(.+?)(?:\.|$|\n)",
            "condition_assumption",
            ["Provided that the system is online"]
        ),
        ConversionRule(
            r"in\s+case\s+(?:of\s+)?(.+?)(?:\.|$|\n)",
            "condition_contingency",
            ["In case of failure", "In case the file is missing"]
        )
    ]
    
    # SLA extraction rules
    SLA_RULES = [
        ConversionRule(
            r"within\s+(\d+)\s*(second|minute|hour|day)s?",
            "sla_timebound",
            ["Within 5 minutes", "Within 30 seconds"]
        ),
        ConversionRule(
            r"(?:must\s+(?:complete|finish)|should\s+take)\s+(?:less\s+than\s+|no\s+more\s+than\s+)?(\d+)\s*(second|minute|hour)s?",
            "sla_requirement",
            ["Must complete in 2 minutes", "Should take less than 30 seconds"]
        )
    ]

class ConversionPhaseProcessor(ABC):
    """Abstract base for conversion phase processors"""
    
    @abstractmethod
    def process(self, context: ConversionContext) -> ConversionContext:
        """Process the current phase and update context"""
        pass
    
    @abstractmethod
    def validate(self, context: ConversionContext) -> List[str]:
        """Validate the phase results"""
        pass

class ScopeDefinitionProcessor(ConversionPhaseProcessor):
    """Extract process scope, boundaries, and success criteria"""
    
    def process(self, context: ConversionContext) -> ConversionContext:
        prose = context.source_prose
        
        # Extract process name (often in title or first sentence)
        name_patterns = [
            r"^(.+?)\s+(?:process|workflow|procedure)",
            r"^(.+?)(?:\n|\.)",
            r"(?:process|workflow):\s*(.+?)(?:\n|\.)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, prose, re.IGNORECASE | re.MULTILINE)
            if match:
                context.conversion_log.append(f"Extracted process name: {match.group(1).strip()}")
                break
        
        # Extract boundaries
        boundary_patterns = [
            r"(?:starts?|begins?|initiates?)\s+(?:when|with|by)\s+(.+?)(?:\.|$|\n)",
            r"(?:ends?|completes?|finishes?)\s+(?:when|with|by)\s+(.+?)(?:\.|$|\n)",
            r"from\s+(.+?)\s+to\s+(.+?)(?:\.|$|\n)"
        ]
        
        for pattern in boundary_patterns:
            matches = re.finditer(pattern, prose, re.IGNORECASE)
            for match in matches:
                context.conversion_log.append(f"Boundary identified: {match.group(0)}")
        
        return context
    
    def validate(self, context: ConversionContext) -> List[str]:
        errors = []
        if not any("process name" in log for log in context.conversion_log):
            errors.append("No clear process name identified")
        return errors

class ActorExtractionProcessor(ConversionPhaseProcessor):
    """Extract and normalize actors and systems"""
    
    def process(self, context: ConversionContext) -> ConversionContext:
        prose = context.source_prose
        
        # Extract actors using predefined rules
        for rule in ConversionRuleSet.ACTOR_RULES:
            matches = re.finditer(rule.pattern, prose, re.IGNORECASE)
            for match in matches:
                actor_name = match.group(1).strip()
                normalized_name = self._normalize_actor_name(actor_name)
                
                if normalized_name not in context.actors:
                    context.actors[normalized_name] = actor_name
                    context.conversion_log.append(f"Actor identified: {actor_name} -> {normalized_name}")
        
        # Extract systems (automated components)
        system_patterns = [
            r"(?:the\s+)?(\w+(?:\s+\w+)*)\s+(?:system|service|application|API)",
            r"(\w+(?:\s+\w+)*)\s+(?:automatically|programmatically)",
            r"(?:using|via)\s+(\w+(?:\s+\w+)*)"
        ]
        
        for pattern in system_patterns:
            matches = re.finditer(pattern, prose, re.IGNORECASE)
            for match in matches:
                system_name = match.group(1).strip()
                normalized_name = self._normalize_system_name(system_name)
                
                if normalized_name not in context.systems:
                    context.systems[normalized_name] = system_name
                    context.conversion_log.append(f"System identified: {system_name} -> {normalized_name}")
        
        return context
    
    def _normalize_actor_name(self, name: str) -> str:
        """Normalize actor name to standard format"""
        # Convert to uppercase, replace spaces with underscores
        normalized = re.sub(r'\s+', '_', name.upper())
        return f"ROLE.{normalized}"
    
    def _normalize_system_name(self, name: str) -> str:
        """Normalize system name to standard format"""
        normalized = re.sub(r'\s+', '_', name.upper())
        return f"SYS.{normalized}"
    
    def validate(self, context: ConversionContext) -> List[str]:
        errors = []
        if not context.actors and not context.systems:
            errors.append("No actors or systems identified")
        return errors

class AtomicDecompositionProcessor(ConversionPhaseProcessor):
    """Decompose prose into atomic, single-responsibility actions"""
    
    def process(self, context: ConversionContext) -> ConversionContext:
        prose = context.source_prose
        sentences = self._split_into_sentences(prose)
        
        for sentence in sentences:
            atomic_actions = self._decompose_sentence(sentence)
            for action in atomic_actions:
                context.atomic_actions.append(action)
                context.conversion_log.append(f"Atomic action: {action['description']}")
        
        return context
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for analysis"""
        # Simple sentence splitting (could be enhanced with NLP)
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _decompose_sentence(self, sentence: str) -> List[Dict[str, Any]]:
        """Decompose a sentence into atomic actions"""
        actions = []
        
        # Check for compound actions (multiple verbs)
        action_verbs = re.findall(r'\b(?:validate|check|verify|send|read|write|load|save|process|execute|run|perform|generate|calculate|transform|filter|sort|merge|split)\b', sentence, re.IGNORECASE)
        
        if len(action_verbs) > 1:
            # Multiple actions in one sentence - need to split
            for verb in action_verbs:
                action = self._extract_single_action(sentence, verb)
                if action:
                    actions.append(action)
        else:
            # Single action
            action = self._extract_single_action(sentence)
            if action:
                actions.append(action)
        
        return actions
    
    def _extract_single_action(self, sentence: str, focus_verb: str = None) -> Optional[Dict[str, Any]]:
        """Extract a single atomic action from a sentence"""
        
        # Match against action rules
        for rule in ConversionRuleSet.ACTION_RULES:
            match = rule.matches(sentence)
            if match:
                return {
                    'description': match.group(1).strip(),
                    'type': rule.action,
                    'source_sentence': sentence,
                    'intent': self._extract_intent(sentence),
                    'confidence': 0.8  # Could be enhanced with ML
                }
        
        return None
    
    def _extract_intent(self, sentence: str) -> str:
        """Extract the intent/purpose of the action"""
        intent_patterns = [
            r"(?:so\s+that|in\s+order\s+to|to\s+(?:ensure|make\s+sure))\s+(.+?)(?:\.|$)",
            r"(?:for|because|since)\s+(.+?)(?:\.|$)"
        ]
        
        for pattern in intent_patterns:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def validate(self, context: ConversionContext) -> List[str]:
        errors = []
        if not context.atomic_actions:
            errors.append("No atomic actions extracted")
        
        # Check for overly complex actions
        complex_actions = [a for a in context.atomic_actions if len(a['description'].split()) > 15]
        if complex_actions:
            errors.append(f"{len(complex_actions)} actions may be too complex and need further decomposition")
        
        return errors

class ProseToAtomicConverter:
    """Main converter orchestrating the conversion process"""
    
    def __init__(self):
        self.processors = {
            ConversionPhase.SCOPE_DEFINITION: ScopeDefinitionProcessor(),
            ConversionPhase.ACTOR_EXTRACTION: ActorExtractionProcessor(),
            ConversionPhase.ATOMIC_DECOMPOSITION: AtomicDecompositionProcessor(),
            # Additional processors would be implemented here
        }
    
    def convert(self, prose: str, domain: str = "") -> Tuple[ConversionContext, List[str]]:
        """Convert prose to atomic process definition"""
        
        context = ConversionContext(source_prose=prose, domain=domain)
        all_errors = []
        
        # Process each phase in order
        for phase in ConversionPhase:
            if phase in self.processors:
                context.current_phase = phase
                context = self.processors[phase].process(context)
                
                # Validate phase results
                errors = self.processors[phase].validate(context)
                if errors:
                    all_errors.extend([f"{phase.value}: {error}" for error in errors])
        
        return context, all_errors
    
    def generate_yaml_skeleton(self, context: ConversionContext) -> str:
        """Generate initial YAML skeleton from conversion context"""
        
        yaml_content = f"""# ===== Atomic Process Definition =====
schema_version: 2.0
process:
  id: PROC.{context.domain.upper().replace(' ', '_')}
  name: "Process Name"  # TODO: Extract from context
  version: "0.1.0"
  description: >
    TODO: Add process description
  domain: "{context.domain}"
  owner: "TODO"
  tags: {list(context.domain.split()) if context.domain else ['todo']}

# ---- Canonical Registries ----
roles:
"""
        
        # Add identified roles
        for role_id, role_name in context.actors.items():
            yaml_content += f"""  - id: {role_id}
    name: "{role_name}"
"""
        
        yaml_content += """
systems:
"""
        
        # Add identified systems
        for system_id, system_name in context.systems.items():
            yaml_content += f"""  - id: {system_id}
    name: "{system_name}"
"""
        
        yaml_content += """
artifacts:
  # TODO: Define artifacts from context

enums:
  # TODO: Define relevant enums

# ---- Atomic Steps ----
steps:
"""
        
        # Add atomic actions as step skeletons
        for i, action in enumerate(context.atomic_actions[:5], 1):  # Limit to first 5 for skeleton
            step_id = f"1.{i:03d}"
            yaml_content += f"""  - id: "{step_id}"
    name: "{action['description'][:50]}..."
    intent: "{action.get('intent', 'TODO')}"
    owner: ROLE.TODO
    system: SYS.TODO
    sla: "TODO: Define SLA"
    actions:
      - "{action['description']}"
    on_success:
      next: "{f'1.{i+1:03d}' if i < len(context.atomic_actions) else 'null'}"
    # TODO: Add inputs, outputs, validations, etc.

"""
        
        return yaml_content

# Example usage and testing
def main():
    """Demo the conversion framework"""
    
    sample_prose = """
    Economic Calendar Ingestion Process
    
    The system monitors the Downloads folder every hour for new economic calendar files.
    When a new file appears, the Python service validates the file format and checks
    if it's different from the previously processed file. If validation passes,
    the service normalizes the data by converting timestamps to UTC and filtering
    for medium and high impact events only. The DevOps team ensures that the 
    processed file is saved to the output directory within 5 minutes. If any
    step fails, the system sends an alert to the Operations team and quarantines
    the problematic file.
    """
    
    converter = ProseToAtomicConverter()
    context, errors = converter.convert(sample_prose, "trading")
    
    print("=== Conversion Results ===")
    print(f"Actors identified: {list(context.actors.keys())}")
    print(f"Systems identified: {list(context.systems.keys())}")
    print(f"Atomic actions: {len(context.atomic_actions)}")
    
    if errors:
        print(f"\nErrors: {errors}")
    
    print("\n=== Generated YAML Skeleton ===")
    yaml_skeleton = converter.generate_yaml_skeleton(context)
    print(yaml_skeleton[:1000] + "..." if len(yaml_skeleton) > 1000 else yaml_skeleton)

if __name__ == "__main__":
    main()