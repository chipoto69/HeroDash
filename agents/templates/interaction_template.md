# Agent Interaction Template for Hero Command Centre

## Standard Interaction Message Format

```json
{
  "message_id": "{{MESSAGE_ID}}",
  "correlation_id": "{{CORRELATION_ID}}",
  "conversation_id": "{{CONVERSATION_ID}}",
  "timestamp": "{{TIMESTAMP}}",
  "message_type": "{{MESSAGE_TYPE}}",
  
  "communication": {
    "sender": {
      "agent_id": "{{SENDER_AGENT_ID}}",
      "agent_type": "{{SENDER_AGENT_TYPE}}",
      "agent_name": "{{SENDER_AGENT_NAME}}",
      "framework": "{{SENDER_FRAMEWORK}}"
    },
    "recipient": {
      "agent_id": "{{RECIPIENT_AGENT_ID}}",
      "agent_type": "{{RECIPIENT_AGENT_TYPE}}",
      "agent_name": "{{RECIPIENT_AGENT_NAME}}",
      "framework": "{{RECIPIENT_FRAMEWORK}}"
    },
    "routing": {
      "nats_subject": "{{NATS_SUBJECT}}",
      "reply_subject": "{{REPLY_SUBJECT}}",
      "delivery_method": "{{DELIVERY_METHOD}}",
      "priority": "{{MESSAGE_PRIORITY}}"
    }
  },
  
  "content": {
    "intent": "{{COMMUNICATION_INTENT}}",
    "subject": "{{MESSAGE_SUBJECT}}",
    "body": "{{MESSAGE_BODY}}",
    "data": {{MESSAGE_DATA}},
    "attachments": [{{ATTACHMENTS}}],
    "format": "{{CONTENT_FORMAT}}"
  },
  
  "context": {
    "conversation_context": {{CONVERSATION_CONTEXT}},
    "task_context": {{TASK_CONTEXT}},
    "workflow_context": {{WORKFLOW_CONTEXT}},
    "session_context": {{SESSION_CONTEXT}}
  },
  
  "interaction_metadata": {
    "interaction_type": "{{INTERACTION_TYPE}}",
    "collaboration_pattern": "{{COLLABORATION_PATTERN}}",
    "decision_point": {{IS_DECISION_POINT}},
    "requires_response": {{REQUIRES_RESPONSE}},
    "response_deadline": "{{RESPONSE_DEADLINE}}",
    "escalation_rules": {{ESCALATION_RULES}}
  },
  
  "quality_assurance": {
    "validation_status": "{{VALIDATION_STATUS}}",
    "confidence_level": {{CONFIDENCE_LEVEL}},
    "clarity_score": {{CLARITY_SCORE}},
    "completeness_score": {{COMPLETENESS_SCORE}},
    "review_required": {{REVIEW_REQUIRED}}
  },
  
  "tracing": {
    "langsmith_trace_id": "{{LANGSMITH_TRACE_ID}}",
    "parent_trace_id": "{{PARENT_TRACE_ID}}",
    "span_id": "{{SPAN_ID}}",
    "trace_tags": ["{{TAG_1}}", "{{TAG_2}}"],
    "trace_metadata": {{TRACE_METADATA}}
  },
  
  "security": {
    "classification": "{{CLASSIFICATION_LEVEL}}",
    "access_control": {{ACCESS_CONTROL_RULES}},
    "encryption_required": {{ENCRYPTION_REQUIRED}},
    "audit_required": {{AUDIT_REQUIRED}}
  }
}
```

## Message Types

### Communication Types
```yaml
# Task Management Messages
task_assignment:
  description: "Assign a task to an agent"
  required_fields: ["task_id", "assignment_details", "deadline"]
  expected_response: "task_acknowledgment"

task_update:
  description: "Update on task progress"
  required_fields: ["task_id", "progress_percentage", "status"]
  expected_response: "acknowledgment"

task_completion:
  description: "Notification of task completion"
  required_fields: ["task_id", "results", "metrics"]
  expected_response: "completion_acknowledgment"

# Coordination Messages
capability_inquiry:
  description: "Request information about agent capabilities"
  required_fields: ["capability_types", "context"]
  expected_response: "capability_response"

status_request:
  description: "Request current status from agent"
  required_fields: ["status_types"]
  expected_response: "status_response"

collaboration_request:
  description: "Request collaboration on a task or workflow"
  required_fields: ["collaboration_type", "scope", "timeline"]
  expected_response: "collaboration_response"

# Knowledge Messages
knowledge_query:
  description: "Request knowledge or context"
  required_fields: ["query", "context_type", "urgency"]
  expected_response: "knowledge_response"

insight_sharing:
  description: "Share generated insights"
  required_fields: ["insight_type", "insight_data", "confidence"]
  expected_response: "insight_acknowledgment"

pattern_alert:
  description: "Alert about detected pattern"
  required_fields: ["pattern_type", "significance", "evidence"]
  expected_response: "pattern_acknowledgment"

# System Messages
health_check:
  description: "Check agent health and availability"
  required_fields: ["check_type"]
  expected_response: "health_response"

error_notification:
  description: "Notify about errors or failures"
  required_fields: ["error_type", "error_details", "severity"]
  expected_response: "error_acknowledgment"

shutdown_notification:
  description: "Notify about planned shutdown"
  required_fields: ["shutdown_time", "reason", "affected_operations"]
  expected_response: "shutdown_acknowledgment"
```

## Interaction Patterns

### Request-Response Pattern
```json
{
  "pattern_type": "request_response",
  "initiator": "{{REQUESTING_AGENT}}",
  "responder": "{{RESPONDING_AGENT}}",
  "workflow": {
    "step_1": {
      "action": "send_request",
      "message_type": "{{REQUEST_TYPE}}",
      "timeout": "{{RESPONSE_TIMEOUT}}",
      "retry_policy": {{RETRY_POLICY}}
    },
    "step_2": {
      "action": "process_request",
      "processing_time": "{{EXPECTED_PROCESSING_TIME}}",
      "validation_required": {{VALIDATION_REQUIRED}}
    },
    "step_3": {
      "action": "send_response",
      "message_type": "{{RESPONSE_TYPE}}",
      "include_metadata": {{INCLUDE_METADATA}}
    },
    "step_4": {
      "action": "acknowledge_response",
      "message_type": "acknowledgment",
      "optional": {{ACKNOWLEDGMENT_OPTIONAL}}
    }
  }
}
```

### Publish-Subscribe Pattern
```json
{
  "pattern_type": "publish_subscribe",
  "publisher": "{{PUBLISHING_AGENT}}",
  "subscribers": ["{{SUBSCRIBER_1}}", "{{SUBSCRIBER_2}}"],
  "workflow": {
    "step_1": {
      "action": "publish_event",
      "message_type": "{{EVENT_TYPE}}",
      "broadcast_scope": "{{BROADCAST_SCOPE}}"
    },
    "step_2": {
      "action": "receive_event",
      "filtering_rules": {{FILTERING_RULES}},
      "processing_async": {{ASYNC_PROCESSING}}
    },
    "step_3": {
      "action": "process_event",
      "processing_type": "{{PROCESSING_TYPE}}",
      "result_publishing": {{PUBLISH_RESULTS}}
    }
  }
}
```

### Delegation Pattern
```json
{
  "pattern_type": "task_delegation",
  "delegator": "{{DELEGATING_AGENT}}",
  "delegate": "{{RECEIVING_AGENT}}",
  "workflow": {
    "step_1": {
      "action": "assess_delegation_need",
      "criteria": {{DELEGATION_CRITERIA}},
      "decision_factors": {{DECISION_FACTORS}}
    },
    "step_2": {
      "action": "select_delegate",
      "selection_algorithm": "{{SELECTION_METHOD}}",
      "capability_matching": {{CAPABILITY_REQUIREMENTS}}
    },
    "step_3": {
      "action": "delegate_task",
      "message_type": "task_assignment",
      "delegation_context": {{DELEGATION_CONTEXT}}
    },
    "step_4": {
      "action": "monitor_progress",
      "monitoring_frequency": "{{MONITORING_FREQUENCY}}",
      "escalation_triggers": {{ESCALATION_TRIGGERS}}
    },
    "step_5": {
      "action": "receive_results",
      "message_type": "task_completion",
      "validation_required": {{RESULT_VALIDATION}}
    }
  }
}
```

## Conversation Management

### Conversation Context
```json
{
  "conversation_id": "{{CONVERSATION_ID}}",
  "conversation_type": "{{CONVERSATION_TYPE}}",
  "participants": [
    {
      "agent_id": "{{AGENT_ID}}",
      "role": "{{CONVERSATION_ROLE}}",
      "join_time": "{{JOIN_TIMESTAMP}}",
      "active": {{IS_ACTIVE}}
    }
  ],
  "conversation_state": {
    "current_phase": "{{CONVERSATION_PHASE}}",
    "decision_points": [{{DECISION_POINTS}}],
    "action_items": [{{ACTION_ITEMS}}],
    "consensus_status": "{{CONSENSUS_STATUS}}"
  },
  "conversation_history": [
    {
      "message_id": "{{MESSAGE_ID}}",
      "timestamp": "{{TIMESTAMP}}",
      "sender": "{{SENDER_ID}}",
      "message_summary": "{{MESSAGE_SUMMARY}}"
    }
  ],
  "conversation_metrics": {
    "duration": "{{CONVERSATION_DURATION}}",
    "message_count": {{MESSAGE_COUNT}},
    "participation_rate": {{PARTICIPATION_RATE}},
    "resolution_status": "{{RESOLUTION_STATUS}}"
  }
}
```

### Context Preservation
```json
{
  "context_id": "{{CONTEXT_ID}}",
  "context_type": "{{CONTEXT_TYPE}}",
  "scope": "{{CONTEXT_SCOPE}}",
  "preservation_rules": {
    "duration": "{{PRESERVATION_DURATION}}",
    "triggers": [{{PRESERVATION_TRIGGERS}}],
    "sharing_rules": {{SHARING_RULES}},
    "cleanup_conditions": {{CLEANUP_CONDITIONS}}
  },
  "context_data": {
    "shared_knowledge": {{SHARED_KNOWLEDGE}},
    "common_references": {{COMMON_REFERENCES}},
    "decision_history": {{DECISION_HISTORY}},
    "learning_outcomes": {{LEARNING_OUTCOMES}}
  }
}
```

## Communication Protocols

### Synchronous Communication
```yaml
characteristics:
  - "Real-time request-response"
  - "Blocking operations"
  - "Immediate feedback"
  - "Higher latency tolerance"

use_cases:
  - "Critical decision making"
  - "Real-time coordination"
  - "Interactive problem solving"
  - "Urgent task assignment"

implementation:
  transport: "NATS request-reply"
  timeout: "5-30 seconds"
  retry_policy: "exponential_backoff"
  error_handling: "immediate_escalation"
```

### Asynchronous Communication
```yaml
characteristics:
  - "Non-blocking operations"
  - "Event-driven responses"
  - "Higher throughput"
  - "Eventual consistency"

use_cases:
  - "Background processing"
  - "Batch operations"
  - "Status updates"
  - "Knowledge sharing"

implementation:
  transport: "NATS publish-subscribe"
  delivery_guarantee: "at_least_once"
  ordering: "message_ordering_preserved"
  persistence: "durable_streams"
```

### Stream Processing
```yaml
characteristics:
  - "Continuous data flow"
  - "Real-time processing"
  - "Scalable throughput"
  - "Windowing support"

use_cases:
  - "Monitoring data streams"
  - "Real-time analytics"
  - "Event processing"
  - "Performance tracking"

implementation:
  transport: "NATS JetStream"
  consumer_groups: "load_balanced_processing"
  flow_control: "backpressure_handling"
  processing: "streaming_aggregation"
```

## Quality Assurance

### Message Validation
```yaml
structural_validation:
  - "Required fields present"
  - "Field types correct"
  - "Message format valid"
  - "Size limits respected"

semantic_validation:
  - "Message intent clear"
  - "Context appropriate"
  - "References valid"
  - "Logic consistent"

security_validation:
  - "Authentication verified"
  - "Authorization checked"
  - "Sensitive data protected"
  - "Audit trail maintained"
```

### Response Quality Metrics
```yaml
timeliness:
  measurement: "response_time_percentiles"
  targets: ["p50 < 100ms", "p95 < 500ms", "p99 < 2s"]

accuracy:
  measurement: "response_correctness_rate"
  targets: ["accuracy > 95%", "false_positive < 2%"]

completeness:
  measurement: "information_completeness_score"
  targets: ["completeness > 90%", "missing_critical_info < 1%"]

clarity:
  measurement: "message_clarity_assessment"
  targets: ["clarity_score > 0.8", "ambiguity_rate < 5%"]
```

## Error Handling

### Communication Errors
```json
{
  "error_type": "communication_error",
  "error_code": "{{ERROR_CODE}}",
  "error_details": {
    "failure_point": "{{FAILURE_POINT}}",
    "network_status": "{{NETWORK_STATUS}}",
    "agent_status": "{{AGENT_STATUS}}",
    "message_status": "{{MESSAGE_STATUS}}"
  },
  "recovery_actions": [
    {
      "action": "retry_delivery",
      "max_attempts": {{MAX_RETRIES}},
      "backoff_strategy": "{{BACKOFF_STRATEGY}}"
    },
    {
      "action": "route_alternative",
      "alternative_agents": ["{{ALT_AGENT_1}}"],
      "route_criteria": {{ROUTING_CRITERIA}}
    },
    {
      "action": "escalate_to_human",
      "escalation_threshold": "{{ESCALATION_THRESHOLD}}",
      "notification_channels": [{{NOTIFICATION_CHANNELS}}]
    }
  ]
}
```

### Protocol Violations
```json
{
  "violation_type": "protocol_violation",
  "violation_details": {
    "expected_pattern": "{{EXPECTED_PATTERN}}",
    "actual_behavior": "{{ACTUAL_BEHAVIOR}}",
    "deviation_severity": "{{SEVERITY_LEVEL}}",
    "impact_assessment": "{{IMPACT_ASSESSMENT}}"
  },
  "corrective_actions": [
    {
      "action": "protocol_correction",
      "correction_method": "{{CORRECTION_METHOD}}",
      "automatic": {{IS_AUTOMATIC}}
    },
    {
      "action": "agent_retraining",
      "training_type": "{{TRAINING_TYPE}}",
      "schedule": "{{TRAINING_SCHEDULE}}"
    }
  ]
}
```

## Usage Examples

### Simple Task Assignment
```json
{
  "message_type": "task_assignment",
  "communication": {
    "sender": {
      "agent_id": "orchestrator_001",
      "agent_type": "task_orchestrator"
    },
    "recipient": {
      "agent_id": "knowledge_001",
      "agent_type": "knowledge_integration"
    }
  },
  "content": {
    "intent": "assign_knowledge_task",
    "subject": "Consolidate recent agent interactions",
    "data": {
      "task_id": "task_12345",
      "priority": "HIGH",
      "deadline": "2025-08-12T18:00:00Z"
    }
  }
}
```

### Knowledge Query
```json
{
  "message_type": "knowledge_query",
  "communication": {
    "sender": {
      "agent_id": "orchestrator_001",
      "agent_type": "task_orchestrator"
    },
    "recipient": {
      "agent_id": "knowledge_001",
      "agent_type": "knowledge_integration"
    }
  },
  "content": {
    "intent": "request_agent_context",
    "subject": "Context for task assignment decision",
    "data": {
      "query": "What is the historical performance of agents with semantic_search capability?",
      "context_type": "agent_performance_history",
      "urgency": "medium"
    }
  }
}
```

### Collaboration Request
```json
{
  "message_type": "collaboration_request",
  "communication": {
    "sender": {
      "agent_id": "knowledge_001",
      "agent_type": "knowledge_integration"
    },
    "recipient": {
      "agent_id": "orchestrator_001",
      "agent_type": "task_orchestrator"
    }
  },
  "content": {
    "intent": "request_workflow_collaboration",
    "subject": "Complex knowledge consolidation workflow",
    "data": {
      "collaboration_type": "sequential_workflow",
      "scope": "multi_agent_knowledge_processing",
      "timeline": "2025-08-12T16:00:00Z to 2025-08-12T20:00:00Z",
      "required_agents": ["task_orchestrator", "monitoring_agents"]
    }
  }
}
```