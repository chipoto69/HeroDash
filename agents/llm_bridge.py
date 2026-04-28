#!/usr/bin/env python3
"""
Agent-to-LLM Bridge for Hero Command Centre
Connects agent runtime to actual LLM instances (Claude, OpenAI, local models)
"""

import json
import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, AsyncGenerator
from pathlib import Path
from dataclasses import dataclass
import uuid

# LLM Client imports (conditional based on availability)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger("LLMBridge")

@dataclass
class LLMConfig:
    """Configuration for LLM connections"""
    provider: str  # "anthropic", "openai", "local", "ollama"
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.1
    timeout: int = 30
    rate_limit: int = 10  # requests per minute

@dataclass
class ConversationMessage:
    """Message in agent conversation"""
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = None

@dataclass
class AgentContext:
    """Contextual information for agent processing"""
    agent_id: str
    agent_type: str
    task_id: Optional[str] = None
    conversation_history: List[ConversationMessage] = None
    system_prompt: str = ""
    working_memory: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.conversation_history is None:
            self.conversation_history = []
        if self.working_memory is None:
            self.working_memory = {}

class LLMBridge:
    """Bridge between agent runtime and LLM providers"""
    
    def __init__(self):
        self.llm_configs: Dict[str, LLMConfig] = {}
        self.agent_contexts: Dict[str, AgentContext] = {}
        self.active_conversations: Dict[str, str] = {}  # agent_id -> conversation_id
        
        # Performance tracking
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens_used": 0,
            "average_response_time": 0.0,
            "requests_per_provider": {}
        }
        
        # Initialize LLM configurations
        self._initialize_llm_configs()
        
        logger.info("LLM Bridge initialized")
    
    def _initialize_llm_configs(self):
        """Initialize LLM provider configurations"""
        
        # Anthropic Claude configuration
        if ANTHROPIC_AVAILABLE and os.getenv('ANTHROPIC_API_KEY'):
            self.llm_configs['anthropic'] = LLMConfig(
                provider="anthropic",
                model=os.getenv('ANTHROPIC_MODEL', 'claude-3-sonnet-20240229'),
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                max_tokens=4000,
                temperature=0.1
            )
            logger.info("Configured Anthropic Claude")
        
        # OpenAI configuration
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            self.llm_configs['openai'] = LLMConfig(
                provider="openai",
                model=os.getenv('OPENAI_MODEL', 'gpt-4'),
                api_key=os.getenv('OPENAI_API_KEY'),
                max_tokens=4000,
                temperature=0.1
            )
            logger.info("Configured OpenAI")
        
        # Ollama local configuration
        ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
        if REQUESTS_AVAILABLE:
            try:
                response = requests.get(f"{ollama_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    self.llm_configs['ollama'] = LLMConfig(
                        provider="ollama",
                        model=os.getenv('OLLAMA_MODEL', 'llama2'),
                        base_url=ollama_url,
                        max_tokens=4000,
                        temperature=0.1
                    )
                    logger.info("Configured Ollama local LLM")
            except Exception:
                pass  # Ollama not available
        
        # Default to mock provider if no others available
        if not self.llm_configs:
            self.llm_configs['mock'] = LLMConfig(
                provider="mock",
                model="mock-model",
                max_tokens=4000,
                temperature=0.1
            )
            logger.warning("No LLM providers available, using mock provider")
    
    def get_best_llm_for_agent(self, agent_type: str) -> str:
        """Select the best LLM provider for a specific agent type"""
        
        # Agent-specific LLM preferences
        preferences = {
            "task_orchestrator": ["anthropic", "openai", "ollama", "mock"],
            "knowledge_integration": ["anthropic", "openai", "ollama", "mock"],
            "default": ["anthropic", "openai", "ollama", "mock"]
        }
        
        agent_prefs = preferences.get(agent_type, preferences["default"])
        
        # Return first available preferred provider
        for provider in agent_prefs:
            if provider in self.llm_configs:
                return provider
        
        # Fallback to any available provider
        return list(self.llm_configs.keys())[0] if self.llm_configs else "mock"
    
    async def create_agent_context(self, agent_id: str, agent_type: str, 
                                 system_prompt: str, task_id: Optional[str] = None) -> AgentContext:
        """Create conversation context for an agent"""
        
        context = AgentContext(
            agent_id=agent_id,
            agent_type=agent_type,
            task_id=task_id,
            system_prompt=system_prompt
        )
        
        # Add system message to conversation
        system_message = ConversationMessage(
            role="system",
            content=system_prompt,
            timestamp=datetime.now(),
            metadata={"agent_type": agent_type, "task_id": task_id}
        )
        context.conversation_history.append(system_message)
        
        self.agent_contexts[agent_id] = context
        logger.info(f"Created context for agent {agent_id} ({agent_type})")
        
        return context
    
    async def process_agent_message(self, agent_id: str, message: str, 
                                  message_type: str = "task_input",
                                  metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a message through an agent's LLM"""
        
        if agent_id not in self.agent_contexts:
            raise ValueError(f"No context found for agent {agent_id}")
        
        context = self.agent_contexts[agent_id]
        
        try:
            # Add user message to conversation
            user_message = ConversationMessage(
                role="user", 
                content=message,
                timestamp=datetime.now(),
                metadata={"message_type": message_type, **(metadata or {})}
            )
            context.conversation_history.append(user_message)
            
            # Select LLM provider
            provider = self.get_best_llm_for_agent(context.agent_type)
            
            # Generate response
            start_time = datetime.now()
            response = await self._generate_llm_response(provider, context)
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Add assistant response to conversation
            assistant_message = ConversationMessage(
                role="assistant",
                content=response["content"],
                timestamp=datetime.now(),
                metadata={
                    "provider": provider,
                    "model": self.llm_configs[provider].model,
                    "response_time": response_time,
                    "tokens_used": response.get("tokens_used", 0)
                }
            )
            context.conversation_history.append(assistant_message)
            
            # Update metrics
            self._update_metrics(provider, response_time, response.get("tokens_used", 0), True)
            
            # Parse response for structured actions
            parsed_response = await self._parse_agent_response(response["content"], context)
            
            result = {
                "agent_id": agent_id,
                "response": response["content"],
                "parsed_actions": parsed_response.get("actions", []),
                "working_memory_updates": parsed_response.get("memory_updates", {}),
                "response_time": response_time,
                "provider_used": provider,
                "tokens_used": response.get("tokens_used", 0),
                "metadata": {
                    "message_type": message_type,
                    "conversation_length": len(context.conversation_history)
                }
            }
            
            logger.info(f"Processed message for agent {agent_id} using {provider} "
                       f"({response_time:.2f}s, {response.get('tokens_used', 0)} tokens)")
            
            return result
            
        except Exception as e:
            self._update_metrics(provider, 0, 0, False)
            logger.error(f"Error processing message for agent {agent_id}: {e}")
            raise
    
    async def _generate_llm_response(self, provider: str, context: AgentContext) -> Dict[str, Any]:
        """Generate response from specific LLM provider"""
        
        config = self.llm_configs[provider]
        
        if provider == "anthropic":
            return await self._generate_anthropic_response(config, context)
        elif provider == "openai":
            return await self._generate_openai_response(config, context)
        elif provider == "ollama":
            return await self._generate_ollama_response(config, context)
        elif provider == "mock":
            return await self._generate_mock_response(config, context)
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    async def _generate_anthropic_response(self, config: LLMConfig, context: AgentContext) -> Dict[str, Any]:
        """Generate response using Anthropic Claude"""
        
        if not ANTHROPIC_AVAILABLE:
            raise RuntimeError("Anthropic not available")
        
        client = anthropic.AsyncAnthropic(api_key=config.api_key)
        
        # Convert conversation to Claude format
        messages = []
        for msg in context.conversation_history[1:]:  # Skip system message
            if msg.role in ["user", "assistant"]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        try:
            response = await client.messages.create(
                model=config.model,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                system=context.system_prompt,
                messages=messages
            )
            
            return {
                "content": response.content[0].text,
                "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
                "model": config.model
            }
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def _generate_openai_response(self, config: LLMConfig, context: AgentContext) -> Dict[str, Any]:
        """Generate response using OpenAI GPT"""
        
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI not available")
        
        client = openai.AsyncOpenAI(api_key=config.api_key)
        
        # Convert conversation to OpenAI format
        messages = []
        for msg in context.conversation_history:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        try:
            response = await client.chat.completions.create(
                model=config.model,
                messages=messages,
                max_tokens=config.max_tokens,
                temperature=config.temperature,
                timeout=config.timeout
            )
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model": config.model
            }
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _generate_ollama_response(self, config: LLMConfig, context: AgentContext) -> Dict[str, Any]:
        """Generate response using Ollama local LLM"""
        
        if not REQUESTS_AVAILABLE:
            raise RuntimeError("Requests not available for Ollama")
        
        # Prepare conversation for Ollama
        conversation = f"System: {context.system_prompt}\n\n"
        for msg in context.conversation_history[1:]:  # Skip system message
            conversation += f"{msg.role.title()}: {msg.content}\n"
        conversation += "Assistant: "
        
        try:
            async with asyncio.timeout(config.timeout):
                response = requests.post(
                    f"{config.base_url}/api/generate",
                    json={
                        "model": config.model,
                        "prompt": conversation,
                        "stream": False,
                        "options": {
                            "temperature": config.temperature,
                            "num_predict": config.max_tokens
                        }
                    },
                    timeout=config.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                return {
                    "content": result["response"],
                    "tokens_used": result.get("eval_count", 0) + result.get("prompt_eval_count", 0),
                    "model": config.model
                }
                
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise
    
    async def _generate_mock_response(self, config: LLMConfig, context: AgentContext) -> Dict[str, Any]:
        """Generate mock response for testing"""
        
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Generate contextual mock response based on agent type
        if context.agent_type == "task_orchestrator":
            mock_responses = [
                "Task analyzed and assigned to appropriate agent based on capability matching.",
                "Workflow coordination initiated with 3 sequential steps identified.",
                "Load balancing assessment complete - distributing tasks across available agents.",
                "Priority escalation detected - adjusting task queue for urgent processing."
            ]
        elif context.agent_type == "knowledge_integration":
            mock_responses = [
                "Knowledge graph updated with new entities and relationships.",
                "Pattern recognition complete - identified 3 significant trends.",
                "Semantic search executed - returning 15 relevant knowledge nodes.",
                "Memory consolidation in progress - processing 47 new episodes."
            ]
        else:
            mock_responses = [
                "Task processed successfully using mock LLM provider.",
                "Analysis complete with mock reasoning engine.",
                "Decision made using simulated agent intelligence."
            ]
        
        import random
        response_content = random.choice(mock_responses)
        
        return {
            "content": response_content,
            "tokens_used": len(response_content.split()) * 1.3,  # Rough token estimate
            "model": config.model
        }
    
    async def _parse_agent_response(self, response: str, context: AgentContext) -> Dict[str, Any]:
        """Parse agent response for structured actions and memory updates"""
        
        parsed = {
            "actions": [],
            "memory_updates": {},
            "decisions": [],
            "next_steps": []
        }
        
        # Simple parsing logic - in production, this would be more sophisticated
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Parse action indicators
            if line.startswith('ACTION:') or line.startswith('- ACTION:'):
                action = line.replace('ACTION:', '').replace('- ACTION:', '').strip()
                parsed["actions"].append({
                    "type": "agent_action",
                    "description": action,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Parse memory updates
            elif line.startswith('MEMORY:') or line.startswith('- MEMORY:'):
                memory = line.replace('MEMORY:', '').replace('- MEMORY:', '').strip()
                parsed["memory_updates"][f"update_{len(parsed['memory_updates'])}"] = memory
            
            # Parse decisions
            elif line.startswith('DECISION:') or line.startswith('- DECISION:'):
                decision = line.replace('DECISION:', '').replace('- DECISION:', '').strip()
                parsed["decisions"].append(decision)
            
            # Parse next steps
            elif line.startswith('NEXT:') or line.startswith('- NEXT:'):
                next_step = line.replace('NEXT:', '').replace('- NEXT:', '').strip()
                parsed["next_steps"].append(next_step)
        
        return parsed
    
    def _update_metrics(self, provider: str, response_time: float, tokens_used: int, success: bool):
        """Update performance metrics"""
        
        self.metrics["total_requests"] += 1
        
        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
        
        self.metrics["total_tokens_used"] += tokens_used
        
        # Update average response time
        total_successful = self.metrics["successful_requests"]
        if total_successful > 1:
            current_avg = self.metrics["average_response_time"]
            self.metrics["average_response_time"] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
        else:
            self.metrics["average_response_time"] = response_time
        
        # Update per-provider metrics
        if provider not in self.metrics["requests_per_provider"]:
            self.metrics["requests_per_provider"][provider] = 0
        self.metrics["requests_per_provider"][provider] += 1
    
    async def cleanup_agent_context(self, agent_id: str):
        """Clean up agent context and conversation history"""
        
        if agent_id in self.agent_contexts:
            context = self.agent_contexts[agent_id]
            
            # Save conversation history for analysis
            conversation_file = Path.home() / ".hero_core" / "cache" / f"conversation_{agent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            conversation_data = {
                "agent_id": agent_id,
                "agent_type": context.agent_type,
                "task_id": context.task_id,
                "conversation_history": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "timestamp": msg.timestamp.isoformat(),
                        "metadata": msg.metadata
                    }
                    for msg in context.conversation_history
                ],
                "working_memory": context.working_memory
            }
            
            with open(conversation_file, 'w') as f:
                json.dump(conversation_data, f, indent=2)
            
            del self.agent_contexts[agent_id]
            logger.info(f"Cleaned up context for agent {agent_id}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            **self.metrics,
            "active_contexts": len(self.agent_contexts),
            "available_providers": list(self.llm_configs.keys()),
            "provider_configs": {
                provider: {
                    "model": config.model,
                    "provider": config.provider
                }
                for provider, config in self.llm_configs.items()
            }
        }

# Global bridge instance
_bridge = None

def get_llm_bridge() -> LLMBridge:
    """Get or create the global LLM bridge instance"""
    global _bridge
    if _bridge is None:
        _bridge = LLMBridge()
    return _bridge

async def main():
    """Test the LLM bridge"""
    bridge = get_llm_bridge()
    
    # Create test agent context
    system_prompt = """You are a test agent for the Hero Command Centre. 
    Your role is to process tasks and provide intelligent responses.
    Always format your responses with clear actions and decisions."""
    
    context = await bridge.create_agent_context(
        "test_agent_001",
        "task_orchestrator", 
        system_prompt
    )
    
    # Test message processing
    test_message = "Analyze the current system load and recommend optimization strategies."
    
    result = await bridge.process_agent_message(
        "test_agent_001",
        test_message,
        "analysis_request"
    )
    
    print("LLM Bridge Test Results:")
    print(f"Response: {result['response']}")
    print(f"Provider: {result['provider_used']}")
    print(f"Response Time: {result['response_time']:.2f}s")
    print(f"Tokens Used: {result['tokens_used']}")
    print(f"Actions: {result['parsed_actions']}")
    
    # Clean up
    await bridge.cleanup_agent_context("test_agent_001")
    
    # Show metrics
    metrics = bridge.get_metrics()
    print(f"\nMetrics: {json.dumps(metrics, indent=2)}")

if __name__ == "__main__":
    asyncio.run(main())