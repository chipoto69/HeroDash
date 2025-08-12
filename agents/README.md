# Hero Command Centre - AI Agent System

## Overview

This directory contains the complete AI agent system for the Hero Command Centre, including comprehensive system prompts, configurations, and templates for implementing a production-ready multi-agent collaboration framework.

## Directory Structure

```
agents/
├── sysprompts/                     # System prompts for each agent type
│   ├── task_orchestrator_sysprompt.md
│   └── knowledge_integration_sysprompt.md
├── configs/                        # Shared configuration files
│   ├── agent_capabilities.yaml
│   ├── nats_subjects.yaml
│   └── langsmith_config.yaml
├── templates/                      # Reusable prompt templates
│   ├── task_template.md
│   ├── knowledge_template.md
│   └── interaction_template.md
├── test_agent_integration.py       # Integration test suite
└── README.md                       # This file
```

## Agent Types

### 1. Task Orchestrator Agent

**Purpose**: Central coordination hub for multi-agent task distribution and workflow orchestration.

**Key Responsibilities**:
- Intelligent task assignment based on agent capabilities and load
- Multi-step workflow coordination using LangGraph patterns
- Load balancing and resource optimization
- Progress monitoring and failure handling
- Real-time priority management

**System Prompt**: `sysprompts/task_orchestrator_sysprompt.md`

### 2. Knowledge Integration Agent

**Purpose**: Cognitive memory and intelligence hub for the multi-agent ecosystem.

**Key Responsibilities**:
- Temporal knowledge graph management using Graphiti
- Semantic search and pattern recognition
- Context preservation across agent interactions
- Insight generation and memory consolidation
- Multi-modal knowledge synthesis

**System Prompt**: `sysprompts/knowledge_integration_sysprompt.md`

## Configuration Files

### Agent Capabilities (`configs/agent_capabilities.yaml`)

Defines:
- Agent specifications and performance requirements
- Capability categories and compatibility matrix
- Performance tiers and scaling policies
- Integration specifications for LangSmith and NATS

### NATS Subjects (`configs/nats_subjects.yaml`)

Defines:
- Complete subject hierarchy for agent communication
- Message routing rules and wildcard patterns
- Stream configurations and consumer groups
- Security permissions and environment overrides

### LangSmith Configuration (`configs/langsmith_config.yaml`)

Defines:
- Tracing configuration for all agent operations
- Project structure and metadata standards
- Sampling strategies and performance monitoring
- Export configurations and retention policies

## Templates

### Task Template (`templates/task_template.md`)

Standardized format for:
- Task definition and assignment
- Resource requirements and constraints
- Quality assurance and validation rules
- Error handling and retry policies

### Knowledge Template (`templates/knowledge_template.md`)

Standardized format for:
- Knowledge entries and episodes
- Entity relationships and facts
- Pattern recognition and insights
- Context preservation and lineage

### Interaction Template (`templates/interaction_template.md`)

Standardized format for:
- Agent-to-agent communication
- Conversation management and context
- Quality assurance and error handling
- Communication protocols and patterns

## Integration with Hero Framework

### Existing Components

The agent system integrates seamlessly with:

- **Agent Coordinator** (`monitors/agent_coordinator.py`): Task orchestration and agent management
- **Chimera Bridge** (`monitors/chimera_bridge.py`): Integration with Frontline/Chimera framework
- **LangSmith Tracer** (`monitors/langsmith_tracer.py`): Observability and workflow tracing
- **Hero Dashboard** (`hero_core_optimized_fixed.sh`): Real-time monitoring and control

### Communication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    LangSmith Studio (Observability)         │
└─────────────────────────────────────────────────────────────┘
                              ↑
                         LangGraph Tracing
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Hero Command Centre Dashboard                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Task        │  │  Knowledge   │  │  Monitoring  │     │
│  │  Orchestrator│  │  Integration │  │  Agents      │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    NATS JetStream Bus                       │
│ Streams: Tasks, Results, Events, Control | KV Store | OS    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  UI Agent   │ Embedder  │ Retriever │ Memory  │ Orchestrator│
│             │ (Chimera) │ (Chimera) │(Chimera)│  (External) │
└─────────────────────────────────────────────────────────────┘
```

## Testing

### Integration Test Suite

Run the comprehensive test suite:

```bash
# Run all tests
python3 agents/test_agent_integration.py --test all

# Run specific test categories
python3 agents/test_agent_integration.py --test config      # Configuration validation
python3 agents/test_agent_integration.py --test prompts    # System prompt structure
python3 agents/test_agent_integration.py --test templates  # Template validation
python3 agents/test_agent_integration.py --test nats       # NATS compatibility
python3 agents/test_agent_integration.py --test integration # Framework integration
python3 agents/test_agent_integration.py --test workflow   # Workflow simulation
```

### Test Coverage

The test suite validates:
- ✅ Configuration file structure and completeness
- ✅ System prompt content and organization
- ✅ Template format and variable usage
- ✅ NATS subject pattern compatibility
- ✅ Hero framework integration points
- ✅ End-to-end workflow simulation

## Implementation Guide

### Step 1: Environment Setup

1. **Install Dependencies**:
   ```bash
   pip install langsmith langchain langgraph psutil pyyaml
   pip install nats-py  # For NATS messaging
   ```

2. **Configure Environment Variables**:
   ```bash
   export LANGSMITH_API_KEY="your_api_key"
   export LANGSMITH_PROJECT="hero-command-centre"
   export NATS_URL="nats://localhost:4222"
   ```

### Step 2: Agent Deployment

1. **Initialize Agent Framework**:
   ```python
   from agents.configs import agent_capabilities
   from monitors.agent_coordinator import get_coordinator
   
   # Load configurations
   coordinator = get_coordinator()
   
   # Register agents based on capabilities config
   for agent_name, config in agent_capabilities['agents'].items():
       coordinator.register_agent(
           agent_name,
           config['type'],
           config['capabilities'],
           config['framework']
       )
   ```

2. **Deploy System Prompts**:
   - Use the system prompts as templates for your AI agent implementation
   - Customize agent behavior by modifying prompt sections
   - Ensure consistent messaging patterns using templates

### Step 3: Integration Testing

1. **Run Integration Tests**:
   ```bash
   python3 agents/test_agent_integration.py
   ```

2. **Validate Real-time Integration**:
   ```bash
   # Start Hero Dashboard
   ./launch_hero_optimized_fixed.sh
   
   # Monitor agent activities in real-time
   python3 monitors/agent_coordinator.py --status
   python3 monitors/chimera_bridge.py --status
   ```

### Step 4: Production Deployment

1. **Scale Configuration**:
   - Adjust performance requirements in `agent_capabilities.yaml`
   - Configure production NATS clusters
   - Set up LangSmith project for production tracing

2. **Monitoring Setup**:
   - Enable all Hero Dashboard monitoring sections
   - Configure alerting thresholds
   - Set up log aggregation and analysis

## Best Practices

### System Prompt Customization

1. **Maintain Structure**: Keep the core sections while customizing content
2. **Context Awareness**: Update capability definitions based on your specific use case
3. **Performance Tuning**: Adjust performance metrics and thresholds
4. **Security Considerations**: Review and enhance security sections

### Configuration Management

1. **Environment Separation**: Use different configs for dev/staging/prod
2. **Version Control**: Track configuration changes carefully
3. **Validation**: Always run tests after configuration changes
4. **Documentation**: Document any customizations made

### Template Usage

1. **Consistent Formatting**: Use templates for all agent interactions
2. **Variable Substitution**: Implement proper template variable handling
3. **Validation**: Validate messages against template schemas
4. **Evolution**: Update templates as requirements change

## Troubleshooting

### Common Issues

1. **Agent Registration Failures**:
   - Check capability definitions in `agent_capabilities.yaml`
   - Verify NATS connectivity
   - Review agent coordinator logs

2. **Communication Errors**:
   - Validate NATS subject patterns
   - Check message format against templates
   - Verify agent permissions

3. **Performance Issues**:
   - Review performance tier configurations
   - Check resource limits and scaling policies
   - Monitor LangSmith traces for bottlenecks

### Debug Commands

```bash
# Check agent coordinator status
python3 monitors/agent_coordinator.py --status

# Test NATS connectivity
python3 monitors/chimera_bridge.py --nats-test

# View LangSmith traces
python3 monitors/langsmith_tracer.py --stats

# Run diagnostic tests
python3 agents/test_agent_integration.py --test integration --verbose
```

## Future Enhancements

### Planned Features

1. **Dynamic Agent Scaling**: Automatic agent deployment based on load
2. **Advanced Pattern Recognition**: Machine learning for workflow optimization
3. **Multi-Framework Support**: Support for additional agent frameworks
4. **Visual Workflow Designer**: GUI for creating agent workflows

### Extension Points

1. **Custom Agent Types**: Add new agent types with specialized capabilities
2. **Integration Plugins**: Extend integration with external systems
3. **Custom Templates**: Create domain-specific message templates
4. **Advanced Analytics**: Enhanced performance and behavior analysis

## Contributing

When contributing to the agent system:

1. **Follow Templates**: Use existing templates for consistency
2. **Test Integration**: Always run the full test suite
3. **Document Changes**: Update configuration documentation
4. **Performance Impact**: Consider performance implications of changes

## Support

For issues and questions:

1. **Review Logs**: Check Hero Dashboard and agent coordinator logs
2. **Run Tests**: Use the integration test suite for diagnosis
3. **Check Configuration**: Validate all configuration files
4. **Monitor Performance**: Use LangSmith and Hero Dashboard for insights

---

**Note**: This agent system is designed to work seamlessly with the existing Hero Command Centre infrastructure. All components are tested and validated for production deployment.