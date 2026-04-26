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
            except json.JSONDecodeError as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Malformed validation rules for attribute {definition.id}: {str(e)}")
                raise ValueError("Validation rules are corrupted (invalid JSON)")

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
            from datetime import datetime
            try:
                datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                 raise ValueError("Date must be in YYYY-MM-DD format")

        elif definition.type == AttributeTypeEnum.CHOICE.value:
            if "options" not in rules or not isinstance(rules["options"], list):
                raise ValueError("Attribute definition is missing valid 'options' list")
            if value not in rules["options"]:
                raise ValueError(f"Value '{value}' is not a valid option")

        return True
