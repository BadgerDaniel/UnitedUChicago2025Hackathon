import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Bot, User } from 'lucide-react';

interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatInterfaceProps {
  isExpanded: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ isExpanded }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: 'Hello! I\'m your Flight Demand Assistant. I can help you analyze route demand, weather impacts, and provide forecasting insights. What would you like to know?',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const quickSuggestions = [
    'Chicago to Denver demand',
    'Weekend demand trends',
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Simulate AI response
    setTimeout(() => {
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: generateResponse(inputValue),
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1500);
  };

  const generateResponse = (input: string): string => {
    const lowerInput = input.toLowerCase();
    
    if (lowerInput.includes('chicago') && lowerInput.includes('denver')) {
      return `**Chicago to Denver Route Analysis**

**Current Demand**: Very High (97% load factor)
**Trend**: ↗️ Increasing (+12% vs last week)
**Peak Days**: Monday, Friday
**Recommended Actions**:
• Consider additional capacity
• Dynamic pricing optimization
• Monitor competitor activity

**Weather Impact**: Minimal (clear conditions forecasted)
**Events**: No major events affecting demand`;
    }
    
    if (lowerInput.includes('weekend')) {
      return `**Weekend Demand Patterns**

**Overall Trend**: Leisure travel dominates weekends
**High Demand Routes**:
• Chicago → Denver (97% load factor)
• New York → Los Angeles (95% load factor)
• Atlanta → Dallas (87% load factor)

**Recommendations**:
• Increase leisure route capacity
• Adjust pricing for business routes
• Monitor holiday weekend patterns`;
    }
    
    if (lowerInput.includes('weather')) {
      return `**Weather Impact Analysis**

**Current Conditions**: Generally favorable
**Affected Routes**: 
• Seattle routes (minor delays expected)
• Denver hub (clear conditions)

**Forecast Impact**: 
• Next 48 hours: Minimal disruption
• Weekend: Potential weather system in Northeast
• Recommendation: Monitor JFK operations`;
    }
    
    return `I understand you're asking about "${input}". Let me analyze the current flight demand data and provide you with insights. 

**Key Metrics**:
• Overall network load factor: 84%
• High-demand routes identified: 12
• Weather-affected routes: 2
• Trending upward: 67% of routes

Would you like me to dive deeper into any specific aspect of flight demand forecasting?`;
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700 h-full flex flex-col">
      {/* Clean Header - Only Title */}
      <div className="p-4 border-b border-gray-200 dark:border-slate-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white tracking-tight">Flight Demand Assistant</h2>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
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
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="flex items-start space-x-2">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-gray-200 dark:bg-slate-700 text-gray-600 dark:text-gray-300">
                <Bot className="w-4 h-4" />
              </div>
              <div className="bg-gray-100 dark:bg-slate-800 border border-gray-300 dark:border-slate-600 rounded-lg p-3">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

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
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleSendMessage}
              disabled={!inputValue.trim()}
              className={`p-3 rounded-lg transition-all duration-200 flex items-center justify-center ${
                inputValue.trim()
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

export default ChatInterface;