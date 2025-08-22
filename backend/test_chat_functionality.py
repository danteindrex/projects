#!/usr/bin/env python3
"""
Test script to verify chat functionality with real tool execution
"""
import asyncio
import json
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import get_db_session
from app.models.integration import Integration
from app.models.user import User
from app.tools.registry import tool_registry
from app.services.streaming_service import streaming_service

async def test_chat_with_real_tools():
    """Test that chat uses real tools, not simulated responses"""
    print("🧪 Testing Chat Functionality with Real Tools")
    print("=" * 50)
    
    # Get database session
    db = next(get_db_session())
    
    try:
        # Get a user and active integration
        user = db.query(User).first()
        active_integration = db.query(Integration).filter(Integration.status == 'active').first()
        
        if not user:
            print("❌ No users found in database")
            return False
            
        if not active_integration:
            print("❌ No active integrations found")
            print("🔧 Available integrations:")
            integrations = db.query(Integration).all()
            for i in integrations:
                print(f"  - {i.name} ({i.integration_type}) - Status: {i.status}")
            print("\n💡 To test real functionality, activate an integration through the UI")
            return False
        
        print(f"👤 Using user: {user.email} (ID: {user.id})")
        print(f"🔗 Using integration: {active_integration.name} ({active_integration.integration_type})")
        
        # Test tool registry
        print(f"\n🛠️  Available tools for {active_integration.integration_type}:")
        available_tools = tool_registry.get_available_tools(active_integration.integration_type.value)
        for tool in available_tools:
            print(f"  - {tool['name']}: {tool['description'][:60]}...")
        
        # Test streaming service with a sample query
        session_id = f"test_session_{user.id}_123"
        test_query = "search for repositories python"
        
        print(f"\n🔄 Testing streaming query: '{test_query}'")
        print("📡 Streaming response:")
        
        response_count = 0
        has_tool_calls = False
        final_response = None
        
        async for stream_event in streaming_service.process_query_streaming(
            test_query, str(user.id), session_id, db
        ):
            response_count += 1
            event_type = stream_event.get('type', 'unknown')
            content = stream_event.get('content', '')
            
            print(f"  [{response_count}] {event_type}: {content[:80]}...")
            
            if event_type == 'tool_call':
                has_tool_calls = True
                
            if event_type == 'final':
                final_response = stream_event
        
        print(f"\n📊 Test Results:")
        print(f"  - Total streaming events: {response_count}")
        print(f"  - Tool calls detected: {'✅ Yes' if has_tool_calls else '❌ No'}")
        print(f"  - Final response received: {'✅ Yes' if final_response else '❌ No'}")
        
        if final_response:
            data = final_response.get('data', {})
            print(f"  - Agent results: {len(data.get('agent_results', {}))}")
            print(f"  - Tools used: {data.get('tools_used', [])}")
        
        # Determine if real tools were used
        if has_tool_calls and final_response:
            print(f"\n🎉 SUCCESS: Chat is using REAL TOOLS, not simulated responses!")
            return True
        else:
            print(f"\n⚠️  WARNING: Chat may be using simulated responses or tools failed to execute")
            return False
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

async def main():
    """Main test function"""
    print("🚀 Starting Chat Functionality Test...")
    success = await test_chat_with_real_tools()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ CHAT FUNCTIONALITY VERIFIED!")
        print("The system uses real API tools for actual business actions.")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠️  CHAT FUNCTIONALITY NEEDS ATTENTION")
        print("Check integration credentials and status.")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())