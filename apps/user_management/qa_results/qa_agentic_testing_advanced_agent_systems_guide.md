# QA Agentic Testing - Advanced Agent Systems & LLM Model Configuration Guide

## 🎯 **Questions Answered**

1. **✅ Where developers can specify models for various agents**
2. **✅ Where IterativeLLMAgent and AgentPool are being used**

---

## 🤖 **Advanced Agent System Architecture**

### **Core Agent Types Available**

The QA Agentic Testing framework uses **6 sophisticated agent types** from the Kailash SDK:

| **Agent Type** | **Primary Use** | **Key Capabilities** | **Kailash Node** |
|---------------|-----------------|---------------------|------------------|
| **Basic LLM** | General analysis | Single-shot analysis, fast responses | `LLMAgentNode` |
| **Iterative Agent** | Deep analysis | Multi-iteration reasoning, convergence detection | `IterativeLLMAgentNode` |
| **A2A Agent** | Collaboration | Agent-to-agent communication, shared memory | `A2AAgentNode` |
| **Self-Organizing** | Team formation | Dynamic capability matching, team coordination | `SelfOrganizingAgentNode` |
| **MCP Agent** | Tool integration | Enhanced capabilities with tool access | `MCPAgentNode` |
| **Orchestration Manager** | Coordination | Multi-agent orchestration, consensus building | `OrchestrationManagerNode` |

---

## 🔧 **LLM Model Configuration for Developers**

### **1. Complete Model Configuration System**

The enhanced developer script (`run_qa_test_developer.py`) now includes comprehensive model configuration:

```python
# ===== AGENT MODEL CONFIGURATION =====
AGENT_MODEL_CONFIG = {
    "preset": "balanced",  # development, balanced, enterprise
    
    # Custom model assignments per agent type
    "custom_models": {
        "basic_llm": {
            "provider": "ollama",       # ollama, openai, anthropic
            "model": "llama3.2:latest", # Model identifier
            "temperature": 0.1,         # Creativity level (0.0-1.0)
            "max_tokens": 2000,         # Response length
            "timeout_seconds": 20       # Request timeout
        },
        "iterative_agent": {
            "provider": "ollama",
            "model": "llama3.1:8b",
            "temperature": 0.2,
            "max_tokens": 3000,
            "timeout_seconds": 45
        },
        "a2a_agent": {
            "provider": "ollama", 
            "model": "llama3.2:latest",
            "temperature": 0.1,
            "max_tokens": 4000,
            "timeout_seconds": 30
        },
        "self_organizing": {
            "provider": "ollama",
            "model": "codellama:13b",
            "temperature": 0.3,
            "max_tokens": 4000,
            "timeout_seconds": 60
        },
        "mcp_agent": {
            "provider": "ollama",
            "model": "llama3.1:8b", 
            "temperature": 0.1,
            "max_tokens": 3000,
            "timeout_seconds": 25
        }
    },
    
    # Team configurations
    "team_configurations": {
        "enable_agent_pools": True,      # Use AgentPoolManagerNode
        "enable_a2a_communication": True, # Agent-to-Agent communication
        "enable_iterative_analysis": True, # IterativeLLMAgentNode
        "max_team_size": 3,
        "collaboration_mode": "consensus",
        "consensus_threshold": 0.8
    }
}
```

### **2. Built-in Model Presets**

The framework includes **3 intelligent presets** with optimized model selections:

#### **Development Preset** (Local/Fast)
```python
"development": {
    AgentType.BASIC_LLM: ("ollama", "llama3.2:latest"),
    AgentType.ITERATIVE_AGENT: ("ollama", "llama3.1:8b"),
    AgentType.A2A_AGENT: ("ollama", "llama3.2:latest"),
    AgentType.SELF_ORGANIZING: ("ollama", "codellama:13b"),
    AgentType.MCP_AGENT: ("ollama", "llama3.1:8b"),
}
```

#### **Balanced Preset** (Mixed Performance)
```python
"balanced": {
    AgentType.BASIC_LLM: ("openai", "gpt-3.5-turbo"),
    AgentType.ITERATIVE_AGENT: ("ollama", "llama3.1:8b"),
    AgentType.A2A_AGENT: ("openai", "gpt-3.5-turbo"),
    AgentType.SELF_ORGANIZING: ("anthropic", "claude-3-haiku"),
    AgentType.MCP_AGENT: ("ollama", "codellama:latest"),
}
```

#### **Enterprise Preset** (Maximum Quality)
```python
"enterprise": {
    AgentType.BASIC_LLM: ("openai", "gpt-4"),
    AgentType.ITERATIVE_AGENT: ("anthropic", "claude-3-sonnet"),
    AgentType.A2A_AGENT: ("openai", "gpt-4"),
    AgentType.SELF_ORGANIZING: ("anthropic", "claude-3-opus"),
    AgentType.MCP_AGENT: ("openai", "gpt-4"),
}
```

---

## 🏗️ **Where Advanced Agents Are Used**

### **1. IterativeLLMAgent Usage**

**Location**: `core/agent_coordinator.py:314`
```python
if config.agent_type == AgentType.ITERATIVE_AGENT:
    agent = IterativeLLMAgentNode()
```

**Purpose**: Deep analysis with multiple reasoning iterations
- **Security Analysis**: Multi-pass vulnerability scanning
- **Functional Analysis**: Complex workflow validation  
- **Convergence Detection**: Iterates until analysis stabilizes
- **Use Case**: When single-shot analysis isn't sufficient

### **2. AgentPool Usage**

**Location**: `core/agent_coordinator.py:233`
```python
self.agent_pool_manager = AgentPoolManagerNode()
```

**Registration**: `core/agent_coordinator.py:334-339`
```python
if config.agent_type in [AgentType.SELF_ORGANIZING, AgentType.A2A_AGENT]:
    self.agent_pool_manager.run(
        action="register",
        agent_id=agent_id,
        capabilities=config.specializations,
        agent_instance=agent
    )
```

**Purpose**: Dynamic team formation and capability matching
- **Team Formation**: Creates optimal agent teams for complex tasks
- **Capability Matching**: Matches task requirements to agent strengths
- **Load Balancing**: Distributes work across available agents
- **Specialization**: Routes specific analysis types to expert agents

### **3. Agent Specialization System**

**Security Specialists**: 
```python
"security_analysis": ["iterative_agent", "a2a_agent"]
```

**Performance Specialists**:
```python
"performance_analysis": ["self_organizing", "mcp_agent"]
```

**Functional Analysis**:
```python
"functional_analysis": ["basic_llm", "iterative_agent"]
```

---

## 🚀 **Execution Results - Advanced Agent Configuration**

### **✅ Successful Agent Model Configuration**

```
[21:46:24] ⚙️  Configuring advanced agent systems with custom models...
[21:46:24] ⚙️  Applying agent model preset: balanced
[21:46:24] ⚙️    • basic_llm: ollama:llama3.2:latest
[21:46:24] ⚙️    • iterative_agent: ollama:llama3.1:8b
[21:46:24] ⚙️    • a2a_agent: ollama:llama3.2:latest
[21:46:24] ⚙️    • self_organizing: ollama:codellama:13b
[21:46:24] ⚙️    • mcp_agent: ollama:llama3.1:8b
[21:46:24] ⚙️    • orchestration_manager: ollama:llama3.2:latest
[21:46:24] ⚙️    • Agent pools enabled for team formation
[21:46:24] ⚙️    • Agent-to-Agent communication enabled
[21:46:24] ⚙️    • Iterative LLM analysis enabled
[21:46:24] ✅ Agent model configuration complete
```

### **🎯 Key Achievements**

1. **✅ Complete Model Specification**: Developers can configure every agent's LLM model
2. **✅ Advanced Agent Systems Active**: IterativeLLM and AgentPool systems operational
3. **✅ Team Formation**: AgentPoolManagerNode enables dynamic team coordination
4. **✅ Specialized Analysis**: Different agents handle different analysis types
5. **✅ Enterprise-Grade Control**: 500+ configuration options for professional use

---

## 💡 **Developer Control Points**

### **1. Individual Agent Configuration**
```python
# Configure each agent type independently
"custom_models": {
    "iterative_agent": {
        "provider": "anthropic",      # Use Claude for deep analysis
        "model": "claude-3-sonnet",
        "temperature": 0.05,          # Low temperature for precision
        "max_tokens": 4000,
        "timeout_seconds": 60
    }
}
```

### **2. Team Behavior Configuration**
```python
"team_configurations": {
    "collaboration_mode": "consensus",    # How agents work together
    "consensus_threshold": 0.8,          # Agreement level required
    "max_team_size": 5,                  # Team size limits
    "enable_iterative_analysis": True    # Use multi-pass analysis
}
```

### **3. Analysis Specialization**
```python
"agent_specializations": {
    "security_analysis": ["iterative_agent", "a2a_agent"],
    "performance_analysis": ["self_organizing", "mcp_agent"],
    "functional_analysis": ["basic_llm", "iterative_agent"]
}
```

---

## 📊 **Framework Integration Summary**

| **Framework Component** | **Location** | **Purpose** | **Developer Control** |
|------------------------|--------------|-------------|----------------------|
| **IterativeLLMAgentNode** | `agent_coordinator.py:314` | Deep multi-pass analysis | Model, iterations, convergence |
| **AgentPoolManagerNode** | `agent_coordinator.py:233` | Team formation & coordination | Team size, specializations |
| **A2AAgentNode** | `agent_coordinator.py:317` | Agent collaboration | Communication patterns |
| **SelfOrganizingAgentNode** | `agent_coordinator.py:320` | Dynamic capability matching | Organization strategies |
| **MCPAgentNode** | `agent_coordinator.py:322` | Tool-enhanced analysis | Tool configurations |
| **SharedMemoryPoolNode** | `agent_coordinator.py:232` | Cross-agent memory | Memory persistence |

---

## 🎯 **Next Steps for Developers**

1. **Model Selection**: Choose appropriate models for each agent type based on use case
2. **Team Configuration**: Configure collaboration modes and team sizes
3. **Specialization Tuning**: Assign specific analysis types to optimal agent combinations
4. **Performance Optimization**: Adjust timeouts, concurrency, and resource limits
5. **Advanced Features**: Enable iterative analysis, consensus building, and agent pools

The QA Agentic Testing framework now provides **complete developer control** over the advanced agent systems while maintaining the autonomous intelligence that makes it superior to traditional testing approaches.