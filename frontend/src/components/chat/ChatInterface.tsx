'use client';

import React, { useState, useEffect, useRef } from 'react';
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
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isConnected, setIsConnected] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [currentToolCall, setCurrentToolCall] = useState<ToolCallEvent | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Initialize WebSocket connection
    initializeWebSocket();
    
    // Add welcome message
    setMessages([
      {
        id: 'welcome',
        content: 'Hello! I\'m your AI assistant. I can help you query your business systems, analyze data, and provide insights. What would you like to know?',
        type: 'assistant',
        timestamp: new Date().toISOString()
      }
    ]);

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const initializeWebSocket = () => {
    // In real implementation, this would connect to the backend WebSocket
    // For now, simulate the connection
    setIsConnected(true);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content: inputValue,
      type: 'user',
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Simulate AI processing
    await simulateAIResponse(userMessage.content);
  };

  const simulateAIResponse = async (userInput: string) => {
    // Simulate thinking phase
    setIsThinking(true);
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsThinking(false);

    // Simulate tool calling
    if (userInput.toLowerCase().includes('jira') || userInput.toLowerCase().includes('issue')) {
      await simulateToolCall('jira_api', 'Fetching Jira issues...');
    } else if (userInput.toLowerCase().includes('zendesk') || userInput.toLowerCase().includes('ticket')) {
      await simulateToolCall('zendesk_api', 'Fetching Zendesk tickets...');
    }

    // Generate response
    const response = generateAIResponse(userInput);
    
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

      await new Promise(resolve => setTimeout(resolve, 100));
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
        return 'bg-primary-600 text-white ml-auto';
      case 'assistant':
        return 'bg-white border border-neutral-200';
      case 'tool_call':
        return 'bg-blue-50 border border-blue-200';
      case 'thinking':
        return 'bg-yellow-50 border border-yellow-200';
      default:
        return 'bg-neutral-50 border border-neutral-200';
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
      <div className="bg-white border-b border-neutral-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-neutral-900">AI Assistant Chat</h2>
            <p className="text-sm text-neutral-600">Ask me anything about your business systems</p>
          </div>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-neutral-600">
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex items-start space-x-3 ${
              message.type === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {message.type !== 'user' && (
              <div className="flex-shrink-0">
                {getMessageIcon(message.type)}
              </div>
            )}
            
            <div className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg shadow-soft ${getMessageStyle(message.type)}`}>
              <p className="text-sm">{message.content}</p>
              <p className="text-xs opacity-70 mt-1">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>

            {message.type === 'user' && (
              <div className="flex-shrink-0">
                {getMessageIcon(message.type)}
              </div>
            )}
          </div>
        ))}

        {/* Thinking indicator */}
        {isThinking && (
          <div className="flex items-start space-x-3 justify-start">
            <div className="flex-shrink-0">
              <ClockIcon className="w-8 h-8 text-yellow-600" />
            </div>
            <div className="bg-yellow-50 border border-yellow-200 px-4 py-2 rounded-lg shadow-soft">
              <p className="text-sm text-yellow-800">Thinking...</p>
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
      </div>

      {/* Input */}
      <div className="bg-white border-t border-neutral-200 px-6 py-4">
        <div className="flex space-x-3">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Ask me about your business systems..."
            className="flex-1 px-4 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            disabled={isLoading}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            loading={isLoading}
            className="px-6"
          >
            <PaperAirplaneIcon className="h-4 w-4" />
          </Button>
        </div>
        
        {isLoading && (
          <p className="text-xs text-neutral-500 mt-2 text-center">
            AI is processing your request...
          </p>
        )}
      </div>
    </div>
  );
}
