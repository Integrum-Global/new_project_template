# QA Agentic Testing - Agent Usage Patterns & Decision Logic

## 🤖 **When Are IterativeLLMAgents and AgentPool Used?**

### **IterativeLLMAgent Usage - Deep Analysis Scenarios**

**Location**: `core/agent_coordinator.py:457-479`

```python
if config.agent_type == AgentType.ITERATIVE_AGENT:
    result = agent.run(
        provider=config.provider,
        model=config.model,
        messages=[{"role": "user", "content": enhanced_prompt}],
        max_iterations=3,
        convergence_threshold=0.8,
        max_tokens=config.max_tokens,
        temperature=config.temperature
    )
```

**🎯 Automatically Used For:**
1. **Security Analysis** - Complex vulnerability assessments requiring multiple iterations
2. **Functional Analysis** - Deep business logic validation needing iterative reasoning
3. **Complex Scenario Validation** - When single-shot analysis isn't sufficient
4. **Convergence Detection** - Iterates until analysis stabilizes (convergence_threshold=0.8)

**📊 Performance Metrics Tracked:**
- `iteration_count`: Number of analysis iterations performed
- `convergence_time`: Time taken to reach stable analysis
- `confidence_score`: Final confidence after iterations

---

### **AgentPool (AgentPoolManagerNode) Usage - Team Coordination**

**Location**: `core/agent_coordinator.py:233` (Initialization)
```python
self.agent_pool_manager = AgentPoolManagerNode()
```

**Location**: `core/agent_coordinator.py:334-339` (Agent Registration)
```python
if config.agent_type in [AgentType.SELF_ORGANIZING, AgentType.A2A_AGENT]:
    self.agent_pool_manager.run(
        action="register",
        agent_id=agent_id,
        capabilities=config.specializations,
        agent_instance=agent
    )
```

**🎯 Automatically Used For:**
1. **Team Formation** - Creates optimal agent teams for complex tasks
2. **Capability Matching** - Routes tasks to agents with appropriate specializations
3. **Load Balancing** - Distributes work across available agents
4. **Collaborative Analysis** - Coordinates multi-agent consensus building

---

## 🧠 **Who Decides What Agent To Use?**

### **1. Pre-Configured Agent Specializations**

**Location**: `core/agent_coordinator.py:252-290`

```python
# Default agent configurations with specializations
self.agent_configs["iterative_analyzer"] = AgentConfig(
    agent_type=AgentType.ITERATIVE_AGENT,
    specializations=[AnalysisType.SECURITY, AnalysisType.FUNCTIONAL],
    priority=3,
    collaboration_mode="iterative"
)

self.agent_configs["a2a_collaborator"] = AgentConfig(
    agent_type=AgentType.A2A_AGENT,
    specializations=[AnalysisType.CONSENSUS, AnalysisType.PERFORMANCE],
    priority=2,
    collaboration_mode="collaborative"
)

self.agent_configs["self_organizing_team"] = AgentConfig(
    agent_type=AgentType.SELF_ORGANIZING,
    specializations=[AnalysisType.PERFORMANCE, AnalysisType.INTEGRATION],
    priority=2,
    collaboration_mode="team_based"
)
```

### **2. Dynamic Agent Selection Logic**

**Location**: `core/agent_coordinator.py:358-370`

```python
def get_specialized_agents(self, analysis_type: AnalysisType) -> List[str]:
    """Get agents specialized for a specific analysis type."""
    specialized_agents = []
    for agent_id, config in self.agent_configs.items():
        if config.enabled and analysis_type in config.specializations:
            specialized_agents.append(agent_id)
    
    # Sort by priority (higher priority first)
    specialized_agents.sort(
        key=lambda aid: self.agent_configs[aid].priority, 
        reverse=True
    )
    return specialized_agents
```

### **3. Analysis Type to Agent Mapping**

| **Analysis Type** | **Primary Agent** | **Secondary Agent** | **Reasoning** |
|------------------|------------------|-------------------|---------------|
| **Security** | IterativeLLMAgent | A2AAgent | Security needs deep, multi-pass analysis |
| **Performance** | SelfOrganizingAgent | MCPAgent | Performance requires team optimization |
| **Functional** | IterativeLLMAgent | BasicLLM | Functional testing needs deep validation |
| **Consensus** | A2AAgent | OrchestrationManager | Consensus requires collaboration |

---

## 🔄 **Workflow Decision Tree**

```
Test Scenario Generated
    ↓
Analysis Type Determined (Security/Performance/Functional/Usability)
    ↓
Agent Selection Logic:
    
    IF analysis_type == SECURITY:
        → Use IterativeLLMAgent (deep analysis)
        → Register in AgentPool for collaboration
        → Run 3 iterations with convergence detection
    
    IF analysis_type == PERFORMANCE:
        → Use SelfOrganizingAgent (team formation)
        → Register in AgentPool with performance capabilities
        → Form optimal team for performance analysis
    
    IF analysis_type == FUNCTIONAL:
        → Use IterativeLLMAgent (thorough validation)
        → Run iterative business logic analysis
    
    IF complex_scenario OR consensus_needed:
        → Use A2AAgent (collaboration)
        → Enable shared memory pool
        → Coordinate multi-agent analysis
```

---

## ⚙️ **Developer Control Points**

### **1. Agent Model Configuration**
```python
AGENT_MODEL_CONFIG = {
    "custom_models": {
        "iterative_agent": {
            "provider": "ollama",
            "model": "llama3.1:8b",
            "temperature": 0.2,      # Higher for creative iteration
            "max_tokens": 3000,      # More tokens for deep analysis
            "timeout_seconds": 45    # Longer timeout for iterations
        },
        "self_organizing": {
            "provider": "ollama",
            "model": "codellama:13b",
            "temperature": 0.3,      # Higher for team creativity
            "team_size": 3           # Optimal team size
        }
    }
}
```

### **2. Team Configuration Control**
```python
"team_configurations": {
    "enable_agent_pools": True,         # Enable AgentPoolManagerNode
    "enable_a2a_communication": True,   # Enable Agent-to-Agent
    "enable_iterative_analysis": True,  # Enable IterativeLLMAgent
    "max_team_size": 3,
    "collaboration_mode": "consensus",
    "consensus_threshold": 0.8
}
```

---

## 📊 **Execution Pattern Analysis**

### **Observed Agent Usage in Real Testing:**

```
[21:52:44] ⚙️  Configuring advanced agent systems with custom models...
[21:52:44] ⚙️    • iterative_agent: ollama:llama3.1:8b      ← For deep analysis
[21:52:44] ⚙️    • a2a_agent: ollama:llama3.2:latest        ← For collaboration  
[21:52:44] ⚙️    • self_organizing: ollama:codellama:13b     ← For team formation
[21:52:44] ⚙️    • Agent pools enabled for team formation   ← AgentPoolManagerNode active
[21:52:44] ⚙️    • Agent-to-Agent communication enabled     ← A2A coordination active
[21:52:44] ⚙️    • Iterative LLM analysis enabled          ← Multi-iteration analysis active
```

### **Agent Specialization Matrix:**

| **Scenario Type** | **Agent Used** | **Why This Agent** | **Iterations/Team Size** |
|------------------|----------------|-------------------|-------------------------|
| **Security Testing** | IterativeLLMAgent | Needs deep vulnerability analysis | 3 iterations, convergence=0.8 |
| **Performance Testing** | SelfOrganizingAgent | Requires team optimization | Team size=3, dynamic formation |
| **Functional Testing** | IterativeLLMAgent | Business logic validation | 3 iterations, thorough validation |
| **Usability Testing** | A2AAgent | Benefits from collaborative insights | Shared memory, consensus building |

---

## 🎯 **Key Insights**

### **1. Automatic Agent Selection**
- **The framework automatically decides** which agents to use based on analysis type
- **No manual intervention required** - agents are selected by specialization matching
- **Priority-based selection** ensures optimal agent assignment

### **2. Multi-Agent Coordination**
- **AgentPoolManagerNode manages team formation** for complex tasks
- **A2AAgentNode enables collaboration** between different agent types  
- **IterativeLLMAgentNode provides deep analysis** through multiple iterations

### **3. Dynamic Adaptation**
- **Agents adapt their behavior** based on task complexity
- **Team size and composition adjust** based on analysis requirements
- **Convergence detection** ensures analysis quality before completion

### **4. Developer Override Capability**
- **Complete model control** for each agent type
- **Team behavior configuration** through team_configurations
- **Analysis specialization tuning** through agent_specializations

The QA Agentic Testing framework uses **intelligent agent orchestration** where the system automatically selects and coordinates the most appropriate agents based on the analysis type and task complexity, while still providing developers complete control over the underlying models and behavior patterns.