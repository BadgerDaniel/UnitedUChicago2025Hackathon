import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Bot, User, AlertCircle, CheckCircle, Brain, Plane, Cloud, Zap, Database, Newspaper, Globe } from 'lucide-react';
import { agentApi } from '../services/agentApi';
import { agentPredictor } from '../utils/agentPredictor';

interface Message {
  id: string;
  type: 'user' | 'assistant' | 'error' | 'info' | 'routing';
  content: string;
  timestamp: Date;
  agent?: string;
  isTemporary?: boolean;
}

interface ChatInterfaceProps {
  isExpanded: boolean;
}

const ChatInterfaceSmartRouting: React.FC<ChatInterfaceProps> = ({ isExpanded }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hello! I\'m your Flight Demand Assistant powered by a multi-agent system. I can help you analyze route demand, weather impacts, events, and provide forecasting insights. What would you like to know?',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const routingMessageId = useRef<string | null>(null);

  const quickSuggestions = [
    'What\'s the current weather at Chicago O\'Hare airport?',
    'Find recent news about United Airlines flight delays',
    'What concerts are happening in Denver this weekend?',
    'What\'s the current GDP growth rate for the United States?',
  ];

  // Check connection status on mount
  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkConnection = async () => {
    const isConnected = await agentApi.checkHealth();
    setConnectionStatus(isConnected ? 'connected' : 'disconnected');
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const getAgentIcon = (agentName: string) => {
    if (agentName.includes('Flight')) return <Plane className="w-4 h-4" />;
    if (agentName.includes('Weather')) return <Cloud className="w-4 h-4" />;
    if (agentName.includes('Events')) return <Zap className="w-4 h-4" />;
    if (agentName.includes('Economic')) return <Database className="w-4 h-4" />;
    if (agentName.includes('News')) return <Newspaper className="w-4 h-4" />;
    if (agentName.includes('Web')) return <Globe className="w-4 h-4" />;
    if (agentName.includes('Orchestrator')) return <Brain className="w-4 h-4" />;
    return <Bot className="w-4 h-4" />;
  };

  const updateRoutingMessage = (content: string, agent?: string) => {
    if (!routingMessageId.current) {
      // Create initial routing message
      routingMessageId.current = Date.now().toString();
      const routingMessage: Message = {
        id: routingMessageId.current,
        type: 'routing',
        content: content,
        timestamp: new Date(),
        agent: agent,
        isTemporary: true,
      };
      setMessages(prev => [...prev, routingMessage]);
    } else {
      // Update existing routing message
      setMessages(prev => prev.map(msg => 
        msg.id === routingMessageId.current
          ? { ...msg, content: content, agent: agent }
          : msg
      ));
    }
  };

  const removeRoutingMessage = () => {
    if (routingMessageId.current) {
      setMessages(prev => prev.filter(msg => msg.id !== routingMessageId.current));
      routingMessageId.current = null;
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    const userQuery = inputValue;
    setInputValue('');
    setIsTyping(true);
    
    // Predict which agents will be involved
    const predictions = agentPredictor.predictAgents(userQuery);
    
    // Show orchestrator analyzing
    updateRoutingMessage('🧠 Orchestrator analyzing your request...');
    
    // Simulate showing relevant agents only
    let agentIndex = 1;
    const relevantAgentInterval = setInterval(() => {
      if (agentIndex < predictions.length) {
        const pred = predictions[agentIndex];
        updateRoutingMessage(
          `${pred.icon} Routing to ${pred.agent.replace('Agent', '')}: ${pred.reason}...`,
          pred.agent
        );
        agentIndex++;
      } else {
        clearInterval(relevantAgentInterval);
        updateRoutingMessage('✨ Preparing response...');
      }
    }, 1500);

    try {
      const response = await agentApi.sendMessage(userQuery);
      
      // Stop showing routing and clear interval
      clearInterval(relevantAgentInterval);
      removeRoutingMessage();
      
      if (response.success && response.response) {
        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          type: 'assistant',
          content: response.response,
          timestamp: new Date(),
          agent: response.agent,
        };
        setMessages(prev => [...prev, aiResponse]);
        setConnectionStatus('connected');
      } else {
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'error',
          content: response.error || 'An error occurred while processing your request.',
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
        
        if (response.error?.includes('Cannot connect')) {
          setConnectionStatus('disconnected');
        }
      }
    } catch (error) {
      clearInterval(relevantAgentInterval);
      removeRoutingMessage();
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'error',
        content: 'Failed to send message. Please check your connection.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setConnectionStatus('disconnected');
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700 h-full flex flex-col">
      {/* Header with Connection Status */}
      <div className="p-4 border-b border-gray-200 dark:border-slate-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white tracking-tight">Flight Demand Assistant</h2>
        <div className="flex items-center space-x-2">
          {connectionStatus === 'connected' && (
            <div className="flex items-center space-x-1 text-green-600 dark:text-green-400">
              <CheckCircle className="w-4 h-4" />
              <span className="text-xs font-medium">Connected</span>
            </div>
          )}
          {connectionStatus === 'disconnected' && (
            <div className="flex items-center space-x-1 text-red-600 dark:text-red-400">
              <AlertCircle className="w-4 h-4" />
              <span className="text-xs font-medium">Disconnected</span>
            </div>
          )}
          {connectionStatus === 'checking' && (
            <div className="flex items-center space-x-1 text-yellow-600 dark:text-yellow-400">
              <div className="w-4 h-4 border-2 border-yellow-600 dark:border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
              <span className="text-xs font-medium">Connecting...</span>
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => {
          // Extract agent name from routing messages
          let agentName = '';
          let agentIcon = <Bot className="w-4 h-4" />;
          
          if (message.type === 'routing' && message.content.includes(':')) {
            const parts = message.content.split(':');
            if (parts.length > 0) {
              // Extract agent name without emoji
              const rawAgent = parts[0].replace(/[🧠✈️🌤️🎉📊📰🌐🔄✨]/g, '').trim();
              agentName = rawAgent;
              agentIcon = getAgentIcon(message.agent || rawAgent);
            }
          }
          
          return (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex max-w-[80%] ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'} items-start space-x-2`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  message.type === 'user' 
                    ? 'bg-blue-600 text-white ml-2' 
                    : message.type === 'error'
                    ? 'bg-red-600 text-white mr-2'
                    : message.type === 'routing'
                    ? 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white mr-2 animate-pulse'
                    : 'bg-gray-200 dark:bg-slate-700 text-gray-600 dark:text-gray-300 mr-2'
                }`}>
                  {message.type === 'routing' ? agentIcon : 
                   message.type === 'user' ? <User className="w-4 h-4" /> :
                   message.type === 'error' ? <AlertCircle className="w-4 h-4" /> :
                   <Bot className="w-4 h-4" />}
                </div>
                <div className={`rounded-lg p-3 border ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white border-blue-700'
                    : message.type === 'error'
                    ? 'bg-red-50 dark:bg-red-900/20 text-red-900 dark:text-red-200 border-red-300 dark:border-red-800'
                    : message.type === 'routing'
                    ? 'bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 text-indigo-900 dark:text-indigo-200 border-indigo-300 dark:border-indigo-800'
                    : 'bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white border-gray-300 dark:border-slate-600'
                } ${message.type === 'routing' ? 'transition-all duration-300' : ''}`}>
                  <div className="text-sm whitespace-pre-line font-medium leading-relaxed">
                    {message.content}
                  </div>
                  {!message.isTemporary && (
                    <div className={`text-xs mt-1 opacity-70 font-medium flex items-center justify-between ${
                      message.type === 'user' ? 'text-blue-100' : 
                      message.type === 'error' ? 'text-red-600 dark:text-red-400' : 
                      message.type === 'routing' ? 'text-indigo-600 dark:text-indigo-400' :
                      'text-gray-500 dark:text-gray-400'
                    }`}>
                      <span>{message.timestamp.toLocaleTimeString()}</span>
                      {message.agent && (
                        <span className="ml-2 text-xs bg-gray-200 dark:bg-slate-700 px-2 py-0.5 rounded-full">
                          via {message.agent}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Connection Warning */}
      {connectionStatus === 'disconnected' && (
        <div className="mx-4 mb-2 p-3 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-300 dark:border-yellow-800 rounded-lg">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-yellow-600 dark:text-yellow-400" />
            <p className="text-sm text-yellow-800 dark:text-yellow-200 font-medium">
              Not connected to agent system. Make sure the orchestrator is running on port 10000.
            </p>
          </div>
        </div>
      )}

      {/* Quick Suggestions */}
      <div className="p-4 border-t border-gray-200 dark:border-slate-700">
        <div className="flex flex-wrap gap-2 mb-4">
          {quickSuggestions.map((suggestion) => (
            <button
              key={suggestion}
              className="px-3 py-1 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-gray-300 rounded-full text-sm font-medium border-2 border-gray-300 dark:border-slate-600 hover:bg-gray-200 dark:hover:bg-slate-700 hover:border-gray-400 dark:hover:border-slate-500 transition-all duration-200"
              onClick={() => setInputValue(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>

        {/* Input Area */}
        <div className="flex space-x-3">
          <div className="flex-1">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about flight demand, routes, or predictions..."
              className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border-2 border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 resize-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-200 font-medium leading-relaxed hover:border-gray-400 dark:hover:border-slate-500"
              rows={2}
              disabled={isTyping}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isTyping || connectionStatus === 'disconnected'}
              className={`p-3 rounded-lg transition-all duration-200 flex items-center justify-center ${
                inputValue.trim() && !isTyping && connectionStatus !== 'disconnected'
                  ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-xl transform hover:scale-105'
                  : 'bg-gray-200 dark:bg-slate-700 text-gray-400 dark:text-slate-500 cursor-not-allowed'
              }`}
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterfaceSmartRouting;