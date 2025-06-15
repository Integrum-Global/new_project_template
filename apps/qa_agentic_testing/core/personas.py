#!/usr/bin/env python3
"""
Persona Management System for QA Agentic Testing

This module provides intelligent persona generation and management for testing applications.
Personas represent different user types with specific permissions, behaviors, and goals.
"""

import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class Persona:
    """Represents a user persona for testing with specific characteristics and permissions."""

    key: str
    name: str
    role: str
    permissions: List[str]
    goals: List[str]
    behavior_style: str
    typical_actions: List[str]
    expected_success_rate: float = 100.0
    test_focus: List[str] = None

    def __post_init__(self):
        if self.test_focus is None:
            self.test_focus = ["functionality", "permissions", "performance"]

    def get_system_prompt(self) -> str:
        """Generate system prompt for LLM agent based on persona characteristics."""
        return f"""You are {self.name}, a {self.role} testing an application.

Your permissions: {', '.join(self.permissions)}
Your goals: {', '.join(self.goals)}
Your behavior style: {self.behavior_style}
Typical actions you perform: {', '.join(self.typical_actions)}

When testing the application:
1. Act naturally according to your role and permissions
2. Analyze what operations you should be able to perform
3. Consider what outcomes you expect based on your access level
4. Report any issues, unexpected behavior, or security concerns
5. Provide feedback on usability and user experience

Focus areas for this persona: {', '.join(self.test_focus)}

Respond in a structured way that includes:
- Your understanding of the task
- What you attempted to do
- What you observed
- Whether the behavior matches your expectations
- Any issues, suggestions, or security concerns
"""

    def can_perform_action(self, action: str) -> bool:
        """Check if persona should be able to perform a specific action based on permissions."""
        if not self.permissions:
            return False

        # Check for wildcard permissions
        for perm in self.permissions:
            if "*" in perm:
                action_prefix = action.split(":")[0] if ":" in action else action
                perm_prefix = perm.split(":")[0] if ":" in perm else perm
                if action_prefix == perm_prefix or perm == "*":
                    return True

        # Check for exact permission match
        return action in self.permissions

    def to_dict(self) -> Dict[str, Any]:
        """Convert persona to dictionary format."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Persona":
        """Create persona from dictionary."""
        return cls(**data)


class PersonaManager:
    """Manages personas for testing, including built-in templates and custom personas."""

    def __init__(self, templates_dir: Optional[Path] = None):
        self.personas: Dict[str, Persona] = {}
        self.templates_dir = (
            templates_dir or Path(__file__).parent.parent / "templates" / "personas"
        )
        self._load_built_in_personas()
        self._load_template_personas()

    def _load_built_in_personas(self):
        """Load standard built-in personas for common testing scenarios."""

        # Admin Personas
        self.add_persona(
            Persona(
                key="system_admin",
                name="Alice Admin",
                role="System Administrator",
                permissions=["*"],  # Full access
                goals=[
                    "Maintain system security",
                    "Manage all users",
                    "Monitor system activity",
                    "Ensure compliance",
                ],
                behavior_style="Systematic, security-conscious, detail-oriented, thorough",
                typical_actions=[
                    "Create users",
                    "Assign roles",
                    "Review audit logs",
                    "Configure settings",
                    "Monitor performance",
                ],
                expected_success_rate=100.0,
                test_focus=["security", "functionality", "performance", "audit"],
            )
        )

        self.add_persona(
            Persona(
                key="security_officer",
                name="Sarah Security",
                role="Security Officer",
                permissions=["user:read", "role:read", "audit:read", "security:*"],
                goals=[
                    "Monitor security events",
                    "Investigate anomalies",
                    "Generate compliance reports",
                    "Ensure security policies",
                ],
                behavior_style="Vigilant, investigative, compliance-focused, thorough",
                typical_actions=[
                    "Review audit logs",
                    "Monitor login patterns",
                    "Investigate security events",
                    "Generate reports",
                ],
                expected_success_rate=75.0,  # Some restrictions expected
                test_focus=["security", "audit", "compliance"],
            )
        )

        # Business Personas
        self.add_persona(
            Persona(
                key="manager",
                name="Mark Manager",
                role="Department Manager",
                permissions=[
                    "user:read",
                    "user:update",
                    "role:read",
                    "audit:read:own_department",
                ],
                goals=[
                    "Manage team access",
                    "Review team activity",
                    "Request access changes",
                    "Monitor team performance",
                ],
                behavior_style="Goal-oriented, efficiency-focused, team-centric, results-driven",
                typical_actions=[
                    "View team members",
                    "Update team info",
                    "Review team reports",
                    "Request role changes",
                ],
                expected_success_rate=60.0,  # Limited by departmental scope
                test_focus=["functionality", "permissions", "usability"],
            )
        )

        self.add_persona(
            Persona(
                key="analyst",
                name="Anna Analyst",
                role="Business Analyst",
                permissions=["data:read", "reports:generate", "export:data"],
                goals=[
                    "Generate business reports",
                    "Analyze trends",
                    "Export data",
                    "Create dashboards",
                ],
                behavior_style="Data-driven, analytical, detail-oriented, methodical",
                typical_actions=[
                    "Run reports",
                    "Export data",
                    "Analyze trends",
                    "Create visualizations",
                ],
                expected_success_rate=80.0,
                test_focus=["functionality", "performance", "data_accuracy"],
            )
        )

        # User Personas
        self.add_persona(
            Persona(
                key="regular_user",
                name="Rachel Regular",
                role="Regular User",
                permissions=["user:read:self", "user:update:self", "data:read:own"],
                goals=[
                    "Access needed resources",
                    "Update own information",
                    "Complete daily tasks",
                ],
                behavior_style="Task-focused, efficiency-seeking, cautious with new features",
                typical_actions=[
                    "View own profile",
                    "Update personal info",
                    "Access assigned resources",
                ],
                expected_success_rate=90.0,
                test_focus=["usability", "functionality", "accessibility"],
            )
        )

        self.add_persona(
            Persona(
                key="new_user",
                name="Nancy Newbie",
                role="New User",
                permissions=["user:read:self", "onboarding:access"],
                goals=[
                    "Learn the system",
                    "Complete onboarding",
                    "Get necessary access",
                ],
                behavior_style="Curious, cautious, question-asking, learning-oriented",
                typical_actions=[
                    "Explore interface",
                    "Follow tutorials",
                    "Ask for help",
                    "Try basic features",
                ],
                expected_success_rate=70.0,  # May encounter learning curve issues
                test_focus=["usability", "onboarding", "accessibility", "help_system"],
            )
        )

        self.add_persona(
            Persona(
                key="power_user",
                name="Paul Power",
                role="Power User",
                permissions=["user:*:self", "advanced:features", "integration:api"],
                goals=[
                    "Use advanced features",
                    "Integrate with other tools",
                    "Maximize productivity",
                ],
                behavior_style="Experienced, efficiency-focused, feature-seeking, technical",
                typical_actions=[
                    "Use advanced features",
                    "Configure integrations",
                    "Automate workflows",
                ],
                expected_success_rate=95.0,
                test_focus=[
                    "advanced_features",
                    "performance",
                    "integration",
                    "automation",
                ],
            )
        )

    def _load_template_personas(self):
        """Load personas from template files if they exist."""
        if self.templates_dir.exists():
            for template_file in self.templates_dir.glob("*.json"):
                try:
                    with open(template_file, "r") as f:
                        persona_data = json.load(f)
                        if isinstance(persona_data, list):
                            for p_data in persona_data:
                                persona = Persona.from_dict(p_data)
                                self.add_persona(persona)
                        else:
                            persona = Persona.from_dict(persona_data)
                            self.add_persona(persona)
                except Exception as e:
                    print(
                        f"Warning: Could not load persona template {template_file}: {e}"
                    )

    def get_available_industries(self) -> List[str]:
        """Get list of available industry-specific persona templates."""
        industries = []
        if self.templates_dir.exists():
            for template_file in self.templates_dir.glob("*.json"):
                industry_name = template_file.stem.replace("_", " ").title()
                industries.append(industry_name)
        return industries

    def load_industry_personas(self, industry: str) -> List[Persona]:
        """Load personas for a specific industry."""
        industry_file = industry.lower().replace(" ", "_")
        template_path = self.templates_dir / f"{industry_file}.json"

        loaded_personas = []
        if template_path.exists():
            try:
                with open(template_path, "r") as f:
                    persona_data = json.load(f)
                    for p_data in persona_data:
                        persona = Persona.from_dict(p_data)
                        self.add_persona(persona)
                        loaded_personas.append(persona)
            except Exception as e:
                print(f"Error loading industry personas from {template_path}: {e}")

        return loaded_personas

    def generate_custom_persona_interactive(self) -> Persona:
        """Interactive persona generation wizard."""
        print("\n🎭 Custom Persona Generation Wizard")
        print("=" * 50)

        # Basic information
        key = input("Enter persona key (e.g., 'finance_approver'): ").strip()
        name = input("Enter persona name (e.g., 'Frank Finance'): ").strip()
        role = input("Enter role/title (e.g., 'Financial Analyst'): ").strip()

        # Permissions
        print("\nPermissions (enter one per line, empty line to finish):")
        permissions = []
        while True:
            perm = input("  Permission: ").strip()
            if not perm:
                break
            permissions.append(perm)

        # Goals
        print("\nGoals (enter one per line, empty line to finish):")
        goals = []
        while True:
            goal = input("  Goal: ").strip()
            if not goal:
                break
            goals.append(goal)

        # Behavior style
        behavior_style = input(
            "\nBehavior style (e.g., 'detail-oriented, analytical'): "
        ).strip()

        # Typical actions
        print("\nTypical actions (enter one per line, empty line to finish):")
        typical_actions = []
        while True:
            action = input("  Action: ").strip()
            if not action:
                break
            typical_actions.append(action)

        # Expected success rate
        while True:
            try:
                success_rate = float(input("Expected success rate (0-100): ").strip())
                if 0 <= success_rate <= 100:
                    break
                print("Please enter a value between 0 and 100")
            except ValueError:
                print("Please enter a valid number")

        # Test focus areas
        print(
            "\nTest focus areas (select from: functionality, security, performance, usability, compliance)"
        )
        print("Enter selections separated by commas:")
        focus_input = input("Test focus: ").strip()
        test_focus = [f.strip() for f in focus_input.split(",") if f.strip()]

        # Create persona
        persona = Persona(
            key=key,
            name=name,
            role=role,
            permissions=permissions,
            goals=goals,
            behavior_style=behavior_style,
            typical_actions=typical_actions,
            expected_success_rate=success_rate,
            test_focus=test_focus or ["functionality"],
        )

        # Add to manager
        self.add_persona(persona)

        print(f"\n✅ Created persona: {persona.name} ({persona.key})")
        return persona

    def add_persona(self, persona: Persona):
        """Add a persona to the manager."""
        self.personas[persona.key] = persona

    def get_persona(self, key: str) -> Optional[Persona]:
        """Get a persona by key."""
        return self.personas.get(key)

    def list_personas(self) -> List[str]:
        """Get list of all available persona keys."""
        return list(self.personas.keys())

    def get_personas_by_role(self, role_type: str) -> List[Persona]:
        """Get personas filtered by role type (admin, manager, user, etc.)."""
        role_keywords = {
            "admin": ["admin", "administrator", "security"],
            "manager": ["manager", "supervisor", "lead"],
            "user": ["user", "regular", "standard"],
            "analyst": ["analyst", "researcher", "data"],
            "support": ["support", "help", "customer"],
        }

        keywords = role_keywords.get(role_type.lower(), [role_type.lower()])
        matching_personas = []

        for persona in self.personas.values():
            if any(keyword in persona.role.lower() for keyword in keywords):
                matching_personas.append(persona)

        return matching_personas

    def generate_personas_from_permissions(
        self, permission_patterns: List[str]
    ) -> List[Persona]:
        """Generate personas automatically based on discovered permission patterns."""
        generated_personas = []

        # Analyze permission patterns to identify user types
        permission_groups = self._group_permissions(permission_patterns)

        for group_name, permissions in permission_groups.items():
            # Generate persona based on permission group
            persona_key = f"generated_{group_name.lower().replace(' ', '_')}"

            if persona_key not in self.personas:
                persona = self._create_persona_from_permissions(
                    key=persona_key,
                    name=f"Generated {group_name}",
                    role=group_name,
                    permissions=permissions,
                )
                generated_personas.append(persona)
                self.add_persona(persona)

        return generated_personas

    def _group_permissions(self, permissions: List[str]) -> Dict[str, List[str]]:
        """Group permissions into logical user types."""
        groups = {
            "Admin User": [],
            "Manager User": [],
            "Regular User": [],
            "Read-Only User": [],
        }

        for perm in permissions:
            if "*" in perm or "admin" in perm.lower():
                groups["Admin User"].append(perm)
            elif "manage" in perm.lower() or "update" in perm.lower():
                groups["Manager User"].append(perm)
            elif "read" in perm.lower() and "write" not in perm.lower():
                groups["Read-Only User"].append(perm)
            else:
                groups["Regular User"].append(perm)

        # Remove empty groups
        return {k: v for k, v in groups.items() if v}

    def _create_persona_from_permissions(
        self, key: str, name: str, role: str, permissions: List[str]
    ) -> Persona:
        """Create a persona based on permission analysis."""

        # Determine expected success rate based on permissions
        success_rate = 100.0
        if not any("*" in p or "admin" in p.lower() for p in permissions):
            success_rate = 75.0
        if all("read" in p.lower() for p in permissions):
            success_rate = 60.0

        # Generate goals based on permissions
        goals = self._infer_goals_from_permissions(permissions)

        # Generate typical actions
        actions = self._infer_actions_from_permissions(permissions)

        # Determine behavior style
        behavior_style = self._infer_behavior_style(role, permissions)

        return Persona(
            key=key,
            name=name,
            role=role,
            permissions=permissions,
            goals=goals,
            behavior_style=behavior_style,
            typical_actions=actions,
            expected_success_rate=success_rate,
        )

    def _infer_goals_from_permissions(self, permissions: List[str]) -> List[str]:
        """Infer user goals from their permissions."""
        goals = []

        perm_text = " ".join(permissions).lower()

        if "user" in perm_text:
            if "create" in perm_text or "*" in perm_text:
                goals.append("Manage user accounts")
            if "read" in perm_text:
                goals.append("View user information")

        if "role" in perm_text:
            goals.append("Manage user roles and permissions")

        if "audit" in perm_text:
            goals.append("Monitor system activity")

        if "data" in perm_text:
            goals.append("Access and analyze data")

        if "report" in perm_text:
            goals.append("Generate reports")

        return goals or ["Use the application effectively"]

    def _infer_actions_from_permissions(self, permissions: List[str]) -> List[str]:
        """Infer typical actions from permissions."""
        actions = []

        for perm in permissions:
            if "create" in perm.lower():
                resource = perm.split(":")[0] if ":" in perm else "items"
                actions.append(f"Create {resource}")
            elif "read" in perm.lower():
                resource = perm.split(":")[0] if ":" in perm else "information"
                actions.append(f"View {resource}")
            elif "update" in perm.lower():
                resource = perm.split(":")[0] if ":" in perm else "items"
                actions.append(f"Update {resource}")
            elif "delete" in perm.lower():
                resource = perm.split(":")[0] if ":" in perm else "items"
                actions.append(f"Delete {resource}")

        return actions or ["Use application features"]

    def _infer_behavior_style(self, role: str, permissions: List[str]) -> str:
        """Infer behavior style from role and permissions."""
        styles = []

        if "admin" in role.lower():
            styles.extend(["Systematic", "security-conscious", "detail-oriented"])
        elif "manager" in role.lower():
            styles.extend(["Goal-oriented", "efficiency-focused", "team-centric"])
        elif "user" in role.lower():
            styles.extend(["Task-focused", "practical", "efficiency-seeking"])

        if any("security" in p.lower() for p in permissions):
            styles.append("security-aware")
        if any("audit" in p.lower() for p in permissions):
            styles.append("compliance-focused")
        if any("read" in p.lower() and "write" not in p.lower() for p in permissions):
            styles.append("cautious")

        return ", ".join(styles) if styles else "Professional, goal-oriented"

    def export_personas(self, file_path: Path):
        """Export all personas to a JSON file."""
        personas_data = [persona.to_dict() for persona in self.personas.values()]
        with open(file_path, "w") as f:
            json.dump(personas_data, f, indent=2)

    def import_personas(self, file_path: Path):
        """Import personas from a JSON file."""
        with open(file_path, "r") as f:
            personas_data = json.load(f)

        for persona_dict in personas_data:
            persona = Persona.from_dict(persona_dict)
            self.add_persona(persona)

    def get_testing_matrix(
        self, selected_personas: Optional[List[str]] = None
    ) -> List[Persona]:
        """Get a curated list of personas for comprehensive testing."""
        if selected_personas:
            return [
                self.personas[key] for key in selected_personas if key in self.personas
            ]

        # Default testing matrix covers major user types
        default_personas = [
            "system_admin",
            "manager",
            "regular_user",
            "security_officer",
        ]
        available_personas = [
            self.personas[key] for key in default_personas if key in self.personas
        ]

        # Add any additional personas if we don't have enough coverage
        if len(available_personas) < 3:
            additional = [
                p for p in self.personas.values() if p.key not in default_personas
            ]
            available_personas.extend(additional[: 3 - len(available_personas)])

        return available_personas

    # Async methods for future extensibility

    async def generate_personas_from_permissions_async(
        self, permissions: List[str]
    ) -> List[Persona]:
        """Async version of generate_personas_from_permissions for future enhancement."""
        # Small delay to simulate async processing
        await asyncio.sleep(0.01)

        # Delegate to sync method for now
        return self.generate_personas_from_permissions(permissions)

    async def get_testing_matrix_async(self) -> List[Persona]:
        """Async version of get_testing_matrix for future enhancement."""
        # Small delay to simulate async processing
        await asyncio.sleep(0.01)

        # Delegate to sync method for now
        return self.get_testing_matrix()
