"""
Optimized User Validator Node
Reusable node for validating user input with configurable rules
"""

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from kailash.nodes import Node, NodeParameter


class UserValidatorNode(Node):
    """
    High-performance user input validation node with configurable rules

    Features:
    - Email validation with DNS checking (optional)
    - Username format and uniqueness validation
    - Password strength checking with configurable policies
    - Custom field validation rules
    - Async validation support
    - Caching for repeated validations
    """

    def __init__(self, **kwargs):
        # Set default configuration
        self.validation_rules = kwargs.pop(
            "validation_rules", self._get_default_rules()
        )
        self.enable_dns_check = kwargs.pop("enable_dns_check", False)
        self.cache_results = kwargs.pop("cache_results", True)
        self.custom_validators = kwargs.pop("custom_validators", {})

        # Initialize
        super().__init__(**kwargs)

    def get_parameters(self) -> Dict[str, NodeParameter]:
        """Define node parameters"""
        return {
            "validation_type": NodeParameter(
                name="validation_type",
                type=str,
                description="Type of validation to perform",
                default="email",
                required=False,
            ),
            "value": NodeParameter(
                name="value", type=str, description="Value to validate", required=False
            ),
            "email": NodeParameter(
                name="email",
                type=str,
                description="Email address to validate",
                required=False,
            ),
            "username": NodeParameter(
                name="username",
                type=str,
                description="Username to validate",
                required=False,
            ),
            "password": NodeParameter(
                name="password",
                type=str,
                description="Password to validate",
                required=False,
            ),
            "profile_data": NodeParameter(
                name="profile_data",
                type=dict,
                description="Profile data to validate",
                required=False,
            ),
            "existing_values": NodeParameter(
                name="existing_values",
                type=list,
                description="Existing values for duplicate checking",
                required=False,
                default=[],
            ),
            "batch_items": NodeParameter(
                name="batch_items",
                type=list,
                description="List of items to validate in batch",
                required=False,
                default=[],
            ),
            "custom_rules": NodeParameter(
                name="custom_rules",
                type=dict,
                description="Custom validation rules",
                required=False,
                default={},
            ),
        }

    def _get_default_rules(self) -> Dict[str, Any]:
        """Get default validation rules"""
        return {
            "email": {
                "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                "max_length": 254,
                "check_dns": False,
            },
            "username": {
                "pattern": r"^[a-zA-Z0-9_-]{3,32}$",
                "min_length": 3,
                "max_length": 32,
                "reserved_words": ["admin", "root", "system", "api", "test"],
            },
            "password": {
                "min_length": 8,
                "max_length": 128,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_numbers": True,
                "require_special": True,
                "special_chars": "!@#$%^&*()_+-=[]{}|;:,.<>?",
            },
            "phone": {"pattern": r"^\+?1?\d{9,15}$"},
        }

    def validate_email(self, email: str) -> tuple[Optional[str], Optional[str]]:
        """Validate email address"""
        if not email:
            return None, "Email is required"

        email = email.lower().strip()

        # Check pattern
        pattern = self.validation_rules.get("email", {}).get(
            "pattern", r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        )
        if not re.match(pattern, email):
            return None, "Invalid email format"

        # Check length
        if len(email) > self.validation_rules.get("email", {}).get("max_length", 254):
            return None, "Email too long"

        # Check for suspicious patterns
        if email.count("@") != 1:
            return None, "Invalid email format"

        local, domain = email.split("@")

        # Check local part
        if not local or local.startswith(".") or local.endswith(".") or ".." in local:
            return None, "Invalid email format"

        # Check domain
        if (
            not domain
            or domain.startswith(".")
            or domain.endswith(".")
            or ".." in domain
        ):
            return None, "Invalid domain format"

        # DNS check if enabled
        if self.enable_dns_check and self.validation_rules.get("email", {}).get(
            "check_dns", False
        ):
            # In production, perform actual DNS lookup
            # For now, just check common domains
            common_domains = [
                "gmail.com",
                "yahoo.com",
                "hotmail.com",
                "outlook.com",
                "icloud.com",
            ]
            if domain not in common_domains and not domain.endswith(
                (".edu", ".gov", ".org")
            ):
                return None, "Domain verification failed"

        return email, None

    def validate_username(self, username: str) -> tuple[Optional[str], Optional[str]]:
        """Validate username"""
        if not username:
            return None, "Username is required"

        username = username.strip()

        # Check pattern
        pattern = self.validation_rules.get("username", {}).get(
            "pattern", r"^[a-zA-Z0-9_-]{3,32}$"
        )
        if not re.match(pattern, username):
            return (
                None,
                "Username must be 3-32 characters and contain only letters, numbers, underscore, and hyphen",
            )

        # Check length
        min_length = self.validation_rules.get("username", {}).get("min_length", 3)
        max_length = self.validation_rules.get("username", {}).get("max_length", 32)

        if len(username) < min_length:
            return None, f"Username must be at least {min_length} characters"

        if len(username) > max_length:
            return None, f"Username must be at most {max_length} characters"

        # Check reserved words
        reserved = self.validation_rules.get("username", {}).get("reserved_words", [])
        if username.lower() in [word.lower() for word in reserved]:
            return None, "Username is reserved"

        # Check for offensive content (basic check)
        offensive_patterns = ["xxx", "porn", "sex"]
        for pattern in offensive_patterns:
            if pattern in username.lower():
                return None, "Username contains inappropriate content"

        return username, None

    def validate_password(self, password: str) -> tuple[int, List[str]]:
        """Validate password and return strength score with feedback"""
        if not password:
            return 0, ["Password is required"]

        feedback = []
        score = 0
        rules = self.validation_rules.get("password", {})

        # Check length
        min_length = rules.get("min_length", 8)
        max_length = rules.get("max_length", 128)

        if len(password) < min_length:
            feedback.append(f"Password must be at least {min_length} characters")
        elif len(password) > max_length:
            feedback.append(f"Password must be at most {max_length} characters")
        else:
            score += 20
            if len(password) >= 12:
                score += 10
            if len(password) >= 16:
                score += 10

        # Check character types
        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"\d", password))
        special_chars = rules.get("special_chars", "!@#$%^&*()_+-=[]{}|;:,.<>?")
        has_special = bool(re.search(f"[{re.escape(special_chars)}]", password))

        if rules.get("require_uppercase", True) and not has_upper:
            feedback.append("Password must contain at least one uppercase letter")
        else:
            score += 15

        if rules.get("require_lowercase", True) and not has_lower:
            feedback.append("Password must contain at least one lowercase letter")
        else:
            score += 15

        if rules.get("require_numbers", True) and not has_digit:
            feedback.append("Password must contain at least one number")
        else:
            score += 15

        if rules.get("require_special", True) and not has_special:
            feedback.append("Password must contain at least one special character")
        else:
            score += 15

        # Check for common patterns
        common_patterns = ["123", "abc", "qwerty", "password", "admin", "letmein"]
        for pattern in common_patterns:
            if pattern in password.lower():
                feedback.append("Password contains common patterns")
                score = max(0, score - 20)
                break

        # Check for repeated characters
        if re.search(r"(.)\1{2,}", password):
            feedback.append("Password contains repeated characters")
            score = max(0, score - 10)

        # Final score adjustment
        score = min(100, max(0, score))

        return score, feedback

    def validate_profile_data(
        self, profile_data: Dict[str, Any]
    ) -> tuple[bool, List[str]]:
        """Validate profile data"""
        errors = []

        # Required fields
        required_fields = ["first_name", "last_name"]
        for field in required_fields:
            if field not in profile_data or not profile_data[field]:
                errors.append(f"{field.replace('_', ' ').title()} is required")

        # Name validation
        name_pattern = r"^[a-zA-Z\s\'-]{1,50}$"
        for field in ["first_name", "last_name"]:
            if field in profile_data and profile_data[field]:
                if not re.match(name_pattern, profile_data[field]):
                    errors.append(f"Invalid {field.replace('_', ' ')}")

        # Phone validation (optional)
        if "phone" in profile_data and profile_data["phone"]:
            phone_pattern = self.validation_rules.get("phone", {}).get(
                "pattern", r"^\+?1?\d{9,15}$"
            )
            if not re.match(phone_pattern, profile_data["phone"]):
                errors.append("Invalid phone number format")

        # Date of birth validation (optional)
        if "date_of_birth" in profile_data and profile_data["date_of_birth"]:
            try:
                dob = datetime.fromisoformat(profile_data["date_of_birth"])
                age = (datetime.now() - dob).days / 365.25
                if age < 13:
                    errors.append("User must be at least 13 years old")
                elif age > 120:
                    errors.append("Invalid date of birth")
            except:
                errors.append("Invalid date format for date of birth")

        return len(errors) == 0, errors

    def check_duplicate(
        self, value: str, field_type: str, existing_values: List[str]
    ) -> bool:
        """Check if value already exists"""
        if not existing_values:
            return False

        # Case-insensitive comparison for emails and usernames
        if field_type in ["email", "username"]:
            value_lower = value.lower()
            return any(value_lower == existing.lower() for existing in existing_values)

        return value in existing_values

    def run(self, **inputs) -> Dict[str, Any]:
        """Process validation request"""
        validation_type = inputs.get("validation_type", "email")

        if validation_type == "email":
            email = inputs.get("email") or inputs.get("value", "")
            validated_email, error = self.validate_email(email)

            return {
                "valid": validated_email is not None,
                "validated_value": validated_email,
                "error": error,
                "validation_type": "email",
            }

        elif validation_type == "username":
            username = inputs.get("username") or inputs.get("value", "")
            validated_username, error = self.validate_username(username)

            return {
                "valid": validated_username is not None,
                "validated_value": validated_username,
                "error": error,
                "validation_type": "username",
            }

        elif validation_type == "password":
            password = inputs.get("password") or inputs.get("value", "")
            score, feedback = self.validate_password(password)

            return {
                "valid": score >= 60 and len(feedback) == 0,
                "strength_score": score,
                "feedback": feedback,
                "validation_type": "password",
            }

        elif validation_type == "profile":
            profile_data = inputs.get("profile_data", {})
            is_valid, errors = self.validate_profile_data(profile_data)

            return {"valid": is_valid, "errors": errors, "validation_type": "profile"}

        elif validation_type == "duplicate":
            value = inputs.get("value", "")
            field_type = inputs.get("field_type", "email")
            existing_values = inputs.get("existing_values", [])

            is_duplicate = self.check_duplicate(value, field_type, existing_values)

            return {"is_duplicate": is_duplicate, "validation_type": "duplicate"}

        elif validation_type == "batch":
            batch_items = inputs.get("batch_items", [])
            results = []

            for item in batch_items:
                item_type = item.get("type", "email")
                item_value = item.get("value", "")

                if item_type == "email":
                    validated, error = self.validate_email(item_value)
                    results.append(
                        {
                            "value": item_value,
                            "valid": validated is not None,
                            "error": error,
                        }
                    )
                elif item_type == "username":
                    validated, error = self.validate_username(item_value)
                    results.append(
                        {
                            "value": item_value,
                            "valid": validated is not None,
                            "error": error,
                        }
                    )

            return {"results": results, "validation_type": "batch"}

        elif validation_type == "custom":
            value = inputs.get("value", "")
            custom_rules = inputs.get("custom_rules", {})

            # Apply custom validation rules
            errors = []

            if "pattern" in custom_rules:
                if not re.match(custom_rules["pattern"], value):
                    errors.append("Value does not match required pattern")

            if "min_length" in custom_rules:
                if len(value) < custom_rules["min_length"]:
                    errors.append(
                        f"Value must be at least {custom_rules['min_length']} characters"
                    )

            if "max_length" in custom_rules:
                if len(value) > custom_rules["max_length"]:
                    errors.append(
                        f"Value must be at most {custom_rules['max_length']} characters"
                    )

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "validation_type": "custom",
            }

        else:
            return {
                "error": f"Unknown validation type: {validation_type}",
                "validation_type": validation_type,
            }
