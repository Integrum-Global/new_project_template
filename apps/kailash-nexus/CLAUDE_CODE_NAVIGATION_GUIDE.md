# Kailash Nexus Navigation Instructions for Claude Code

## 🎯 IMMEDIATE ACTIONS

### When User Says "Navigate to X":
1. Run: `ls -la src/nexus/X/`
2. Run: `grep -r "class.*" src/nexus/X/ | head -10`
3. Read the main file in that module

### When User Says "Integrate Function Y":
1. Run: `grep -r "def Y" src/nexus/`
2. Read the file containing function Y
3. Check imports at file top
4. Add your code following the wrapper pattern

### When User Says "Replace Function Z":
1. Run: `grep -r "def Z" src/nexus/`
2. Read current implementation
3. Copy function signature exactly
4. Replace body while keeping same return type

## 📂 NAVIGATE LIKE THIS

### Find Any Module:
```bash
ls -la src/nexus/              # See all modules
ls -la src/nexus/core/         # See core components
ls -la src/nexus/channels/     # See channel wrappers
ls -la src/nexus/enterprise/   # See enterprise features
```

### Read Module Purpose:
```bash
head -20 src/nexus/core/application.py    # Read module docstring
grep "class" src/nexus/core/*.py          # Find all classes
grep "def " src/nexus/channels/*.py       # Find all functions
```

## 🔨 INTEGRATE FUNCTIONS NOW

### Step 1: Open Target File
```bash
# For API functions:
code src/nexus/channels/api_wrapper.py

# For CLI commands:
code src/nexus/channels/cli_wrapper.py

# For workflow management:
code src/nexus/core/registry.py
```

### Step 2: Add Your Function
```python
# Find the class
# Add this method:
def your_new_function(self, param1: str, param2: Dict) -> Result:
    # Check tenant
    tenant_id = self.multi_tenant_manager.get_current_tenant() if self.multi_tenant_manager else None

    # Check auth
    if self.auth_manager and not self.auth_manager.check_permission("action_name"):
        raise PermissionError("Unauthorized")

    # Your logic here
    return self.sdk_component.process(param1, param2)
```

### Step 3: Register If Needed
```python
# For API endpoints, add to setup_routes():
self.api_channel.app.add_api_route("/your-endpoint", self.your_new_function)

# For CLI commands, add to setup_commands():
self.cli.add_command(your_command_function)
```

## 🔄 REPLACE FUNCTIONS NOW

### Execute These Commands:
```bash
# 1. Find it
grep -r "def function_name" src/nexus/

# 2. Open it
code src/nexus/path/to/file.py

# 3. Read current implementation
# 4. Replace with YOUR code but KEEP:
#    - Same function name
#    - Same parameters
#    - Same return type
#    - Same decorators
```

### Template for Replacement:
```python
def function_name(self, param1: Type1, param2: Type2) -> ReturnType:
    """Keep original docstring."""
    # Add logging
    logger.info(f"Function called with {param1}")

    # YOUR NEW IMPLEMENTATION HERE

    # Must return same type as original
    return result
```

## 🧠 MEGATHINK LIKE THIS

### Start Megathinking:
```bash
# Say: "MEGATHINKING: [Your Topic]"
# Then run these commands:

# 1. Map dependencies
grep -r "import.*nexus" src/nexus/ | grep -v test | sort | uniq

# 2. Find all usages
grep -r "YourComponent" src/nexus/ | wc -l

# 3. Check tests
find tests/ -name "*test*.py" | xargs grep "YourComponent"
```

### Output Format:
```
MEGATHINKING: Adding WebSocket Support

FOUND:
- 3 files import channels
- APIChannel used in 12 places
- Tests exist in tests/test_channels.py

DECISION:
- Create websocket_wrapper.py
- Follow api_wrapper.py pattern
- Add tests to test_channels.py

RISKS:
- Session sync across channels
- Auth token handling

ACTION:
1. Copy api_wrapper.py as template
2. Modify for WebSocket protocol
3. Test with existing auth flow
```

## 📍 GO TO THESE FILES

### Need Application Logic?
```bash
code src/nexus/core/application.py   # Main app class
```

### Need Config?
```bash
code src/nexus/core/config.py        # All configuration
```

### Need Workflows?
```bash
code src/nexus/core/registry.py      # Workflow management
```

### Need Sessions?
```bash
code src/nexus/core/session.py       # Cross-channel sessions
```

### Need API Endpoints?
```bash
code src/nexus/channels/api_wrapper.py
# Look for: setup_routes() method
# Add your routes there
```

### Need CLI Commands?
```bash
code src/nexus/channels/cli_wrapper.py
# Look for: setup_commands() method
# Add your commands there
```

### Need AI Integration?
```bash
code src/nexus/channels/mcp_wrapper.py
# Look for: register_tools() method
# Add your AI tools there
```

### Need Authentication?
```bash
code src/nexus/enterprise/auth.py
# Key methods:
# - authenticate()
# - validate_token()
# - check_permission()
```

### Need Multi-Tenant?
```bash
code src/nexus/enterprise/multi_tenant.py
# Key methods:
# - create_tenant()
# - get_current_tenant()
# - isolate_data()
```

### Need Marketplace?
```bash
code src/nexus/marketplace/registry.py
# Key methods:
# - publish()
# - search()
# - install()
```

## ⚡ COPY-PASTE THESE

### Add API Endpoint:
```bash
# 1. Open file
code src/nexus/channels/api_wrapper.py

# 2. Find setup_routes()
# 3. Add this:
```
```python
self.api_channel.app.add_api_route(
    "/your-endpoint/{param}",
    self._your_handler,
    methods=["GET", "POST"]
)
```

```python
# 4. Add handler method:
async def _your_handler(self, param: str, request: Request):
    # Get tenant
    tenant_id = self._get_current_tenant() if self.multi_tenant_manager else None

    # Check auth
    user = await self._get_current_user(request) if self.auth_manager else None

    # Your logic
    result = await self._process_something(param, tenant_id, user)

    # Return JSON
    return {"status": "success", "data": result}
```

### Replace Auth Method:
```bash
# 1. Open file
code src/nexus/enterprise/auth.py

# 2. Find authenticate()
# 3. Replace with:
```
```python
async def authenticate(self, credentials: Dict[str, Any]) -> AuthToken:
    """Authenticate user and return token."""
    # Log attempt
    logger.info(f"Auth attempt for user: {credentials.get('username')}")

    # YOUR AUTH LOGIC HERE
    # Example:
    if credentials.get('username') == 'admin' and credentials.get('password') == 'secret':
        token = self._generate_token(user_id='admin')

        # Create audit log (REQUIRED)
        if self.audit_logger:
            self.audit_logger.log('auth.success', {'user': 'admin'})

        # Return AuthToken (REQUIRED FORMAT)
        return AuthToken(
            token=token,
            token_type='bearer',
            user_id='admin',
            expires_at=datetime.now() + timedelta(hours=24)
        )

    # Failed auth
    if self.audit_logger:
        self.audit_logger.log('auth.failed', credentials)
    raise AuthenticationError("Invalid credentials")
```

### Add New Channel:
```bash
# 1. Create file
touch src/nexus/channels/websocket_wrapper.py
code src/nexus/channels/websocket_wrapper.py

# 2. Paste this template:
```
```python
"""WebSocket Channel Wrapper for Nexus."""
import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

class WebSocketChannelWrapper:
    """WebSocket channel with enterprise features."""

    def __init__(
        self,
        ws_channel: Any,
        multi_tenant_manager: Optional[Any] = None,
        auth_manager: Optional[Any] = None,
        metrics_collector: Optional[Any] = None,
    ):
        self.ws_channel = ws_channel
        self.multi_tenant_manager = multi_tenant_manager
        self.auth_manager = auth_manager
        self.metrics_collector = metrics_collector
        self._setup_middleware()
        logger.info("WebSocket channel initialized")

    def _setup_middleware(self):
        """Setup enterprise middleware."""
        # Add your middleware here
        pass

    async def handle_connection(self, websocket, path):
        """Handle new WebSocket connection."""
        # Check auth
        if self.auth_manager:
            token = await self._get_token_from_ws(websocket)
            user = self.auth_manager.validate_token(token)

        # Your WebSocket logic here
        await websocket.send("Connected!")
```

```bash
# 3. Register it
code src/nexus/core/application.py
# Find __init__ method
# Add: from ..channels.websocket_wrapper import WebSocketChannelWrapper
# Add: if "websocket" in config.channels:
#          self.ws_wrapper = WebSocketChannelWrapper(...)
```

## ✅ CHECKLIST BEFORE COMMIT

```bash
# Run these commands:
[ ] grep -r "TODO" src/nexus/          # No TODOs left
[ ] python -m pytest tests/unit/        # Unit tests pass
[ ] python -m black src/nexus/          # Code formatted
[ ] grep -r "print(" src/nexus/        # No debug prints
[ ] git diff --name-only                # Review changes
```

## 🔍 QUICK LOOKUPS

### Module Dependencies
| Module | Depends On | Used By |
|--------|------------|---------|
| core/application | All SDK components | Main entry point |
| channels/* | core/*, enterprise/* | External interfaces |
| enterprise/auth | SDK auth nodes | All channels |
| enterprise/multi_tenant | SDK tenant nodes | All components |
| marketplace/registry | core/registry | Application, channels |

### Common Patterns
| Pattern | Location | Purpose |
|---------|----------|---------|
| Wrapper Pattern | channels/* | Add enterprise to SDK |
| Registry Pattern | core/registry.py | Manage collections |
| Manager Pattern | enterprise/* | Coordinate features |
| Node Integration | Throughout | Use SDK nodes |

### File Naming Conventions
| Type | Convention | Example |
|------|------------|---------|
| Wrappers | *_wrapper.py | api_wrapper.py |
| Managers | *_manager.py | auth_manager.py |
| Nodes | *_node.py | validation_node.py |
| Config | config.py | Standard name |

## 🚀 INSTANT COMMANDS

### When User Says:
```bash
"Show API endpoints"        → grep -r "add_api_route" src/nexus/
"Show CLI commands"         → grep -r "add_command" src/nexus/
"Show auth flow"           → grep -r "authenticate" src/nexus/
"Show tenant isolation"    → grep -r "tenant_id" src/nexus/
"Show workflow registry"   → cat src/nexus/core/registry.py | grep "def "
"Show all classes"         → grep -r "^class " src/nexus/
"Show all imports"         → grep -r "^from kailash" src/nexus/ | sort | uniq
"Show middleware"          → grep -r "_setup_middleware" src/nexus/
"Show error handling"      → grep -r "except " src/nexus/
"Show logging"             → grep -r "logger." src/nexus/
```

## 🎬 ACTION SEQUENCE

### Do This Every Time:
```bash
1. grep -r "function_name" src/nexus/     # Find it
2. code src/nexus/path/to/file.py         # Open it
3. # Read imports and class definition
4. # Add/modify your code
5. python -m pytest tests/unit/test_file.py  # Test it
6. git add -A && git status               # Review changes
```

### Pattern to Follow:
```python
# ALWAYS:
- Import from kailash SDK
- Check self.multi_tenant_manager
- Check self.auth_manager
- Add logger.info() calls
- Return proper types
- Handle exceptions
```

---

**RULE**: Never create from scratch. Always find similar code and copy-modify-test.
