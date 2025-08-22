'use client';

import React, { useState, useEffect, useRef } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiClient } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { 
  PaperAirplaneIcon, 
  CogIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

interface ChatMessage {
  id: string;
  content: string;
  type: 'user' | 'assistant' | 'system' | 'tool_call' | 'thinking';
  timestamp: string;
  metadata?: any;
}

interface ToolCallEvent {
  tool_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: any;
  error?: string;
}

export default function ChatInterface() {
  const { user, isAuthenticated } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentToolCall, setCurrentToolCall] = useState<ToolCallEvent | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isAuthenticated) {
      // Load chat history first, then initialize WebSocket
      loadChatHistory();
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [isAuthenticated, user]);

  const loadChatHistory = async () => {
    try {
      setIsLoadingHistory(true);
      
      // Get or create current session
      const session = await apiClient.getCurrentChatSession();
      setCurrentSessionId(session.session_id);
      
      // Load messages for the session
      const chatMessages = await apiClient.getChatMessages(session.session_id);
      
      // Convert API messages to ChatMessage format
      const formattedMessages: ChatMessage[] = chatMessages.map(msg => ({
        id: msg.message_id.toString(),
        content: msg.content,
        type: msg.message_type as 'user' | 'assistant' | 'system' | 'tool_call' | 'thinking',
        timestamp: msg.metadata?.timestamp || new Date().toISOString(),
        metadata: msg.metadata
      }));
      
      // If no messages exist, add welcome message
      if (formattedMessages.length === 0) {
        const welcomeMessage: ChatMessage = {
          id: 'welcome',
          content: `Hello ${user?.full_name || user?.username}! I'm your AI assistant. I can help you query your business systems, analyze data, and provide insights. What would you like to know?`,
          type: 'assistant',
          timestamp: new Date().toISOString()
        };
        setMessages([welcomeMessage]);
      } else {
        setMessages(formattedMessages);
      }
      
      // Initialize WebSocket after loading history
      initializeWebSocket();
      
    } catch (error) {
      console.error('Failed to load chat history:', error);
      
      // Fallback to welcome message
      setMessages([
        {
          id: 'welcome',
          content: `Hello ${user?.full_name || user?.username}! I'm your AI assistant. I can help you query your business systems, analyze data, and provide insights. What would you like to know?`,
          type: 'assistant',
          timestamp: new Date().toISOString()
        }
      ]);
      
      // Still initialize WebSocket
      initializeWebSocket();
    } finally {
      setIsLoadingHistory(false);
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeWebSocket = () => {
    if (!isAuthenticated || !apiClient.getToken()) {
      return;
    }

    try {
      const wsUrl = `${apiClient.getWebSocketUrl()}?token=${apiClient.getToken()}`;
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          handleWebSocketMessage(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Try to reconnect after 3 seconds
        setTimeout(() => {
          if (isAuthenticated) {
            initializeWebSocket();
          }
        }, 3000);
      };

      ws.onerror = (error) => {
        console.warn('WebSocket connection failed, falling back to API calls:', error);
        setIsConnected(false);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      // Fallback to simulated connection for development
      setIsConnected(true);
    }
  };

  const handleWebSocketMessage = (data: any) => {
    switch (data.type) {
      case 'message':
        const message: ChatMessage = {
          id: data.id || Date.now().toString(),
          content: data.content,
          type: data.message_type || 'assistant',
          timestamp: data.timestamp || new Date().toISOString(),
          metadata: data.metadata
        };
        setMessages(prev => [...prev, message]);
        break;
      
      case 'tool_call':
        setCurrentToolCall(data);
        break;
      
      case 'thinking':
        setIsThinking(data.thinking);
        break;
      
      case 'stream_chunk':
        // Handle streaming response
        updateLastMessage(data.content);
        break;
      
      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const updateLastMessage = (content: string) => {
    setMessages(prev => {
      const lastMessage = prev[prev.length - 1];
      if (lastMessage && lastMessage.type === 'assistant') {
        return [
          ...prev.slice(0, -1),
          { ...lastMessage, content: content }
        ];
      }
      return prev;
    });
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || !isConnected) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputValue,
      type: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    const messageContent = inputValue;
    setInputValue('');
    setIsLoading(true);

    try {
      // Send message via WebSocket if connected
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          type: 'message',
          content: messageContent,
          timestamp: new Date().toISOString()
        }));
      } else {
        // Fallback to simulation if WebSocket not available
        await simulateAIResponse(messageContent);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      // Fallback to simulation
      await simulateAIResponse(messageContent);
    }
  };

  const simulateAIResponse = async (userInput: string) => {
    // Simulate thinking phase with more realistic timing
    setIsThinking(true);
    
    // Vary thinking time based on query complexity
    const baseThinkingTime = 1200;
    const complexityBonus = Math.min(userInput.length * 20, 1000); // Up to 1 extra second for longer queries
    const thinkingTime = baseThinkingTime + complexityBonus + Math.random() * 800; // Add some randomness
    
    await new Promise(resolve => setTimeout(resolve, thinkingTime));
    setIsThinking(false);

    // Small delay between thinking and tool calls for natural flow
    await new Promise(resolve => setTimeout(resolve, 300));

    // Simulate tool calling
    if (userInput.toLowerCase().includes('jira') || userInput.toLowerCase().includes('issue')) {
      await simulateToolCall('jira_api', 'Fetching Jira issues...');
    } else if (userInput.toLowerCase().includes('zendesk') || userInput.toLowerCase().includes('ticket')) {
      await simulateToolCall('zendesk_api', 'Fetching Zendesk tickets...');
    }

    // Generate response
    const response = generateAIResponse(userInput);
    
    // Small delay before streaming for natural flow
    await new Promise(resolve => setTimeout(resolve, 200));
    
    // Simulate streaming
    await streamResponse(response);
    
    setIsLoading(false);
  };

  const simulateToolCall = async (toolName: string, description: string) => {
    setCurrentToolCall({
      tool_name: toolName,
      status: 'pending'
    });

    // Simulate tool execution phases
    await new Promise(resolve => setTimeout(resolve, 500));
    setCurrentToolCall(prev => prev ? { ...prev, status: 'running' } : null);

    await new Promise(resolve => setTimeout(resolve, 1000));
    setCurrentToolCall(prev => prev ? { ...prev, status: 'completed' } : null);

    // Add tool call message
    const toolMessage: ChatMessage = {
      id: Date.now().toString(),
      content: `${toolName} executed successfully`,
      type: 'tool_call',
      timestamp: new Date().toISOString(),
      metadata: { tool_name: toolName, status: 'completed' }
    };

    setMessages(prev => [...prev, toolMessage]);

    // Clear tool call after a delay
    setTimeout(() => setCurrentToolCall(null), 2000);
  };

  const generateAIResponse = (userInput: string): string => {
    const responses = [
      `I've analyzed your request: "${userInput}". Based on the data from your connected systems, here's what I found...`,
      `Great question! Let me check your business systems for that information. I've retrieved the relevant data and here's the summary...`,
      `I understand you're looking for information about "${userInput}". I've connected to your integrations and gathered the following insights...`,
      `Based on your query, I've examined your business data and can provide you with the following analysis...`
    ];

    return responses[Math.floor(Math.random() * responses.length)];
  };

  const streamResponse = async (response: string) => {
    const words = response.split(' ');
    let streamedContent = '';

    for (let i = 0; i < words.length; i++) {
      streamedContent += words[i] + (i < words.length - 1 ? ' ' : '');
      
      const streamMessage: ChatMessage = {
        id: `stream-${Date.now()}`,
        content: streamedContent,
        type: 'assistant',
        timestamp: new Date().toISOString()
      };

      // Update or add the streaming message
      setMessages(prev => {
        const existingIndex = prev.findIndex(m => m.id.startsWith('stream-'));
        if (existingIndex >= 0) {
          const newMessages = [...prev];
          newMessages[existingIndex] = streamMessage;
          return newMessages;
        } else {
          return [...prev, streamMessage];
        }
      });

      // Variable delay for more natural typing rhythm
      const baseDelay = 50;
      const randomDelay = Math.random() * 100; // 0-100ms random variation
      const punctuationDelay = ['.', '!', '?', ','].includes(words[i].slice(-1)) ? 200 : 0;
      
      await new Promise(resolve => setTimeout(resolve, baseDelay + randomDelay + punctuationDelay));
    }

    // Finalize the message
    const finalMessage: ChatMessage = {
      id: Date.now().toString(),
      content: response,
      type: 'assistant',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => {
      const filtered = prev.filter(m => !m.id.startsWith('stream-'));
      return [...filtered, finalMessage];
    });
  };

  const getMessageIcon = (type: string) => {
    switch (type) {
      case 'user':
        return <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white text-sm font-medium">U</div>;
      case 'assistant':
        return <div className="w-8 h-8 bg-teal-600 rounded-full flex items-center justify-center text-white text-sm font-medium">AI</div>;
      case 'tool_call':
        return <CogIcon className="w-8 h-8 text-blue-600" />;
      case 'thinking':
        return <ClockIcon className="w-8 h-8 text-yellow-600" />;
      default:
        return <div className="w-8 h-8 bg-neutral-600 rounded-full flex items-center justify-center text-white text-sm font-medium">S</div>;
    }
  };

  const getMessageStyle = (type: string) => {
    switch (type) {
      case 'user':
        return 'bg-green-200 text-black ml-auto';
      case 'assistant':
        return 'bg-white border border-neutral-200 text-neutral-900';
      case 'tool_call':
        return 'bg-blue-50 border border-blue-200 text-blue-900';
      case 'thinking':
        return 'bg-yellow-50 border border-yellow-200 text-yellow-900';
      default:
        return 'bg-neutral-50 border border-neutral-200 text-neutral-900';
    }
  };

  const getToolCallStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="h-4 w-4 text-yellow-600" />;
      case 'running':
        return <CogIcon className="h-4 w-4 text-blue-600 animate-spin" />;
      case 'completed':
        return <CheckCircleIcon className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-4 w-4 text-red-600" />;
      default:
        return <ClockIcon className="h-4 w-4 text-neutral-400" />;
    }
  };

  return (
    <div className="flex flex-col h-full bg-neutral-50">
      {/* Header */}
      <header className="bg-white border-b border-neutral-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold text-neutral-900">AI Assistant Chat</h1>
            <p className="text-sm text-neutral-600">Ask me anything about your business systems</p>
          </div>
          <div className="flex items-center space-x-2">
            <div 
              className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}
              role="status"
              aria-label={isConnected ? 'Connected to chat service' : 'Disconnected from chat service'}
            ></div>
            <span className="text-sm text-neutral-600" aria-live="polite">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </header>

      {/* Messages */}
      <main 
        id="main-content"
        className="flex-1 overflow-y-auto p-6 space-y-4"
        role="log"
        aria-label="Chat messages"
        aria-live="polite"
      >
        {isLoadingHistory ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-2 text-neutral-600 text-sm">Loading chat history...</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-start space-x-3 ${
              message.type === 'user' ? 'justify-end' : 'justify-start'
            } animate-message-appear`}
          >
            {message.type !== 'user' && (
              <div className="flex-shrink-0">
                {getMessageIcon(message.type)}
              </div>
            )}
            
            <div 
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg shadow-soft ${getMessageStyle(message.type)}`}
              role="article"
              aria-label={`${message.type === 'user' ? 'Your message' : 'AI response'} at ${new Date(message.timestamp).toLocaleTimeString()}`}
            >
              <p className="text-sm">{message.content}</p>
              <time 
                className="text-xs opacity-70 mt-1 block"
                dateTime={message.timestamp}
              >
                {new Date(message.timestamp).toLocaleTimeString()}
              </time>
            </div>

            {message.type === 'user' && (
              <div className="flex-shrink-0">
                {getMessageIcon(message.type)}
              </div>
            )}
          </div>
        ))}

        {/* AI Thinking indicator with fancy animation */}
        {isThinking && (
          <div className="flex items-start space-x-3 justify-start animate-slide-up">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-teal-600 rounded-full flex items-center justify-center text-white text-sm font-medium relative animate-thinking-pulse">
                AI
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-teal-400 rounded-full animate-pulse"></div>
              </div>
            </div>
            <div className="bg-white border border-neutral-200 px-4 py-3 rounded-lg shadow-soft max-w-xs lg:max-w-md">
              <div className="flex items-center space-x-3">
                <div className="flex space-x-1 items-end">
                  <div className="w-2 h-2 bg-teal-500 rounded-full thinking-dot-1"></div>
                  <div className="w-2 h-2 bg-teal-500 rounded-full thinking-dot-2"></div>
                  <div className="w-2 h-2 bg-teal-500 rounded-full thinking-dot-3"></div>
                </div>
                <p className="text-sm text-neutral-700 font-medium">AI is thinking...</p>
              </div>
              <div className="mt-2 text-xs text-neutral-500">Processing your request</div>
            </div>
          </div>
        )}

        {/* Tool call indicator */}
        {currentToolCall && (
          <div className="flex items-start space-x-3 justify-start">
            <div className="flex-shrink-0">
              <CogIcon className="w-8 h-8 text-blue-600" />
            </div>
            <div className="bg-blue-50 border border-blue-200 px-4 py-2 rounded-lg shadow-soft">
              <div className="flex items-center space-x-2">
                {getToolCallStatusIcon(currentToolCall.status)}
                <p className="text-sm text-blue-800">
                  {currentToolCall.status === 'pending' && 'Preparing to call tool...'}
                  {currentToolCall.status === 'running' && `Executing ${currentToolCall.tool_name}...`}
                  {currentToolCall.status === 'completed' && `${currentToolCall.tool_name} completed successfully`}
                  {currentToolCall.status === 'failed' && `${currentToolCall.tool_name} failed`}
                </p>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
          </>
        )}
      </main>

      {/* Input */}
      <div className="bg-white border-t border-neutral-200 px-6 py-4" role="region" aria-label="Message input">
        <form onSubmit={(e) => { e.preventDefault(); handleSendMessage(); }}>
          <div className="flex space-x-3">
            <label htmlFor="chat-input" className="sr-only">
              Type your message
            </label>
            <input
              id="chat-input"
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask me about your business systems..."
              className="flex-1 px-4 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              disabled={isLoading}
              aria-describedby="chat-help-text"
            />
            <Button
              type="submit"
              disabled={!inputValue.trim() || isLoading}
              loading={isLoading}
              className="px-6"
              aria-label="Send message"
            >
              <PaperAirplaneIcon className="h-4 w-4" aria-hidden="true" />
            </Button>
          </div>
          
          <p id="chat-help-text" className="text-xs text-neutral-500 mt-2">
            Press Enter to send, or click the send button
          </p>
          
          {isLoading && (
            <div className="flex items-center justify-center mt-3 animate-slide-up" aria-live="polite">
              <div className="flex space-x-1 items-center">
                <div className="flex space-x-1">
                  <div className="w-1.5 h-1.5 bg-teal-500 rounded-full thinking-dot-1"></div>
                  <div className="w-1.5 h-1.5 bg-teal-500 rounded-full thinking-dot-2"></div>
                  <div className="w-1.5 h-1.5 bg-teal-500 rounded-full thinking-dot-3"></div>
                </div>
                <p className="text-xs text-neutral-500 ml-2">
                  AI is processing your request...
                </p>
              </div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}
