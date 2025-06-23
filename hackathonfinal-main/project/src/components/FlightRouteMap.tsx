import React, { useState, useEffect } from 'react';
import { Maximize2, Minimize2, Network, Zap, Database, Cloud, Globe, Newspaper, Plane, Bot, Activity, X } from 'lucide-react';

interface Agent {
  name: string;
  port: number;
  role: string;
  capabilities: string[];
  tools: string[];
  mcp_servers: string[];
  collaborates_with?: string[];
  isActive: boolean;
}

interface FlightRouteMapProps {
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

const FlightRouteMap: React.FC<FlightRouteMapProps> = ({ isCollapsed, onToggleCollapse }) => {
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);

  // Initialize agents with mock activity
  useEffect(() => {
    const agentData: Omit<Agent, 'isActive'>[] = [
      {
        name: "OrchestratorAgent",
        port: 10002,
        role: "Central Coordinator",
        capabilities: [
          "Route requests to specialized agents",
          "Multi-agent coordination",
          "Automatic agent discovery",
          "Failover handling"
        ],
        tools: ["list_agents", "delegate_task"],
        mcp_servers: []
      },
      {
        name: "FlightIntelligenceAgent",
        port: 10008,
        role: "Flight Search & Pricing",
        capabilities: [
          "Real-time flight search",
          "Route analysis",
          "Price comparison",
          "Delay predictions"
        ],
        tools: [
          "flight-offers-search",
          "airport-routes",
          "search_flights",
          "get_offer_details"
        ],
        mcp_servers: ["amadeus_flight", "duffel_flight", "flight_sql"]
      },
      {
        name: "LiveEventsAgent",
        port: 10004,
        role: "Event Impact Analysis",
        capabilities: [
          "Event discovery by city/date",
          "Attendance estimation",
          "Flight demand impact"
        ],
        tools: ["get_upcoming_events"],
        mcp_servers: ["live_events"]
      },
      {
        name: "AviationWeatherAgent",
        port: 10005,
        role: "Aviation Weather Intelligence",
        capabilities: [
          "METAR/TAF reports",
          "Route weather briefings",
          "Pilot reports",
          "Hub weather analysis"
        ],
        tools: ["get_metar", "get_taf", "get_pireps", "get_route_weather"],
        mcp_servers: ["aviation_weather"]
      },
      {
        name: "EconomicIndicatorsAgent",
        port: 10006,
        role: "Economic Data Analysis",
        capabilities: [
          "GDP & inflation tracking",
          "Exchange rate analysis",
          "Investment flow metrics",
          "Economic impact on travel"
        ],
        tools: ["imf_datasets", "imf_indicators"],
        mcp_servers: ["imf_data"],
        collaborates_with: ["GoogleNewsAgent"]
      },
      {
        name: "GoogleNewsAgent",
        port: 10007,
        role: "News Impact Analysis",
        capabilities: [
          "Aviation industry news",
          "United Airlines coverage",
          "Route-specific news",
          "Economic news correlation"
        ],
        tools: ["google_news_search", "get_economic_analysis"],
        mcp_servers: ["google_news"],
        collaborates_with: ["EconomicIndicatorsAgent"]
      },
      {
        name: "WebScrapingAgent",
        port: 10002,
        role: "Web Content Extraction",
        capabilities: [
          "Static content fetching",
          "Browser automation",
          "Form interaction",
          "Screenshot capture"
        ],
        tools: ["fetch", "navigate", "click", "fill", "screenshot"],
        mcp_servers: ["fetch", "playwright"]
      }
    ];

    const initialAgents: Agent[] = agentData.map(agent => ({
      ...agent,
      isActive: agent.name === "OrchestratorAgent" ? true : Math.random() > 0.4
    }));

    setAgents(initialAgents);

    // Simulate agent activity changes
    const interval = setInterval(() => {
      setAgents(prev => prev.map(agent => ({
        ...agent,
        isActive: agent.name === "OrchestratorAgent" ? true : Math.random() > 0.3
      })));
    }, 4000);

    return () => clearInterval(interval);
  }, []);

  const getAgentIcon = (agentName: string) => {
    switch (agentName) {
      case "OrchestratorAgent": return Network;
      case "FlightIntelligenceAgent": return Plane;
      case "LiveEventsAgent": return Zap;
      case "AviationWeatherAgent": return Cloud;
      case "EconomicIndicatorsAgent": return Database;
      case "GoogleNewsAgent": return Newspaper;
      case "WebScrapingAgent": return Globe;
      default: return Bot;
    }
  };

  const getAgentPosition = (agentName: string, index: number, total: number) => {
    const angle = (index * 2 * Math.PI) / total;
    const radius = 40; // Reduced radius to give more space
    const centerX = 50;
    const centerY = 50;
    
    const x = centerX + (radius * Math.cos(angle - Math.PI / 2)) * 0.8;
    const y = centerY + (radius * Math.sin(angle - Math.PI / 2)) * 0.8;
    
    return { x, y };
  };

  const orchestrator = agents.find(agent => agent.name === "OrchestratorAgent");
  const otherAgents = agents.filter(agent => agent.name !== "OrchestratorAgent");

  return (
    <div className="bg-white dark:bg-slate-900 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700 h-full w-full flex flex-col transition-all duration-300 relative">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-slate-700 flex items-center justify-between">
        <div className={`transition-all duration-300 ${isCollapsed ? 'opacity-0 w-0 overflow-hidden' : 'opacity-100'}`}>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white whitespace-nowrap tracking-tight">Agent Architecture</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400 font-medium">Multi-Agent System Network</p>
        </div>
        <button
          onClick={onToggleCollapse}
          className="p-2 rounded-lg bg-gray-100 dark:bg-slate-800 hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors flex-shrink-0 border-2 border-gray-300 dark:border-slate-600 hover:border-gray-400 dark:hover:border-slate-500"
        >
          {isCollapsed ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
        </button>
      </div>

      {/* Content Area */}
      <div className="flex-1 relative overflow-hidden">
        {/* Collapsed State */}
        <div className={`absolute inset-0 flex items-center justify-center transition-all duration-300 ${
          isCollapsed ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'
        }`}>
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center mb-3 shadow-sm">
              <Network className="w-6 h-6 text-white" />
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400 font-medium tracking-wide">Architecture</span>
          </div>
        </div>

        {/* Expanded State - Main Visualization (Always Full Width) */}
        <div className={`absolute inset-0 transition-all duration-300 ${
          !isCollapsed ? 'opacity-100 scale-100' : 'opacity-0 scale-95 pointer-events-none'
        }`}>
          <div className="h-full p-6">
            <div className="h-full bg-gradient-to-br from-gray-50 to-gray-100 dark:from-slate-800 dark:to-slate-700 rounded-xl border-2 border-gray-200 dark:border-slate-600 relative overflow-hidden">
              
              {/* Background Grid Pattern */}
              <div className="absolute inset-0 opacity-20">
                <div className="absolute inset-0" style={{
                  backgroundImage: `
                    linear-gradient(rgba(59, 130, 246, 0.1) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(59, 130, 246, 0.1) 1px, transparent 1px)
                  `,
                  backgroundSize: '20px 20px'
                }}></div>
              </div>

              {/* SVG for all connections */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none">
                {/* Orchestrator to Agent connections */}
                {otherAgents.map((agent, index) => {
                  const pos = getAgentPosition(agent.name, index, otherAgents.length);
                  return (
                    <line
                      key={`orchestrator-${agent.name}`}
                      x1="50%"
                      y1="50%"
                      x2={`${pos.x}%`}
                      y2={`${pos.y}%`}
                      stroke={agent.isActive ? "#3b82f6" : "#9ca3af"}
                      strokeWidth="2"
                      strokeDasharray={agent.isActive ? "none" : "5,5"}
                      className="transition-all duration-500"
                      opacity={agent.isActive ? "0.8" : "0.4"}
                    />
                  );
                })}
                
                {/* Agent-to-Agent collaboration connections */}
                {otherAgents.map((agent, index) => {
                  if (!agent.collaborates_with) return null;
                  
                  return agent.collaborates_with.map(collaboratorName => {
                    const collaboratorIndex = otherAgents.findIndex(a => a.name === collaboratorName);
                    if (collaboratorIndex === -1) return null;
                    
                    const agentPos = getAgentPosition(agent.name, index, otherAgents.length);
                    const collaboratorPos = getAgentPosition(collaboratorName, collaboratorIndex, otherAgents.length);
                    
                    return (
                      <line
                        key={`${agent.name}-${collaboratorName}`}
                        x1={`${agentPos.x}%`}
                        y1={`${agentPos.y}%`}
                        x2={`${collaboratorPos.x}%`}
                        y2={`${collaboratorPos.y}%`}
                        stroke="#f59e0b"
                        strokeWidth="2"
                        strokeDasharray="3,3"
                        className="transition-all duration-500"
                        opacity="0.7"
                      />
                    );
                  });
                })}
              </svg>

              {/* Central Orchestrator */}
              {orchestrator && (
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2">
                  <div className="relative">
                    {/* Pulse rings for active orchestrator */}
                    <div className="absolute inset-0 animate-ping">
                      <div className="w-20 h-20 bg-blue-500 rounded-full opacity-20"></div>
                    </div>
                    <div className="absolute inset-0 animate-pulse" style={{ animationDelay: '1s' }}>
                      <div className="w-20 h-20 bg-blue-400 rounded-full opacity-15"></div>
                    </div>
                    
                    {/* Main orchestrator node */}
                    <div 
                      className="relative w-20 h-20 bg-gradient-to-br from-blue-500 to-blue-700 rounded-full shadow-2xl cursor-pointer transform hover:scale-110 transition-all duration-300 flex items-center justify-center border-4 border-white dark:border-slate-800"
                      onClick={() => setSelectedAgent(orchestrator)}
                    >
                      <Network className="w-8 h-8 text-white" />
                      <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white dark:border-slate-800 animate-pulse"></div>
                    </div>
                    
                    {/* Orchestrator label */}
                    <div className="absolute -bottom-12 left-1/2 transform -translate-x-1/2 text-center">
                      <div className="bg-white dark:bg-slate-800 px-3 py-1 rounded-full shadow-lg border border-gray-200 dark:border-slate-600">
                        <span className="text-sm font-semibold text-gray-900 dark:text-white">Orchestrator</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Agent Nodes in Circle */}
              {otherAgents.map((agent, index) => {
                const pos = getAgentPosition(agent.name, index, otherAgents.length);
                const IconComponent = getAgentIcon(agent.name);
                
                return (
                  <div key={agent.name}>
                    {/* Agent Node */}
                    <div 
                      className="absolute transform -translate-x-1/2 -translate-y-1/2"
                      style={{ left: `${pos.x}%`, top: `${pos.y}%` }}
                    >
                      <div className="relative">
                        {/* Activity pulse for active agents */}
                        {agent.isActive && (
                          <div className="absolute inset-0 animate-ping">
                            <div className="w-14 h-14 bg-green-500 rounded-full opacity-20"></div>
                          </div>
                        )}
                        
                        {/* Main agent node */}
                        <div 
                          className={`relative w-14 h-14 rounded-full shadow-xl cursor-pointer transform hover:scale-110 transition-all duration-300 flex items-center justify-center border-3 border-white dark:border-slate-800 ${
                            agent.isActive 
                              ? 'bg-gradient-to-br from-green-500 to-green-700' 
                              : 'bg-gradient-to-br from-gray-400 to-gray-600'
                          }`}
                          onClick={() => setSelectedAgent(agent)}
                        >
                          <IconComponent className="w-6 h-6 text-white" />
                          <div className={`absolute -top-1 -right-1 w-3 h-3 rounded-full border-2 border-white dark:border-slate-800 ${
                            agent.isActive ? 'bg-green-400 animate-pulse' : 'bg-gray-400'
                          }`}></div>
                        </div>
                        
                        {/* Agent label - Smart positioning */}
                        <div className={`absolute left-1/2 transform -translate-x-1/2 text-center ${
                          pos.y < 50 ? 'top-16' : '-bottom-12'
                        }`}>
                          <div className="bg-white dark:bg-slate-800 px-2 py-1 rounded-full shadow-md border border-gray-200 dark:border-slate-600">
                            <span className="text-xs font-medium text-gray-800 dark:text-gray-200 whitespace-nowrap">
                              {agent.name.replace('Agent', '')}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Status Legend - Moved to top-left to avoid covering agents */}
              <div className="absolute top-4 left-4 bg-white dark:bg-slate-800 rounded-lg p-3 shadow-lg border border-gray-200 dark:border-slate-600">
                <div className="flex items-center space-x-4 text-xs">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                    <span className="text-gray-700 dark:text-gray-300 font-medium">Active</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
                    <span className="text-gray-700 dark:text-gray-300 font-medium">Inactive</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    <span className="text-gray-700 dark:text-gray-300 font-medium">Orchestrator</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                    <span className="text-gray-700 dark:text-gray-300 font-medium">Collaborates</span>
                  </div>
                </div>
              </div>

              {/* Activity Counter */}
              <div className="absolute top-4 right-4 bg-white dark:bg-slate-800 rounded-lg p-3 shadow-lg border border-gray-200 dark:border-slate-600">
                <div className="flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-green-500" />
                  <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                    {agents.filter(a => a.isActive).length}/{agents.length} Active
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Details Panel - Slides in from RIGHT as overlay */}
      {selectedAgent && (
        <div className="absolute top-0 right-0 h-full w-80 bg-white dark:bg-slate-900 border-l-2 border-gray-200 dark:border-slate-700 shadow-2xl transform transition-transform duration-300 ease-in-out z-50 flex flex-col">
          {/* Fixed Header */}
          <div className="flex-shrink-0 p-4 border-b border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-bold text-gray-900 dark:text-white">
                {selectedAgent.name.replace('Agent', '')}
              </h3>
              <div className="flex items-center space-x-3">
                <div className="flex items-center space-x-2">
                  <div className={`w-3 h-3 rounded-full ${
                    selectedAgent.isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-400'
                  }`}></div>
                  <span className="text-xs font-medium text-gray-600 dark:text-gray-400">
                    {selectedAgent.isActive ? 'ACTIVE' : 'INACTIVE'}
                  </span>
                </div>
                <button
                  onClick={() => setSelectedAgent(null)}
                  className="p-1 rounded-lg bg-gray-200 dark:bg-slate-700 hover:bg-gray-300 dark:hover:bg-slate-600 transition-colors"
                >
                  <X className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                </button>
              </div>
            </div>
          </div>

          {/* Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div className="bg-gray-50 dark:bg-slate-800 rounded-lg p-3 border border-gray-200 dark:border-slate-600">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-1">Role</p>
              <p className="text-sm text-gray-800 dark:text-gray-200">{selectedAgent.role}</p>
            </div>

            <div className="bg-gray-50 dark:bg-slate-800 rounded-lg p-3 border border-gray-200 dark:border-slate-600">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-1">Port</p>
              <p className="text-sm font-mono text-gray-800 dark:text-gray-200">{selectedAgent.port}</p>
            </div>

            <div className="bg-gray-50 dark:bg-slate-800 rounded-lg p-3 border border-gray-200 dark:border-slate-600">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Capabilities</p>
              <div className="space-y-1">
                {selectedAgent.capabilities.map((capability, index) => (
                  <div key={index} className="text-xs bg-blue-50 dark:bg-blue-900/30 rounded px-2 py-1 text-blue-800 dark:text-blue-200 border border-blue-200 dark:border-blue-800">
                    {capability}
                  </div>
                ))}
              </div>
            </div>

            <div className="bg-gray-50 dark:bg-slate-800 rounded-lg p-3 border border-gray-200 dark:border-slate-600">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Tools</p>
              <div className="flex flex-wrap gap-1">
                {selectedAgent.tools.map((tool, index) => (
                  <span key={index} className="text-xs bg-green-50 dark:bg-green-900/30 text-green-800 dark:text-green-200 rounded px-2 py-1 border border-green-200 dark:border-green-800">
                    {tool}
                  </span>
                ))}
              </div>
            </div>

            {selectedAgent.mcp_servers.length > 0 && (
              <div className="bg-gray-50 dark:bg-slate-800 rounded-lg p-3 border border-gray-200 dark:border-slate-600">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">MCP Servers</p>
                <div className="flex flex-wrap gap-1">
                  {selectedAgent.mcp_servers.map((server, index) => (
                    <span key={index} className="text-xs bg-purple-50 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200 rounded px-2 py-1 border border-purple-200 dark:border-purple-800">
                      {server}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {selectedAgent.collaborates_with && (
              <div className="bg-gray-50 dark:bg-slate-800 rounded-lg p-3 border border-gray-200 dark:border-slate-600">
                <p className="text-sm font-medium text-gray-600 dark:text-gray-300 mb-2">Collaborates With</p>
                <div className="space-y-1">
                  {selectedAgent.collaborates_with.map((collaborator, index) => (
                    <div key={index} className="text-xs bg-orange-50 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200 rounded px-2 py-1 border border-orange-200 dark:border-orange-800">
                      {collaborator}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Extra padding at bottom to ensure scrolling works */}
            <div className="h-4"></div>
          </div>

          {/* Fixed Footer */}
          <div className="flex-shrink-0 p-4 border-t border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900">
            <div className="text-center">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Click the X button or outside to close
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FlightRouteMap;