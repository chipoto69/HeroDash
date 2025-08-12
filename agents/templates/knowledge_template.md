# Knowledge Template for Hero Command Centre

## Standard Knowledge Entry Format

```json
{
  "knowledge_id": "{{KNOWLEDGE_ID}}",
  "correlation_id": "{{CORRELATION_ID}}",
  "timestamp": "{{TIMESTAMP}}",
  "knowledge_type": "{{KNOWLEDGE_TYPE}}",
  "source": "{{SOURCE_TYPE}}",
  
  "episode": {
    "episode_id": "{{EPISODE_ID}}",
    "name": "{{EPISODE_NAME}}",
    "description": "{{EPISODE_DESCRIPTION}}",
    "body": "{{EPISODE_CONTENT}}",
    "group_id": "{{GROUP_ID}}",
    "session_id": "{{SESSION_ID}}"
  },
  
  "entities": [
    {
      "entity_id": "{{ENTITY_ID}}",
      "name": "{{ENTITY_NAME}}",
      "type": "{{ENTITY_TYPE}}",
      "properties": {{ENTITY_PROPERTIES}},
      "confidence_score": {{CONFIDENCE_SCORE}}
    }
  ],
  
  "relationships": [
    {
      "relationship_id": "{{RELATIONSHIP_ID}}",
      "source_entity": "{{SOURCE_ENTITY_ID}}",
      "target_entity": "{{TARGET_ENTITY_ID}}",
      "relationship_type": "{{RELATIONSHIP_TYPE}}",
      "properties": {{RELATIONSHIP_PROPERTIES}},
      "strength": {{RELATIONSHIP_STRENGTH}},
      "temporal_context": {{TEMPORAL_CONTEXT}}
    }
  ],
  
  "facts": [
    {
      "fact_id": "{{FACT_ID}}",
      "statement": "{{FACT_STATEMENT}}",
      "entities_involved": ["{{ENTITY_1}}", "{{ENTITY_2}}"],
      "confidence": {{FACT_CONFIDENCE}},
      "evidence": [{{EVIDENCE_SOURCES}}],
      "valid_from": "{{VALID_FROM_TIMESTAMP}}",
      "valid_until": "{{VALID_UNTIL_TIMESTAMP}}",
      "invalidated": {{IS_INVALIDATED}}
    }
  ],
  
  "patterns": [
    {
      "pattern_id": "{{PATTERN_ID}}",
      "pattern_type": "{{PATTERN_TYPE}}",
      "description": "{{PATTERN_DESCRIPTION}}",
      "frequency": {{PATTERN_FREQUENCY}},
      "significance": {{PATTERN_SIGNIFICANCE}},
      "evidence_count": {{EVIDENCE_COUNT}}
    }
  ],
  
  "insights": [
    {
      "insight_id": "{{INSIGHT_ID}}",
      "insight_type": "{{INSIGHT_TYPE}}",
      "summary": "{{INSIGHT_SUMMARY}}",
      "detailed_analysis": "{{DETAILED_ANALYSIS}}",
      "confidence_level": {{CONFIDENCE_LEVEL}},
      "actionable_recommendations": [{{RECOMMENDATIONS}}],
      "derived_from": ["{{SOURCE_PATTERN_1}}", "{{SOURCE_FACT_1}}"]
    }
  ],
  
  "context": {
    "temporal_context": {
      "created_at": "{{CREATION_TIMESTAMP}}",
      "relevant_timeframe": "{{TIMEFRAME}}",
      "temporal_dependencies": [{{TEMPORAL_DEPS}}]
    },
    "workflow_context": {
      "workflow_id": "{{WORKFLOW_ID}}",
      "workflow_stage": "{{WORKFLOW_STAGE}}",
      "related_tasks": ["{{TASK_1}}", "{{TASK_2}}"]
    },
    "agent_context": {
      "source_agent": "{{SOURCE_AGENT}}",
      "participating_agents": ["{{AGENT_1}}", "{{AGENT_2}}"],
      "collaboration_pattern": "{{COLLABORATION_PATTERN}}"
    }
  },
  
  "quality_metrics": {
    "completeness_score": {{COMPLETENESS_SCORE}},
    "accuracy_score": {{ACCURACY_SCORE}},
    "relevance_score": {{RELEVANCE_SCORE}},
    "freshness_score": {{FRESHNESS_SCORE}},
    "consistency_score": {{CONSISTENCY_SCORE}}
  },
  
  "access_control": {
    "classification": "{{CLASSIFICATION_LEVEL}}",
    "access_permissions": ["{{PERMISSION_1}}", "{{PERMISSION_2}}"],
    "sharing_restrictions": {{SHARING_RESTRICTIONS}},
    "retention_period": "{{RETENTION_PERIOD}}"
  },
  
  "tracing": {
    "langsmith_trace_id": "{{LANGSMITH_TRACE_ID}}",
    "knowledge_lineage": [{{KNOWLEDGE_LINEAGE}}],
    "processing_metadata": {{PROCESSING_METADATA}}
  }
}
```

## Knowledge Types

### Primary Knowledge Types
```yaml
episode:
  description: "Raw interaction or event data"
  examples: ["agent_interaction", "task_execution", "user_feedback"]
  storage: "Graphiti episodes"

fact:
  description: "Verified relationship between entities"
  examples: ["agent_capability", "task_requirement", "performance_metric"]
  storage: "Graphiti entity edges"

pattern:
  description: "Recurring behavior or trend"
  examples: ["collaboration_pattern", "performance_trend", "failure_mode"]
  storage: "Pattern recognition results"

insight:
  description: "Derived understanding or recommendation"
  examples: ["optimization_opportunity", "risk_assessment", "capacity_prediction"]
  storage: "Insight generation results"

context:
  description: "Background information for decision making"
  examples: ["historical_performance", "domain_knowledge", "user_preferences"]
  storage: "Context provision cache"
```

### Source Types
```yaml
agent_interaction:
  description: "Data from agent-to-agent communication"
  validation: "Must include participating agents and interaction type"

task_execution:
  description: "Data from task execution and results"
  validation: "Must include task ID, agent, and outcome"

system_monitoring:
  description: "Data from system health and performance monitoring"
  validation: "Must include metrics and timestamp"

user_feedback:
  description: "Data from user interactions and feedback"
  validation: "Must include user context and feedback type"

external_integration:
  description: "Data from external systems (Chimera, APIs)"
  validation: "Must include source system and data provenance"
```

## Entity Types & Properties

### Core Entity Types
```json
{
  "agent": {
    "properties": {
      "agent_id": "string",
      "agent_type": "string",
      "capabilities": "array",
      "framework": "string",
      "performance_metrics": "object",
      "last_active": "timestamp"
    },
    "relationships": ["executes", "collaborates_with", "reports_to"]
  },
  
  "task": {
    "properties": {
      "task_id": "string",
      "task_type": "string",
      "complexity": "number",
      "duration": "number",
      "success_rate": "number",
      "resource_requirements": "object"
    },
    "relationships": ["requires", "depends_on", "produces"]
  },
  
  "workflow": {
    "properties": {
      "workflow_id": "string",
      "workflow_type": "string",
      "steps": "array",
      "optimization_level": "number",
      "success_factors": "array"
    },
    "relationships": ["contains", "optimizes", "replaces"]
  },
  
  "capability": {
    "properties": {
      "capability_name": "string",
      "category": "string",
      "complexity_level": "number",
      "resource_cost": "number",
      "success_indicators": "array"
    },
    "relationships": ["enables", "requires", "enhances"]
  },
  
  "knowledge_domain": {
    "properties": {
      "domain_name": "string",
      "expertise_level": "number",
      "coverage_percentage": "number",
      "update_frequency": "string",
      "authoritative_sources": "array"
    },
    "relationships": ["encompasses", "relates_to", "derives_from"]
  }
}
```

## Relationship Types

### Standard Relationships
```yaml
# Execution Relationships
executes: "Agent performs task"
requires: "Task needs capability"
produces: "Task generates output"
consumes: "Task uses resource"

# Collaboration Relationships
collaborates_with: "Agents work together"
delegates_to: "Agent assigns work to another"
reports_to: "Agent provides status to another"
assists: "Agent helps another"

# Knowledge Relationships
derives_from: "Knowledge comes from source"
relates_to: "Knowledge is connected to other knowledge"
contradicts: "Knowledge conflicts with other knowledge"
supersedes: "Knowledge replaces older knowledge"

# Temporal Relationships
precedes: "Event happens before another"
triggers: "Event causes another event"
correlates_with: "Events happen together"
depends_on: "Event requires another event"

# Performance Relationships
optimizes: "Entity improves another"
degrades: "Entity worsens another"
influences: "Entity affects another"
predicts: "Entity forecasts another"
```

## Pattern Recognition Templates

### Collaboration Patterns
```json
{
  "pattern_type": "collaboration_pattern",
  "pattern_name": "{{PATTERN_NAME}}",
  "description": "{{PATTERN_DESCRIPTION}}",
  "frequency": {{OCCURRENCE_COUNT}},
  "participants": ["{{AGENT_1}}", "{{AGENT_2}}"],
  "trigger_conditions": [{{TRIGGER_CONDITIONS}}],
  "success_indicators": [{{SUCCESS_INDICATORS}}],
  "optimization_opportunities": [{{OPTIMIZATIONS}}],
  "evidence": {
    "episodes": ["{{EPISODE_1}}", "{{EPISODE_2}}"],
    "frequency_data": {{FREQUENCY_DATA}},
    "performance_metrics": {{PERFORMANCE_METRICS}}
  }
}
```

### Performance Patterns
```json
{
  "pattern_type": "performance_pattern",
  "pattern_name": "{{PATTERN_NAME}}",
  "description": "{{PATTERN_DESCRIPTION}}",
  "trend_direction": "{{INCREASING|DECREASING|STABLE|CYCLICAL}}",
  "affected_entities": ["{{ENTITY_1}}", "{{ENTITY_2}}"],
  "time_horizon": "{{TIME_PERIOD}}",
  "predictive_value": {{PREDICTION_ACCURACY}},
  "intervention_points": [{{INTERVENTION_OPTIONS}}],
  "business_impact": {
    "efficiency_change": {{EFFICIENCY_DELTA}},
    "quality_change": {{QUALITY_DELTA}},
    "cost_change": {{COST_DELTA}}
  }
}
```

## Insight Generation Templates

### Optimization Insights
```json
{
  "insight_type": "optimization_opportunity",
  "insight_id": "{{INSIGHT_ID}}",
  "title": "{{INSIGHT_TITLE}}",
  "summary": "{{BRIEF_SUMMARY}}",
  "detailed_analysis": {
    "current_state": "{{CURRENT_STATE_DESCRIPTION}}",
    "identified_inefficiency": "{{INEFFICIENCY_DESCRIPTION}}",
    "root_cause_analysis": "{{ROOT_CAUSES}}",
    "potential_improvements": [{{IMPROVEMENT_OPTIONS}}]
  },
  "recommendations": [
    {
      "recommendation": "{{RECOMMENDATION_TEXT}}",
      "priority": "{{HIGH|MEDIUM|LOW}}",
      "effort_required": "{{EFFORT_LEVEL}}",
      "expected_impact": "{{IMPACT_DESCRIPTION}}",
      "implementation_steps": [{{IMPLEMENTATION_STEPS}}],
      "risks": [{{POTENTIAL_RISKS}}]
    }
  ],
  "supporting_evidence": {
    "data_sources": [{{DATA_SOURCES}}],
    "statistical_confidence": {{CONFIDENCE_PERCENTAGE}},
    "validation_methods": [{{VALIDATION_METHODS}}]
  }
}
```

### Risk Assessment Insights
```json
{
  "insight_type": "risk_assessment",
  "insight_id": "{{INSIGHT_ID}}",
  "title": "{{RISK_TITLE}}",
  "risk_level": "{{CRITICAL|HIGH|MEDIUM|LOW}}",
  "probability": {{PROBABILITY_SCORE}},
  "impact_severity": {{IMPACT_SCORE}},
  "risk_factors": [
    {
      "factor": "{{RISK_FACTOR}}",
      "contribution": {{CONTRIBUTION_PERCENTAGE}},
      "trend": "{{INCREASING|DECREASING|STABLE}}"
    }
  ],
  "mitigation_strategies": [
    {
      "strategy": "{{MITIGATION_STRATEGY}}",
      "effectiveness": {{EFFECTIVENESS_SCORE}},
      "implementation_cost": "{{COST_LEVEL}}",
      "timeline": "{{IMPLEMENTATION_TIMELINE}}"
    }
  ],
  "monitoring_requirements": [{{MONITORING_NEEDS}}]
}
```

## Context Provision Templates

### Agent Context
```json
{
  "context_type": "agent_context",
  "agent_id": "{{AGENT_ID}}",
  "context_summary": {
    "expertise_areas": [{{EXPERTISE_AREAS}}],
    "performance_history": {{PERFORMANCE_SUMMARY}},
    "collaboration_preferences": {{COLLABORATION_PREFS}},
    "current_workload": {{WORKLOAD_STATUS}}
  },
  "relevant_knowledge": [
    {
      "knowledge_type": "{{KNOWLEDGE_TYPE}}",
      "relevance_score": {{RELEVANCE_SCORE}},
      "summary": "{{KNOWLEDGE_SUMMARY}}",
      "last_updated": "{{UPDATE_TIMESTAMP}}"
    }
  ],
  "success_patterns": [{{SUCCESS_PATTERNS}}],
  "failure_modes": [{{KNOWN_FAILURE_MODES}}],
  "optimization_suggestions": [{{OPTIMIZATION_SUGGESTIONS}}]
}
```

### Task Context
```json
{
  "context_type": "task_context",
  "task_type": "{{TASK_TYPE}}",
  "context_summary": {
    "similar_tasks": [{{SIMILAR_TASK_REFERENCES}}],
    "success_factors": [{{SUCCESS_FACTORS}}],
    "common_challenges": [{{COMMON_CHALLENGES}}],
    "resource_patterns": {{RESOURCE_USAGE_PATTERNS}}
  },
  "best_practices": [
    {
      "practice": "{{BEST_PRACTICE}}",
      "effectiveness": {{EFFECTIVENESS_SCORE}},
      "applicability": "{{APPLICABILITY_CONDITIONS}}"
    }
  ],
  "agent_recommendations": [
    {
      "agent_type": "{{RECOMMENDED_AGENT_TYPE}}",
      "suitability_score": {{SUITABILITY_SCORE}},
      "rationale": "{{RECOMMENDATION_RATIONALE}}"
    }
  ]
}
```

## Quality Assessment

### Quality Metrics
```yaml
completeness:
  description: "How complete is the knowledge representation"
  scale: "0.0 to 1.0"
  calculation: "Required fields present / Total required fields"

accuracy:
  description: "How accurate is the knowledge content"
  scale: "0.0 to 1.0"
  calculation: "Based on validation against known facts"

relevance:
  description: "How relevant is the knowledge to current context"
  scale: "0.0 to 1.0"
  calculation: "Context matching score"

freshness:
  description: "How recent and up-to-date is the knowledge"
  scale: "0.0 to 1.0"
  calculation: "Time decay function based on creation/update time"

consistency:
  description: "How consistent is the knowledge with existing knowledge"
  scale: "0.0 to 1.0"
  calculation: "Conflict detection and resolution score"
```

### Validation Rules
```yaml
required_validation:
  - "All entity references must exist in knowledge graph"
  - "Relationship types must be from approved vocabulary"
  - "Temporal constraints must be logically consistent"
  - "Confidence scores must be between 0.0 and 1.0"

content_validation:
  - "Episode content must not contain sensitive information"
  - "Facts must have supporting evidence"
  - "Insights must reference source patterns or facts"
  - "Patterns must have minimum evidence threshold"

integrity_validation:
  - "No circular dependencies in knowledge relationships"
  - "Temporal facts must not contradict chronology"
  - "Entity properties must conform to type schema"
  - "Knowledge classification must match content sensitivity"
```

## Usage Examples

### Simple Episode Storage
```json
{
  "knowledge_type": "episode",
  "episode": {
    "name": "agent_task_completion",
    "description": "Task orchestrator completed workflow assignment",
    "body": "Task_001 successfully assigned to knowledge_agent_002 based on capability match and current load assessment",
    "group_id": "session_2025_08_12_001"
  },
  "source": "agent_interaction"
}
```

### Complex Pattern Recognition
```json
{
  "knowledge_type": "pattern",
  "patterns": [{
    "pattern_type": "collaboration_pattern",
    "pattern_name": "knowledge_intensive_workflow",
    "description": "When tasks require both semantic search and graph operations, task orchestrator consistently assigns to knowledge integration agent with 95% success rate",
    "frequency": 47,
    "significance": 0.87
  }],
  "source": "pattern_recognition"
}
```