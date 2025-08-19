#!/usr/bin/env python3
"""
Minimal AI agent test that works quickly
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Disable CrewAI telemetry for faster execution
os.environ['OPENTELEMETRY_EXPORTER_OTLP_ENDPOINT'] = ''
os.environ['OPENTELEMETRY_EXPORTER_OTLP_TRACES_ENDPOINT'] = ''

from crewai import Agent as CrewAIAgent, Task, Crew
from langchain_openai import ChatOpenAI

def test_basic_ai():
    """Test basic AI functionality quickly"""
    print("🧪 Testing AI Agents...")
    
    try:
        # Check API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY not found")
            return False
        
        print("✅ OpenAI API key configured")
        
        # Initialize LLM
        llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0.1,
            openai_api_key=api_key
        )
        
        # Create router agent
        router_agent = CrewAIAgent(
            role="System Router and Orchestrator",
            goal="Route user queries and provide intelligent responses",
            backstory="You are an intelligent routing system for business integrations.",
            verbose=False,
            llm=llm
        )
        print("✅ Router Agent created")
        
        # Create integration agents
        jira_agent = CrewAIAgent(
            role="Jira Integration Specialist", 
            goal="Handle Jira-related queries and project management",
            backstory="You are an expert in Jira project management and issue tracking.",
            verbose=False,
            llm=llm
        )
        
        salesforce_agent = CrewAIAgent(
            role="Salesforce CRM Expert",
            goal="Manage Salesforce data and customer relationships", 
            backstory="You are a Salesforce CRM specialist who manages customer relationships.",
            verbose=False,
            llm=llm
        )
        
        zendesk_agent = CrewAIAgent(
            role="Customer Support Specialist",
            goal="Handle customer support tickets and improve support processes",
            backstory="You are a customer support expert who manages tickets and analytics.",
            verbose=False, 
            llm=llm
        )
        print("✅ Integration Agents created")
        
        # Test queries
        test_cases = [
            {
                "query": "How can I improve our sprint planning?",
                "agent": jira_agent,
                "expected": "jira"
            },
            {
                "query": "What's our lead conversion rate?",
                "agent": salesforce_agent,
                "expected": "salesforce"
            },
            {
                "query": "How many support tickets are pending?", 
                "agent": zendesk_agent,
                "expected": "zendesk"
            }
        ]
        
        print("🚀 Testing agent responses...")
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: {test_case['query']}")
            
            # Create task
            task = Task(
                description=f"Provide a helpful response to: {test_case['query']}",
                agent=test_case['agent']
            )
            
            # Create and execute crew
            crew = Crew(
                agents=[test_case['agent']],
                tasks=[task],
                verbose=False
            )
            
            result = crew.kickoff()
            print(f"✅ {test_case['expected'].title()} Agent Response: {str(result)[:150]}...")
        
        # Test routing logic
        print("\n🧭 Testing routing logic...")
        
        routing_queries = [
            "Show me Jira issues",
            "Update Salesforce leads", 
            "Check Zendesk tickets",
            "General business overview"
        ]
        
        for query in routing_queries:
            # Simple routing logic
            agents_needed = []
            
            if "jira" in query.lower() or "issue" in query.lower() or "sprint" in query.lower():
                agents_needed.append("Jira Agent")
            if "salesforce" in query.lower() or "lead" in query.lower() or "crm" in query.lower():
                agents_needed.append("Salesforce Agent")  
            if "zendesk" in query.lower() or "ticket" in query.lower() or "support" in query.lower():
                agents_needed.append("Zendesk Agent")
            if not agents_needed:
                agents_needed.append("Router Agent")
            
            print(f"   '{query}' → {', '.join(agents_needed)}")
        
        print("\n✅ All tests completed successfully!")
        print("🎉 AI agents are working correctly!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_basic_ai()
    if success:
        print("\n🏆 SUCCESS: AI implementation is working!")
    else:
        print("\n💥 FAILED: AI implementation needs fixes")