import json
import re
from typing import Dict, Any, Union
from ..models import AttributeDefinition
from ..schemas.configuration import AttributeTypeEnum, NumericalRules, TextRules

class ValidationService:
    @staticmethod
    def validate_attribute_value(definition: AttributeDefinition, value: str) -> bool:
        """
        Validates a value against the attribute definition's rules.
        Raises ValueError if validation fails.
        """
        # Parse Rules
        rules: Dict[str, Any] = {}
        if definition.validation_rules:
            try:
                if isinstance(definition.validation_rules, str):
                    rules = json.loads(definition.validation_rules)
                elif isinstance(definition.validation_rules, dict):
                    rules = definition.validation_rules
            except json.JSONDecodeError:
                # Log this? For now, fail safe (allow or deny? allow if rules are broken to avoid blockage)
                # Let's log and proceed, or raise error? 
                # Better to ignore malformed rules than blocking operations, but M11 Hardening implies strictness.
                # Let's fail safe (pass) but maybe log.
                pass

        # 1. Type Validation
        if definition.type == AttributeTypeEnum.NUMERICAL.value:
            try:
                num_val = float(value)
            except ValueError:
                raise ValueError(f"Value '{value}' must be a number")
            
            # Min/Max Validation
            if "min" in rules and rules["min"] is not None:
                if num_val < rules["min"]:
                    raise ValueError(f"Value {num_val} is below minimum {rules['min']}")
            if "max" in rules and rules["max"] is not None:
                if num_val > rules["max"]:
                    raise ValueError(f"Value {num_val} is above maximum {rules['max']}")

        elif definition.type == AttributeTypeEnum.TEXT.value:
            # Length
            if "min_length" in rules and rules["min_length"] is not None:
                if len(value) < rules["min_length"]:
                    raise ValueError(f"Text length {len(value)} is below minimum {rules['min_length']}")
            
            # Regex
            if "regex" in rules and rules["regex"]:
                if not re.match(rules["regex"], value):
                    raise ValueError(f"Value does not match required format (regex: {rules['regex']})")
                    
        elif definition.type == AttributeTypeEnum.DATE.value:
            # Basic ISO format check? YYYY-MM-DD
            # Using datetime.fromisoformat or simple regex
            if not re.match(r"^\d{4}-\d{2}-\d{2}", value):
                 raise ValueError("Date must be in YYYY-MM-DD format")

        elif definition.type == AttributeTypeEnum.CHOICE.value:
            # Check if value is in options
            if "options" in rules and isinstance(rules["options"], list):
                if value not in rules["options"]:
                    raise ValueError(f"Value '{value}' is not a valid option")

        return True
