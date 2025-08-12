#!/usr/bin/env python3
"""
Agent Integration Test for Hero Command Centre
Tests the agent system prompts and configurations with existing framework
"""

import json
import os
import sys
import asyncio
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add Hero monitors to path
sys.path.append(str(Path(__file__).parent.parent / "monitors"))

try:
    from agent_coordinator import get_coordinator, TaskPriority
    from chimera_bridge import get_bridge
    from langsmith_tracer import get_tracer, trace_hero_function
    HERO_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Hero framework not fully available: {e}")
    HERO_AVAILABLE = False

class AgentIntegrationTester:
    """Test suite for agent integration with Hero framework"""
    
    def __init__(self):
        self.test_results = []
        self.agents_dir = Path(__file__).parent
        self.cache_dir = Path.home() / ".hero_core" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configurations
        self.load_configurations()
        
        # Initialize Hero components if available
        if HERO_AVAILABLE:
            self.coordinator = get_coordinator()
            self.bridge = get_bridge()
            self.tracer = get_tracer()
        else:
            self.coordinator = None
            self.bridge = None
            self.tracer = None
    
    def load_configurations(self):
        """Load agent configurations"""
        try:
            # Load agent capabilities
            with open(self.agents_dir / "configs" / "agent_capabilities.yaml", 'r') as f:
                self.capabilities_config = yaml.safe_load(f)
            
            # Load NATS subjects
            with open(self.agents_dir / "configs" / "nats_subjects.yaml", 'r') as f:
                self.nats_config = yaml.safe_load(f)
            
            # Load LangSmith config
            with open(self.agents_dir / "configs" / "langsmith_config.yaml", 'r') as f:
                self.langsmith_config = yaml.safe_load(f)
                
            print("✅ Configuration files loaded successfully")
            
        except Exception as e:
            print(f"❌ Error loading configurations: {e}")
            self.capabilities_config = {}
            self.nats_config = {}
            self.langsmith_config = {}
    
    @trace_hero_function("test_configuration_validation", "integration-tester")
    def test_configuration_validation(self):
        """Test that all configuration files are valid and complete"""
        test_name = "Configuration Validation"
        issues = []
        
        # Test agent capabilities config
        if not self.capabilities_config:
            issues.append("Agent capabilities config is empty or invalid")
        else:
            required_agents = ["task_orchestrator", "knowledge_integration"]
            for agent in required_agents:
                if agent not in self.capabilities_config.get("agents", {}):
                    issues.append(f"Missing agent configuration for {agent}")
                else:
                    agent_config = self.capabilities_config["agents"][agent]
                    required_fields = ["capabilities", "specialized_functions", "communication"]
                    for field in required_fields:
                        if field not in agent_config:
                            issues.append(f"Missing {field} in {agent} configuration")
        
        # Test NATS subjects config
        if not self.nats_config:
            issues.append("NATS subjects config is empty or invalid")
        else:
            required_patterns = ["agent_coordination", "knowledge_management", "agent_responses"]
            for pattern in required_patterns:
                if pattern not in self.nats_config.get("subject_patterns", {}):
                    issues.append(f"Missing NATS subject pattern: {pattern}")
        
        # Test LangSmith config
        if not self.langsmith_config:
            issues.append("LangSmith config is empty or invalid")
        else:
            if "tracing" not in self.langsmith_config:
                issues.append("Missing tracing configuration in LangSmith config")
        
        success = len(issues) == 0
        self.test_results.append({
            "test": test_name,
            "success": success,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed: {', '.join(issues)}")
        
        return success
    
    @trace_hero_function("test_system_prompt_structure", "integration-tester")
    def test_system_prompt_structure(self):
        """Test that system prompts have proper structure and content"""
        test_name = "System Prompt Structure"
        issues = []
        
        # Test Task Orchestrator prompt
        orchestrator_prompt_path = self.agents_dir / "sysprompts" / "task_orchestrator_sysprompt.md"
        if not orchestrator_prompt_path.exists():
            issues.append("Task Orchestrator system prompt file missing")
        else:
            with open(orchestrator_prompt_path, 'r') as f:
                content = f.read()
                required_sections = [
                    "Agent Identity & Purpose",
                    "Available Capabilities & Tools", 
                    "Communication Protocols",
                    "Decision-Making Framework",
                    "Collaboration Rules",
                    "Error Handling & Recovery"
                ]
                for section in required_sections:
                    if section not in content:
                        issues.append(f"Missing section '{section}' in Task Orchestrator prompt")
        
        # Test Knowledge Integration prompt
        knowledge_prompt_path = self.agents_dir / "sysprompts" / "knowledge_integration_sysprompt.md"
        if not knowledge_prompt_path.exists():
            issues.append("Knowledge Integration system prompt file missing")
        else:
            with open(knowledge_prompt_path, 'r') as f:
                content = f.read()
                required_sections = [
                    "Agent Identity & Purpose",
                    "Knowledge Architecture",
                    "Query Intelligence & Context Provision",
                    "Learning & Adaptation Mechanisms"
                ]
                for section in required_sections:
                    if section not in content:
                        issues.append(f"Missing section '{section}' in Knowledge Integration prompt")
        
        success = len(issues) == 0
        self.test_results.append({
            "test": test_name,
            "success": success,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed: {', '.join(issues)}")
        
        return success
    
    @trace_hero_function("test_template_structure", "integration-tester")
    def test_template_structure(self):
        """Test that templates have proper structure"""
        test_name = "Template Structure"
        issues = []
        
        # Test templates exist
        template_files = [
            "task_template.md",
            "knowledge_template.md", 
            "interaction_template.md"
        ]
        
        for template_file in template_files:
            template_path = self.agents_dir / "templates" / template_file
            if not template_path.exists():
                issues.append(f"Template file missing: {template_file}")
            else:
                with open(template_path, 'r') as f:
                    content = f.read()
                    if len(content) < 1000:  # Basic content check
                        issues.append(f"Template file {template_file} appears incomplete")
                    if "{{" not in content:  # Check for template variables
                        issues.append(f"Template file {template_file} has no template variables")
        
        success = len(issues) == 0
        self.test_results.append({
            "test": test_name,
            "success": success,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed: {', '.join(issues)}")
        
        return success
    
    @trace_hero_function("test_hero_framework_integration", "integration-tester")
    def test_hero_framework_integration(self):
        """Test integration with existing Hero framework"""
        test_name = "Hero Framework Integration"
        issues = []
        
        if not HERO_AVAILABLE:
            issues.append("Hero framework not available for testing")
        else:
            # Test coordinator integration
            if self.coordinator is None:
                issues.append("Agent coordinator not available")
            else:
                try:
                    # Test registering agents from config
                    orchestrator_config = self.capabilities_config["agents"]["task_orchestrator"]
                    agent_id = self.coordinator.register_agent(
                        "test_orchestrator",
                        orchestrator_config["type"],
                        orchestrator_config["capabilities"][:3],  # Use first 3 capabilities
                        "hero-command-centre"
                    )
                    if not agent_id:
                        issues.append("Failed to register test orchestrator agent")
                    else:
                        print(f"  ✓ Registered test orchestrator agent: {agent_id}")
                        
                except Exception as e:
                    issues.append(f"Error registering orchestrator agent: {e}")
            
            # Test bridge integration
            if self.bridge is None:
                issues.append("Chimera bridge not available")
            else:
                try:
                    status = self.bridge.get_chimera_status()
                    if "integration_status" not in status:
                        issues.append("Chimera bridge status format unexpected")
                    else:
                        print(f"  ✓ Chimera bridge status retrieved")
                except Exception as e:
                    issues.append(f"Error getting Chimera bridge status: {e}")
            
            # Test tracer integration
            if self.tracer is None:
                issues.append("LangSmith tracer not available")
            else:
                try:
                    stats = self.tracer.get_agent_statistics()
                    if "session_id" not in stats:
                        issues.append("LangSmith tracer stats format unexpected")
                    else:
                        print(f"  ✓ LangSmith tracer stats retrieved")
                except Exception as e:
                    issues.append(f"Error getting tracer stats: {e}")
        
        success = len(issues) == 0
        self.test_results.append({
            "test": test_name,
            "success": success,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed: {', '.join(issues)}")
        
        return success
    
    @trace_hero_function("test_agent_workflow_simulation", "integration-tester")
    def test_agent_workflow_simulation(self):
        """Simulate agent workflow using the configurations"""
        test_name = "Agent Workflow Simulation"
        issues = []
        
        if not HERO_AVAILABLE or not self.coordinator:
            issues.append("Hero framework not available for workflow simulation")
        else:
            try:
                # Simulate task orchestrator workflow
                print("  → Simulating task orchestrator workflow...")
                
                # Register both agent types
                orchestrator_config = self.capabilities_config["agents"]["task_orchestrator"]
                knowledge_config = self.capabilities_config["agents"]["knowledge_integration"]
                
                orchestrator_id = self.coordinator.register_agent(
                    "sim_orchestrator",
                    orchestrator_config["type"],
                    orchestrator_config["capabilities"][:3],
                    "hero-command-centre"
                )
                
                knowledge_id = self.coordinator.register_agent(
                    "sim_knowledge",
                    knowledge_config["type"], 
                    knowledge_config["capabilities"][:3],
                    "hero-command-centre"
                )
                
                if not orchestrator_id or not knowledge_id:
                    issues.append("Failed to register simulation agents")
                else:
                    print(f"    ✓ Registered orchestrator: {orchestrator_id}")
                    print(f"    ✓ Registered knowledge agent: {knowledge_id}")
                    
                    # Submit test task
                    task_id = self.coordinator.submit_task(
                        "integration_test_task",
                        "Test task for agent integration validation",
                        ["knowledge_graph_management"],
                        TaskPriority.NORMAL
                    )
                    
                    if not task_id:
                        issues.append("Failed to submit test task")
                    else:
                        print(f"    ✓ Submitted test task: {task_id}")
                        
                        # Simulate task completion
                        success = self.coordinator.complete_task(
                            task_id,
                            {"test_result": "simulation_successful", "validation": "passed"}
                        )
                        
                        if not success:
                            issues.append("Failed to complete test task")
                        else:
                            print(f"    ✓ Completed test task")
                
            except Exception as e:
                issues.append(f"Error in workflow simulation: {e}")
        
        success = len(issues) == 0
        self.test_results.append({
            "test": test_name,
            "success": success,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed: {', '.join(issues)}")
        
        return success
    
    def test_nats_subject_compatibility(self):
        """Test NATS subject patterns are compatible with existing system"""
        test_name = "NATS Subject Compatibility"
        issues = []
        
        # Check subject patterns match expected formats
        if "subject_patterns" in self.nats_config:
            patterns = self.nats_config["subject_patterns"]
            
            # Validate hero namespace
            if "hero_core" in patterns:
                hero_pattern = patterns["hero_core"]["pattern"]
                if not hero_pattern.startswith("hero.v1."):
                    issues.append("Hero core pattern doesn't follow versioning convention")
            else:
                issues.append("Missing hero_core pattern definition")
            
            # Validate agent coordination patterns
            if "agent_coordination" in patterns:
                coord_subjects = patterns["agent_coordination"].get("subjects", {})
                required_subjects = ["task_assign", "task_status", "agent_register"]
                for subject in required_subjects:
                    if subject not in coord_subjects:
                        issues.append(f"Missing coordination subject: {subject}")
            else:
                issues.append("Missing agent_coordination pattern definition")
        else:
            issues.append("No subject patterns defined in NATS config")
        
        success = len(issues) == 0
        self.test_results.append({
            "test": test_name,
            "success": success,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        })
        
        if success:
            print(f"✅ {test_name} passed")
        else:
            print(f"❌ {test_name} failed: {', '.join(issues)}")
        
        return success
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        report = {
            "test_summary": {
                "total_tests": len(self.test_results),
                "passed_tests": len([r for r in self.test_results if r["success"]]),
                "failed_tests": len([r for r in self.test_results if not r["success"]]),
                "success_rate": len([r for r in self.test_results if r["success"]]) / len(self.test_results) if self.test_results else 0,
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results,
            "environment": {
                "hero_framework_available": HERO_AVAILABLE,
                "python_version": sys.version,
                "test_location": str(self.agents_dir)
            },
            "configuration_status": {
                "capabilities_config_loaded": bool(self.capabilities_config),
                "nats_config_loaded": bool(self.nats_config),
                "langsmith_config_loaded": bool(self.langsmith_config)
            }
        }
        
        # Save report
        report_file = self.cache_dir / "agent_integration_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📊 Test Report Generated: {report_file}")
        return report
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Agent Integration Tests...\n")
        
        tests = [
            self.test_configuration_validation,
            self.test_system_prompt_structure,
            self.test_template_structure,
            self.test_nats_subject_compatibility,
            self.test_hero_framework_integration,
            self.test_agent_workflow_simulation
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
            print()  # Add spacing between tests
        
        # Generate final report
        report = self.generate_test_report()
        
        print(f"🎯 Test Results: {passed_tests}/{total_tests} tests passed")
        print(f"📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed! Agent integration is ready for production.")
            return True
        else:
            print("⚠️  Some tests failed. Review the issues before deploying agents.")
            return False

def main():
    """Main test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Hero Agent Integration Tester")
    parser.add_argument("--test", choices=["config", "prompts", "templates", "nats", "integration", "workflow", "all"],
                       default="all", help="Specific test to run")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    tester = AgentIntegrationTester()
    
    if args.test == "all":
        success = tester.run_all_tests()
    elif args.test == "config":
        success = tester.test_configuration_validation()
    elif args.test == "prompts":
        success = tester.test_system_prompt_structure()
    elif args.test == "templates":
        success = tester.test_template_structure()
    elif args.test == "nats":
        success = tester.test_nats_subject_compatibility()
    elif args.test == "integration":
        success = tester.test_hero_framework_integration()
    elif args.test == "workflow":
        success = tester.test_agent_workflow_simulation()
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)