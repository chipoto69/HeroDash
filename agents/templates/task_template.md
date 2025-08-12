# Task Template for Hero Command Centre Agents

## Standard Task Format

```json
{
  "task_id": "{{TASK_ID}}",
  "correlation_id": "{{CORRELATION_ID}}",
  "timestamp": "{{TIMESTAMP}}",
  "task_name": "{{TASK_NAME}}",
  "description": "{{TASK_DESCRIPTION}}",
  "priority": "{{PRIORITY_LEVEL}}",
  "deadline": "{{DEADLINE_ISO8601}}",
  
  "assignment": {
    "assigned_agent": "{{AGENT_ID}}",
    "agent_type": "{{AGENT_TYPE}}",
    "assignment_reason": "{{ASSIGNMENT_REASONING}}",
    "backup_agents": ["{{BACKUP_AGENT_1}}", "{{BACKUP_AGENT_2}}"]
  },
  
  "requirements": {
    "required_capabilities": ["{{CAPABILITY_1}}", "{{CAPABILITY_2}}"],
    "resource_limits": {
      "max_duration_ms": {{MAX_DURATION}},
      "max_memory_mb": {{MAX_MEMORY}},
      "max_cpu_percentage": {{MAX_CPU}}
    },
    "dependencies": ["{{DEPENDENCY_TASK_1}}", "{{DEPENDENCY_TASK_2}}"]
  },
  
  "inputs": {
    "data": {{INPUT_DATA}},
    "context": {{TASK_CONTEXT}},
    "parameters": {{TASK_PARAMETERS}}
  },
  
  "execution": {
    "status": "{{STATUS}}",
    "started_at": "{{START_TIMESTAMP}}",
    "progress_percentage": {{PROGRESS}},
    "current_step": "{{CURRENT_STEP}}",
    "estimated_completion": "{{ETA_TIMESTAMP}}"
  },
  
  "outputs": {
    "result": {{TASK_RESULT}},
    "artifacts": ["{{ARTIFACT_1}}", "{{ARTIFACT_2}}"],
    "metrics": {{PERFORMANCE_METRICS}},
    "completed_at": "{{COMPLETION_TIMESTAMP}}"
  },
  
  "quality": {
    "success_criteria": {{SUCCESS_CRITERIA}},
    "validation_rules": {{VALIDATION_RULES}},
    "quality_score": {{QUALITY_SCORE}},
    "review_required": {{REVIEW_BOOLEAN}}
  },
  
  "error_handling": {
    "retry_policy": {
      "max_retries": {{MAX_RETRIES}},
      "backoff_strategy": "{{BACKOFF_STRATEGY}}",
      "retry_conditions": ["{{RETRY_CONDITION_1}}"]
    },
    "fallback_options": ["{{FALLBACK_1}}", "{{FALLBACK_2}}"],
    "escalation_rules": {{ESCALATION_RULES}}
  },
  
  "tracing": {
    "langsmith_trace_id": "{{LANGSMITH_TRACE_ID}}",
    "parent_workflow_id": "{{PARENT_WORKFLOW_ID}}",
    "tags": ["{{TAG_1}}", "{{TAG_2}}"],
    "metadata": {{TRACE_METADATA}}
  }
}
```

## Task Status Values

### Valid Status States
- `pending` - Task created but not yet assigned
- `assigned` - Task assigned to agent but not started
- `in_progress` - Task currently being executed
- `paused` - Task execution temporarily halted
- `completed` - Task successfully completed
- `failed` - Task execution failed
- `cancelled` - Task was cancelled before completion
- `timeout` - Task exceeded maximum duration
- `escalated` - Task escalated to different agent/human

### Status Transition Rules
```
pending → assigned → in_progress → {completed|failed|paused}
pending → cancelled
assigned → cancelled
in_progress → {paused → in_progress}
failed → {assigned|escalated} (retry/escalation)
any_status → cancelled (emergency stop)
```

## Priority Levels

### Priority Values
- `URGENT` (4) - Immediate execution required, interrupt other tasks
- `HIGH` (3) - High priority, fast-track through queue
- `NORMAL` (2) - Standard priority, normal queue processing
- `LOW` (1) - Background task, execute when resources available

### Priority Assignment Guidelines
- **URGENT**: System failures, security incidents, critical user requests
- **HIGH**: Important workflows, time-sensitive operations, escalated tasks
- **NORMAL**: Regular operations, routine maintenance, standard requests
- **LOW**: Optimization tasks, cleanup operations, background analysis

## Capability Requirements

### Standard Capabilities
```yaml
# Coordination Capabilities
task_distribution: "Ability to distribute tasks to other agents"
workflow_orchestration: "Ability to coordinate multi-step workflows"
load_balancing: "Ability to balance workload across agents"
agent_coordination: "Ability to coordinate with other agents"

# Knowledge Capabilities
knowledge_graph_management: "Ability to manage knowledge graphs"
semantic_search: "Ability to perform semantic searches"
pattern_recognition: "Ability to recognize patterns in data"
insight_generation: "Ability to generate insights from data"

# Technical Capabilities
data_processing: "Ability to process and transform data"
api_integration: "Ability to integrate with external APIs"
file_operations: "Ability to read/write files"
database_operations: "Ability to query databases"

# Communication Capabilities
nats_messaging: "Ability to communicate via NATS"
http_requests: "Ability to make HTTP requests"
real_time_updates: "Ability to provide real-time updates"
alert_generation: "Ability to generate alerts"
```

## Input/Output Formats

### Standard Input Format
```json
{
  "data": {
    "primary": {{PRIMARY_DATA}},
    "secondary": {{SECONDARY_DATA}},
    "reference": {{REFERENCE_DATA}}
  },
  "context": {
    "session_id": "{{SESSION_ID}}",
    "user_context": {{USER_CONTEXT}},
    "workflow_context": {{WORKFLOW_CONTEXT}},
    "historical_context": {{HISTORICAL_CONTEXT}}
  },
  "parameters": {
    "configuration": {{CONFIG_PARAMS}},
    "preferences": {{USER_PREFERENCES}},
    "constraints": {{EXECUTION_CONSTRAINTS}}
  }
}
```

### Standard Output Format
```json
{
  "result": {
    "status": "{{EXECUTION_STATUS}}",
    "data": {{RESULT_DATA}},
    "summary": "{{RESULT_SUMMARY}}",
    "confidence_score": {{CONFIDENCE_SCORE}}
  },
  "artifacts": [
    {
      "type": "{{ARTIFACT_TYPE}}",
      "location": "{{ARTIFACT_LOCATION}}",
      "description": "{{ARTIFACT_DESCRIPTION}}"
    }
  ],
  "metrics": {
    "execution_time_ms": {{EXECUTION_TIME}},
    "resource_usage": {{RESOURCE_USAGE}},
    "quality_metrics": {{QUALITY_METRICS}},
    "performance_score": {{PERFORMANCE_SCORE}}
  },
  "recommendations": [
    {
      "type": "{{RECOMMENDATION_TYPE}}",
      "priority": "{{RECOMMENDATION_PRIORITY}}",
      "description": "{{RECOMMENDATION_DESCRIPTION}}",
      "actionable": {{IS_ACTIONABLE}}
    }
  ]
}
```

## Error Handling Patterns

### Standard Error Format
```json
{
  "error": {
    "code": "{{ERROR_CODE}}",
    "type": "{{ERROR_TYPE}}",
    "message": "{{ERROR_MESSAGE}}",
    "details": {{ERROR_DETAILS}},
    "timestamp": "{{ERROR_TIMESTAMP}}",
    "context": {{ERROR_CONTEXT}}
  },
  "recovery": {
    "attempted_solutions": [
      {
        "solution": "{{SOLUTION_DESCRIPTION}}",
        "success": {{SOLUTION_SUCCESS}},
        "timestamp": "{{SOLUTION_TIMESTAMP}}"
      }
    ],
    "recommended_actions": ["{{ACTION_1}}", "{{ACTION_2}}"],
    "escalation_required": {{ESCALATION_BOOLEAN}},
    "retry_possible": {{RETRY_BOOLEAN}}
  },
  "impact": {
    "severity": "{{SEVERITY_LEVEL}}",
    "affected_components": ["{{COMPONENT_1}}", "{{COMPONENT_2}}"],
    "downstream_effects": ["{{EFFECT_1}}", "{{EFFECT_2}}"],
    "user_impact": "{{USER_IMPACT_DESCRIPTION}}"
  }
}
```

### Common Error Types
- `CAPABILITY_MISMATCH` - Agent lacks required capabilities
- `RESOURCE_EXHAUSTION` - Insufficient resources for execution
- `TIMEOUT` - Task exceeded maximum duration
- `DEPENDENCY_FAILURE` - Required dependency failed
- `VALIDATION_ERROR` - Input validation failed
- `SYSTEM_ERROR` - System-level error occurred
- `COMMUNICATION_ERROR` - Inter-agent communication failed
- `DATA_ERROR` - Data corruption or invalid format

## Validation Rules

### Task Validation Checklist
```yaml
required_fields:
  - task_id
  - task_name
  - description
  - priority
  - required_capabilities

field_validation:
  task_id: "UUID format"
  priority: "Must be URGENT, HIGH, NORMAL, or LOW"
  deadline: "Must be valid ISO8601 timestamp"
  required_capabilities: "Must be array of valid capability strings"

business_rules:
  - "Deadline must be in the future"
  - "Required capabilities must exist in capability registry"
  - "Resource limits must be positive integers"
  - "Dependencies must reference existing task IDs"

security_validation:
  - "No sensitive data in task description"
  - "Agent assignment follows access control rules"
  - "Input data conforms to security policies"
```

## Usage Examples

### Simple Task Creation
```json
{
  "task_id": "task_001",
  "task_name": "system_health_check",
  "description": "Perform comprehensive system health assessment",
  "priority": "NORMAL",
  "required_capabilities": ["system_monitoring", "health_assessment"],
  "inputs": {
    "data": {
      "target_systems": ["hero_dashboard", "nats_server", "knowledge_graph"]
    }
  }
}
```

### Complex Workflow Task
```json
{
  "task_id": "workflow_001",
  "task_name": "knowledge_consolidation_workflow",
  "description": "Multi-step knowledge consolidation and insight generation",
  "priority": "HIGH",
  "required_capabilities": ["workflow_orchestration", "knowledge_graph_management"],
  "dependencies": ["data_collection_001", "preprocessing_001"],
  "inputs": {
    "data": {
      "source_episodes": ["episode_001", "episode_002"],
      "consolidation_rules": "standard_consolidation_v2"
    },
    "parameters": {
      "quality_threshold": 0.8,
      "max_processing_time": 300000
    }
  }
}
```