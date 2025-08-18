#!/usr/bin/env python3
"""
Simple AI agent test without external dependencies
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from crewai import Agent as CrewAIAgent, Task, Crew
from langchain_openai import ChatOpenAI

async def test_basic_crewai():
    """Test basic CrewAI functionality"""
    print("🧪 Testing basic CrewAI functionality...")
    
    try:
        # Check API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found")
            return False
        
        print("✅ OpenAI API key found")
        
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,
            openai_api_key=api_key
        )
        print("✅ LLM initialized")
        
        # Create a simple agent
        test_agent = CrewAIAgent(
            role="Test Agent",
            goal="Answer user questions helpfully",
            backstory="You are a helpful AI assistant for testing purposes.",
            verbose=True,
            llm=llm
        )
        print("✅ Agent created")
        
        # Create a simple task
        test_task = Task(
            description="Say 'Hello, AI agents are working!' and explain briefly what you do.",
            agent=test_agent
        )
        print("✅ Task created")
        
        # Create crew and execute
        crew = Crew(
            agents=[test_agent],
            tasks=[test_task],
            verbose=True
        )
        print("✅ Crew created")
        
        print("🚀 Executing task...")
        result = crew.kickoff()
        
        print(f"✅ Task completed successfully!")
        print(f"📝 Result: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

async def test_specialized_agents():
    """Test specialized integration agents"""
    print("\n🎯 Testing specialized agents...")
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,
            openai_api_key=api_key
        )
        
        # Create specialized agents
        jira_agent = CrewAIAgent(
            role="Jira Integration Specialist",
            goal="Handle Jira-related queries and project management tasks",
            backstory="""You are an expert in Jira project management and issue tracking. 
            You can help with issues, sprints, projects, and reporting.""",
            verbose=True,
            llm=llm
        )
        
        salesforce_agent = CrewAIAgent(
            role="Salesforce CRM Expert", 
            goal="Manage Salesforce data and customer relationships",
            backstory="""You are a Salesforce CRM specialist who excels at managing 
            customer relationships and sales pipelines.""",
            verbose=True,
            llm=llm
        )
        
        print("✅ Specialized agents created")
        
        # Test queries
        test_cases = [
            ("How can I track sprint progress in Jira?", jira_agent),
            ("What's the best way to manage leads in Salesforce?", salesforce_agent)
        ]
        
        for query, agent in test_cases:
            print(f"\n📝 Testing: {query}")
            
            task = Task(
                description=f"Answer this question: {query}",
                agent=agent
            )
            
            crew = Crew(
                agents=[agent],
                tasks=[task],
                verbose=False  # Less verbose for cleaner output
            )
            
            result = crew.kickoff()
            print(f"✅ Response: {str(result)[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Specialized agents test failed: {str(e)}")
        return False

async def test_multi_agent_collaboration():
    """Test multiple agents working together"""
    print("\n🤝 Testing multi-agent collaboration...")
    
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,
            openai_api_key=api_key
        )
        
        # Create router agent
        router_agent = CrewAIAgent(
            role="System Router and Orchestrator",
            goal="Route queries and coordinate responses from specialist agents",
            backstory="""You are an intelligent routing system that coordinates 
            between different business system specialists.""",
            verbose=True,
            allow_delegation=True,
            llm=llm
        )
        
        # Create integration agent
        integration_agent = CrewAIAgent(
            role="Integration Specialist",
            goal="Provide specific technical information about business systems",
            backstory="""You are an expert in business system integrations 
            and can provide detailed technical guidance.""",
            verbose=True,
            llm=llm
        )
        
        print("✅ Multi-agent system created")
        
        # Create collaborative task
        router_task = Task(
            description="""Analyze this request: 'I need to set up automated reporting 
            that pulls data from multiple business systems.' 
            
            Provide a high-level plan and coordination strategy.""",
            agent=router_agent
        )
        
        integration_task = Task(
            description="""Based on the router's analysis, provide specific technical 
            details about implementing automated reporting across business systems.""",
            agent=integration_agent
        )
        
        # Execute collaborative crew
        crew = Crew(
            agents=[router_agent, integration_agent],
            tasks=[router_task, integration_task],
            verbose=True
        )
        
        print("🚀 Executing collaborative task...")
        result = crew.kickoff()
        
        print(f"✅ Collaborative task completed!")
        print(f"📝 Result: {str(result)[:300]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Multi-agent collaboration test failed: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Simple AI Agent Test Suite")
    print("=" * 40)
    
    tests = [
        ("Basic CrewAI", test_basic_crewai),
        ("Specialized Agents", test_specialized_agents), 
        ("Multi-Agent Collaboration", test_multi_agent_collaboration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*15} {test_name} {'='*15}")
        
        try:
            success = await test_func()
            results[test_name] = success
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*40)
    print("🏁 TEST SUMMARY")
    print("="*40)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All AI agent tests passed!")
    else:
        print("⚠️ Some tests failed.")

if __name__ == "__main__":
    asyncio.run(main())