"""
Slack API integration tools.
"""
from typing import Dict, Any, List, Optional
import json
from datetime import datetime

from app.tools.base import BaseBusinessTool, ToolExecutionResult, ToolExecutionEvent, ToolCategory
from app.tools.registry import register_tool


@register_tool("slack", {"category": ToolCategory.COMMUNICATION, "priority": 1})
class SlackSendMessageTool(BaseBusinessTool):
    """Send messages to Slack channels or users."""
    
    @property
    def tool_name(self) -> str:
        return "slack_send_message"
    
    @property
    def description(self) -> str:
        return "Send messages to Slack channels or direct messages to users. Supports rich formatting, mentions, and attachments."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["bot_token"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test Slack connection by getting bot info."""
        headers = {
            "Authorization": f"Bearer {self.credentials.credentials['bot_token']}",
            "Content-Type": "application/json"
        }
        
        url = "https://slack.com/api/auth.test"
        
        response = await self._make_request("POST", url, headers=headers)
        auth_data = response.json()
        
        if not auth_data.get("ok"):
            raise ValueError(f"Slack auth failed: {auth_data.get('error', 'Unknown error')}")
        
        return {
            "bot_id": auth_data.get("bot_id"),
            "user": auth_data.get("user"),
            "team": auth_data.get("team"),
            "url": auth_data.get("url")
        }
    
    async def execute(
        self, 
        channel: str,
        text: str,
        username: Optional[str] = None,
        icon_emoji: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> ToolExecutionResult:
        """Send a message to Slack."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Sending message to {channel}"
            ))
            
            headers = {
                "Authorization": f"Bearer {self.credentials.credentials['bot_token']}",
                "Content-Type": "application/json"
            }
            
            # Build message payload
            message_data = {
                "channel": channel,
                "text": text
            }
            
            if username:
                message_data["username"] = username
            
            if icon_emoji:
                message_data["icon_emoji"] = icon_emoji
            
            if attachments:
                message_data["attachments"] = attachments
            
            url = "https://slack.com/api/chat.postMessage"
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Sending message to Slack..."
            ))
            
            response = await self._make_request("POST", url, headers=headers, data=message_data)
            result_data = response.json()
            
            if not result_data.get("ok"):
                raise ValueError(f"Slack API error: {result_data.get('error', 'Unknown error')}")
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message="Message sent successfully"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "message_ts": result_data.get("ts"),
                    "channel": result_data.get("channel"),
                    "text": text,
                    "permalink": f"https://slack.com/archives/{result_data.get('channel')}/p{result_data.get('ts', '').replace('.', '')}"
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "send_message", "channel": channel}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Message sending failed: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "send_message", "channel": channel}
            )


@register_tool("slack", {"category": ToolCategory.READ, "priority": 2})
class SlackGetChannelsTool(BaseBusinessTool):
    """Get list of Slack channels."""
    
    @property
    def tool_name(self) -> str:
        return "slack_get_channels"
    
    @property
    def description(self) -> str:
        return "Get a list of Slack channels that the bot has access to, including public channels, private channels, and DMs."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["bot_token"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test connection."""
        return {"status": "connected"}
    
    async def execute(
        self, 
        types: str = "public_channel,private_channel",
        limit: int = 100,
        **kwargs
    ) -> ToolExecutionResult:
        """Get Slack channels."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message="Getting Slack channels"
            ))
            
            headers = {
                "Authorization": f"Bearer {self.credentials.credentials['bot_token']}",
                "Content-Type": "application/json"
            }
            
            url = "https://slack.com/api/conversations.list"
            params = {
                "types": types,
                "limit": limit
            }
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Fetching channel list..."
            ))
            
            response = await self._make_request("GET", url, headers=headers, params=params)
            result_data = response.json()
            
            if not result_data.get("ok"):
                raise ValueError(f"Slack API error: {result_data.get('error', 'Unknown error')}")
            
            # Process channels
            channels = []
            for channel in result_data.get("channels", []):
                channel_info = {
                    "id": channel.get("id"),
                    "name": channel.get("name"),
                    "is_private": channel.get("is_private", False),
                    "is_archived": channel.get("is_archived", False),
                    "is_general": channel.get("is_general", False),
                    "num_members": channel.get("num_members", 0),
                    "topic": channel.get("topic", {}).get("value", ""),
                    "purpose": channel.get("purpose", {}).get("value", ""),
                    "created": channel.get("created")
                }
                channels.append(channel_info)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Retrieved {len(channels)} channels"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "channels": channels,
                    "total": len(channels)
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "get_channels"}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Failed to get channels: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "get_channels"}
            )


@register_tool("slack", {"category": ToolCategory.READ, "priority": 3})
class SlackGetMessagesTool(BaseBusinessTool):
    """Get messages from a Slack channel."""
    
    @property
    def tool_name(self) -> str:
        return "slack_get_messages"
    
    @property
    def description(self) -> str:
        return "Get recent messages from a Slack channel. Can retrieve message history with timestamps, users, and content."
    
    @property
    def required_credentials(self) -> List[str]:
        return ["bot_token"]
    
    async def _test_connection_impl(self) -> Dict[str, Any]:
        """Test connection."""
        return {"status": "connected"}
    
    async def execute(
        self, 
        channel: str,
        limit: int = 20,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
        **kwargs
    ) -> ToolExecutionResult:
        """Get messages from a Slack channel."""
        start_time = datetime.now()
        
        try:
            await self.emit_event(ToolExecutionEvent(
                type="start",
                tool_name=self.tool_name,
                message=f"Getting messages from {channel}"
            ))
            
            headers = {
                "Authorization": f"Bearer {self.credentials.credentials['bot_token']}",
                "Content-Type": "application/json"
            }
            
            url = "https://slack.com/api/conversations.history"
            params = {
                "channel": channel,
                "limit": limit
            }
            
            if oldest:
                params["oldest"] = oldest
            if latest:
                params["latest"] = latest
            
            await self.emit_event(ToolExecutionEvent(
                type="progress",
                tool_name=self.tool_name,
                message="Fetching message history..."
            ))
            
            response = await self._make_request("GET", url, headers=headers, params=params)
            result_data = response.json()
            
            if not result_data.get("ok"):
                raise ValueError(f"Slack API error: {result_data.get('error', 'Unknown error')}")
            
            # Process messages
            messages = []
            for message in result_data.get("messages", []):
                message_info = {
                    "ts": message.get("ts"),
                    "user": message.get("user"),
                    "text": message.get("text", ""),
                    "type": message.get("type", "message"),
                    "subtype": message.get("subtype"),
                    "bot_id": message.get("bot_id"),
                    "username": message.get("username"),
                    "timestamp": datetime.fromtimestamp(float(message.get("ts", 0))).isoformat() if message.get("ts") else None
                }
                messages.append(message_info)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.emit_event(ToolExecutionEvent(
                type="complete",
                tool_name=self.tool_name,
                message=f"Retrieved {len(messages)} messages"
            ))
            
            return ToolExecutionResult(
                success=True,
                data={
                    "messages": messages,
                    "channel": channel,
                    "has_more": result_data.get("has_more", False)
                },
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "get_messages", "channel": channel}
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            
            await self.emit_event(ToolExecutionEvent(
                type="error",
                tool_name=self.tool_name,
                message=f"Failed to get messages: {error_msg}"
            ))
            
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                tool_name=self.tool_name,
                execution_time=execution_time,
                metadata={"action": "get_messages", "channel": channel}
            )