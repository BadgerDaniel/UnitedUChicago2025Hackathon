import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Bot, User, AlertCircle } from 'lucide-react';
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

const ChatInterfaceDemo: React.FC<ChatInterfaceProps> = ({ isExpanded }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'info',
      content: 'Demo Mode: Smart routing visualization (orchestrator not connected)',
      timestamp: new Date(),
    },
    {
      id: '2',
      type: 'assistant',
      content: `Hello! I'm your Flight Demand Assistant. In this demo, you can see how smart routing works. Try asking about:
• Flights from Chicago to Denver
• Weather conditions
• Latest United Airlines news
• Major events in cities`,
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const routingMessageId = useRef<string | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const updateRoutingMessage = (content: string, agent?: string) => {
    if (!routingMessageId.current) {
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

  const generateMockResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase();
    
    if (lowerQuery.includes('flight') || lowerQuery.includes('chicago') || lowerQuery.includes('denver')) {
      return `Based on analysis from FlightIntelligenceAgent:

**Chicago (ORD) → Denver (DEN) Flights**
• 12 daily flights available
• Price range: $189 - $542
• Average flight time: 2h 35m
• Best deals: Early morning (6-8 AM) and late evening (9-11 PM)
• Load factor: 87% (High demand)

Recommendation: Book soon as prices are trending upward.`;
    }
    
    if (lowerQuery.includes('weather')) {
      return `Based on data from AviationWeatherAgent:

**Current Aviation Weather**
• Denver (DEN): Clear, winds 5-10 kts from west
• Chicago (ORD): Partly cloudy, winds 10-15 kts from north
• No SIGMETs or AIRMETs in effect
• VFR conditions at both airports

Flight impact: Minimal - excellent flying conditions`;
    }
    
    if (lowerQuery.includes('news') || lowerQuery.includes('united')) {
      return `Based on GoogleNewsAgent analysis:

**Latest United Airlines News**
• New routes announced to European destinations
• Fleet expansion: 50 new aircraft on order
• Q3 earnings beat expectations by 12%
• Sustainability initiative: Net-zero by 2050
• Customer satisfaction scores up 8% YoY`;
    }
    
    if (lowerQuery.includes('event')) {
      return `Based on LiveEventsAgent data:

**Major Events Impact Analysis**
• Chicago: Tech Conference (Mon-Wed) - Expected 50,000 attendees
• Denver: Ski Season Opening - Increased weekend demand
• Both cities: Holiday shopping season starting

Recommendation: Expect higher prices during event dates`;
    }
    
    return `I've analyzed your request using our multi-agent system. The relevant agents have been consulted to provide comprehensive information about "${query}". 

For more specific information, please refine your query or connect the orchestrator on port 10000.`;
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
        
        // After a short delay, show the response
        setTimeout(() => {
          removeRoutingMessage();
          
          const aiResponse: Message = {
            id: (Date.now() + 1).toString(),
            type: 'assistant',
            content: generateMockResponse(userQuery),
            timestamp: new Date(),
            agent: predictions[predictions.length - 1]?.agent,
          };
          setMessages(prev => [...prev, aiResponse]);
          setIsTyping(false);
        }, 1000);
      }
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700 h-full flex flex-col">
      <div className="p-4 border-b border-gray-200 dark:border-slate-700">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white tracking-tight">
            Flight Demand Assistant
          </h2>
          <span className="px-3 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 rounded-full text-xs font-medium">
            Demo Mode
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.type === 'routing' ? (
              <div className="flex items-center space-x-2 max-w-[80%]">
                <div className="bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 rounded-lg p-3 animate-pulse">
                  <p className="text-sm font-medium">{message.content}</p>
                </div>
              </div>
            ) : message.type === 'info' ? (
              <div className="flex items-center space-x-2 max-w-[80%]">
                <AlertCircle className="w-5 h-5 text-blue-500" />
                <div className="bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-lg p-3">
                  <p className="text-sm">{message.content}</p>
                </div>
              </div>
            ) : message.type === 'error' ? (
              <div className="flex items-center space-x-2 max-w-[80%]">
                <AlertCircle className="w-5 h-5 text-red-500" />
                <div className="bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200 rounded-lg p-3">
                  <p className="text-sm">{message.content}</p>
                </div>
              </div>
            ) : (
              <div className={`flex max-w-[80%] ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'} items-start space-x-2`}>
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  message.type === 'user' 
                    ? 'bg-blue-600 text-white ml-2' 
                    : 'bg-gray-200 dark:bg-slate-700 text-gray-600 dark:text-gray-300 mr-2'
                }`}>
                  {message.type === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>
                <div className={`rounded-lg p-3 border ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white border-blue-700'
                    : 'bg-gray-100 dark:bg-slate-800 text-gray-900 dark:text-white border-gray-300 dark:border-slate-600'
                }`}>
                  <div className="text-sm whitespace-pre-line font-medium leading-relaxed">{message.content}</div>
                  <div className={`text-xs mt-1 opacity-70 font-medium ${
                    message.type === 'user' ? 'text-blue-100' : 'text-gray-500 dark:text-gray-400'
                  }`}>
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 border-t border-gray-200 dark:border-slate-700">
        <div className="flex space-x-3">
          <div className="flex-1">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Try: 'What flights from Chicago to Denver?' or 'Latest news about United Airlines'"
              className="w-full px-4 py-3 bg-gray-50 dark:bg-slate-800 border-2 border-gray-300 dark:border-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:focus:ring-blue-400 dark:focus:border-blue-400 resize-none text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-all duration-200 font-medium leading-relaxed hover:border-gray-400 dark:hover:border-slate-500"
              rows={2}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isTyping}
              className={`p-3 rounded-lg transition-all duration-200 flex items-center justify-center ${
                inputValue.trim() && !isTyping
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

export default ChatInterfaceDemo;