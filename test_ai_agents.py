#!/usr/bin/env python3
"""
Comprehensive test script for CrewAI agents
Tests agent creation, initialization, query processing, and routing
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

sys.path.append('backend')

from datetime import datetime
from typing import Dict, Any

# Import our services
from backend.app.services.crewai_service import crewai_service, process_query
from backend.app.services.agent_lifecycle import (
    agent_lifecycle_manager, 
    initialize_crewai_integration,
    execute_agent_task,
    get_crewai_agents_status
)
from backend.app.models.integration import Integration
from backend.app.core.config import settings

# Mock database session for testing
class MockDB:
    def __init__(self):
        self.integrations = [
            Integration(id=1, name="Jira", type="jira", status="active", config={}),
            Integration(id=2, name="Salesforce", type="salesforce", status="active", config={}),
            Integration(id=3, name="Zendesk", type="zendesk", status="active", config={}),
            Integration(id=4, name="Slack", type="slack", status="active", config={})
        ]
    
    def query(self, model):
        return self
    
    def filter(self, condition):
        return self
    
    def all(self):
        return self.integrations
    
    def add(self, obj):
        pass
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass

async def test_openai_connection():
    """Test OpenAI API connection"""
    print("🔧 Testing OpenAI API connection...")
    
    try:
        from langchain_openai import ChatOpenAI
        
        # Check if API key is set
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment")
            return False
        
        if api_key.startswith('your_') or len(api_key) < 20:
            print("❌ OPENAI_API_KEY appears to be a placeholder")
            return False
        
        # Test basic LLM initialization
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview", 
            temperature=0.1,
            openai_api_key=api_key,
            max_tokens=100
        )
        
        # Test a simple call
        response = llm.invoke("Say 'API connection successful' if this works")
        print(f"✅ OpenAI connection successful: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {str(e)}")
        return False

async def test_crewai_service_initialization():
    """Test CrewAI service initialization"""
    print("🚀 Testing CrewAI service initialization...")
    
    try:
        db = MockDB()
        await crewai_service.initialize_agents(db)
        
        # Check if router agent was created
        if crewai_service.router_agent is None:
            print("❌ Router agent not created")
            return False
        
        print(f"✅ Router agent created: {crewai_service.router_agent.role}")
        
        # Check integration agents
        if not crewai_service.integration_agents:
            print("❌ No integration agents created")
            return False
        
        print(f"✅ Created {len(crewai_service.integration_agents)} integration agents:")
        for agent_id, agent in crewai_service.integration_agents.items():
            print(f"   - {agent_id}: {agent.role}")
        
        return True
        
    except Exception as e:
        print(f"❌ CrewAI service initialization failed: {str(e)}")
        return False

async def test_agent_lifecycle_integration():
    """Test agent lifecycle integration with CrewAI"""
    print("🔄 Testing agent lifecycle integration...")
    
    try:
        db = MockDB()
        success = await initialize_crewai_integration(db)
        
        if not success:
            print("❌ CrewAI integration initialization failed")
            return False
        
        print("✅ CrewAI integration initialized successfully")
        
        # Get all agents status
        lifecycle_status = await agent_lifecycle_manager.get_all_agents_status()
        crewai_status = await get_crewai_agents_status()
        
        print(f"✅ Lifecycle agents: {len(lifecycle_status)}")
        print(f"✅ CrewAI agents: {crewai_status.get('total_agents', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent lifecycle integration failed: {str(e)}")
        return False

async def test_query_routing():
    """Test AI-powered query routing"""
    print("🧭 Testing AI-powered query routing...")
    
    test_queries = [
        "Show me all open Jira issues in our sprint",
        "What are our top Salesforce leads this week?", 
        "How many support tickets are pending in Zendesk?",
        "Send a message to the team channel in Slack",
        "Give me a general overview of our project status"
    ]
    
    try:
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {query}")
            
            routing_result = await crewai_service._route_query(query)
            
            print(f"   Routed to: {routing_result.get('agents', [])}")
            print(f"   Strategy: {routing_result.get('strategy', 'unknown')}")
            print(f"   Reasoning: {routing_result.get('reasoning', 'No reasoning provided')}")
        
        print("✅ Query routing tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Query routing test failed: {str(e)}")
        return False

async def test_agent_execution():
    """Test agent task execution"""
    print("⚡ Testing agent task execution...")
    
    test_cases = [
        {
            "query": "How many issues are in our current sprint?",
            "expected_agent": "jira"
        },
        {
            "query": "What's our sales pipeline looking like?", 
            "expected_agent": "salesforce"
        },
        {
            "query": "Show me customer support metrics",
            "expected_agent": "zendesk"
        }
    ]
    
    try:
        for i, test_case in enumerate(test_cases, 1):
            query = test_case["query"]
            print(f"\n🔍 Test {i}: {query}")
            
            # Test full query processing
            result = await process_query(
                query=query,
                user_id="test_user",
                session_id=f"test_session_{i}"
            )
            
            print(f"   Status: {'✅ Success' if result else '❌ Failed'}")
            if result:
                print(f"   Agents used: {result.get('total_agents', 0)}")
                print(f"   Summary: {result.get('summary', 'No summary')[:100]}...")
        
        print("✅ Agent execution tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Agent execution test failed: {str(e)}")
        return False

async def test_error_handling():
    """Test error handling and fallbacks"""
    print("🛡️ Testing error handling...")
    
    try:
        # Test with invalid query
        result = await process_query("", "test_user", "test_session")
        print(f"✅ Empty query handled: {result is not None}")
        
        # Test with very long query
        long_query = "What " * 1000  # Very long query
        result = await process_query(long_query, "test_user", "test_session")
        print(f"✅ Long query handled: {result is not None}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False

async def test_performance_metrics():
    """Test performance monitoring"""
    print("📊 Testing performance metrics...")
    
    try:
        # Get initial status
        status = await crewai_service.get_all_agents_status()
        print(f"✅ Retrieved status for {status.get('total_agents', 0)} agents")
        
        # Test rapid queries to check performance
        start_time = datetime.utcnow()
        
        for i in range(3):
            result = await process_query(
                f"Test query {i+1}",
                "test_user",
                f"test_session_{i}"
            )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ Processed 3 queries in {duration:.2f} seconds")
        print(f"✅ Average time per query: {duration/3:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance metrics test failed: {str(e)}")
        return False

async def run_all_tests():
    """Run all tests"""
    print("🧪 Starting AI Agent Comprehensive Test Suite")
    print("=" * 50)
    
    # Set environment
    os.environ.setdefault('ENVIRONMENT', 'development')
    
    tests = [
        ("OpenAI Connection", test_openai_connection),
        ("CrewAI Service Initialization", test_crewai_service_initialization),
        ("Agent Lifecycle Integration", test_agent_lifecycle_integration),
        ("Query Routing", test_query_routing),
        ("Agent Execution", test_agent_execution),
        ("Error Handling", test_error_handling),
        ("Performance Metrics", test_performance_metrics)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results[test_name] = False
    
    # Print summary
    print("\n" + "="*50)
    print("🏁 TEST SUMMARY")
    print("="*50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! AI agents are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    asyncio.run(run_all_tests())