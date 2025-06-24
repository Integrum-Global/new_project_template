"""User Management Configuration"""

from .settings import UserManagementConfig

# Create a singleton instance
config = UserManagementConfig()

# For backward compatibility
AppConfig = UserManagementConfig

__all__ = ["config", "AppConfig", "UserManagementConfig"]
