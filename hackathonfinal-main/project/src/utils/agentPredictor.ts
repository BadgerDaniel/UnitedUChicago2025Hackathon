/**
 * Agent Predictor Utility
 * Analyzes user queries to predict which agents will be involved
 */

interface AgentPrediction {
  agent: string;
  reason: string;
  icon?: string;
}

export class AgentPredictor {
  private agentPatterns = [
    {
      agent: 'FlightIntelligenceAgent',
      icon: '✈️',
      patterns: [
        /flight|fly|route|airline|airport|departure|arrival|booking|ticket|cabin|seat/i,
        /ORD|LAX|JFK|DEN|ATL|DFW|SFO|LHR|CDG|NRT|HND|Tokyo|O'Hare/i,
        /United|UA|UAL|American|Delta|Southwest/i,
        /premium.*cabin|business.*class|first.*class|economy/i,
        /demand.*forecast|load.*factor|capacity/i,
      ],
      reason: 'Searching flight databases'
    },
    {
      agent: 'AviationWeatherAgent',
      icon: '🌤️',
      patterns: [
        /weather|storm|rain|snow|wind|visibility|forecast|METAR|TAF/i,
        /conditions.*airport|airport.*conditions/i,
        /weather.*pattern|climate|seasonal/i,
        /typhoon|hurricane|turbulence/i,
      ],
      reason: 'Checking aviation weather'
    },
    {
      agent: 'LiveEventsAgent',
      icon: '🎉',
      patterns: [
        /event|concert|conference|festival|game|convention|happening/i,
        /tech.*conference|business.*conference|summit|expo/i,
        /Olympics|World.*Cup|Super.*Bowl/i,
        /what.*happening|things.*do|activities/i,
      ],
      reason: 'Finding local events'
    },
    {
      agent: 'EconomicIndicatorsAgent',
      icon: '📊',
      patterns: [
        /economic|GDP|inflation|exchange|currency|market|indicator/i,
        /economy|financial.*data|recession|growth/i,
        /business.*travel|corporate.*demand/i,
        /Japan.*economy|US.*economy|trade/i,
      ],
      reason: 'Analyzing economic data'
    },
    {
      agent: 'GoogleNewsAgent',
      icon: '📰',
      patterns: [
        /news|headline|article|announcement|press.*release/i,
        /United Airlines|UAL|aviation.*news/i,
        /latest.*about|what.*saying|media.*coverage/i,
        /business.*travel.*news|airline.*industry/i,
      ],
      reason: 'Searching news articles'
    },
    {
      agent: 'WebScrapingAgent',
      icon: '🌐',
      patterns: [
        /website|webpage|scrape|extract|online/i,
        /check.*site|visit.*page|web.*data/i,
        /online.*booking|travel.*site/i,
      ],
      reason: 'Fetching web content'
    }
  ];

  predictAgents(query: string): AgentPrediction[] {
    const predictions: AgentPrediction[] = [];
    const queryLower = query.toLowerCase();
    
    // Always starts with orchestrator
    predictions.push({
      agent: 'OrchestratorAgent',
      icon: '🧠',
      reason: 'Analyzing your request'
    });

    // Track which agents are matched to avoid duplicates
    const matchedAgents = new Set<string>();

    // Check which agents might be involved
    for (const agentInfo of this.agentPatterns) {
      const matches = agentInfo.patterns.some(pattern => pattern.test(query));
      if (matches && !matchedAgents.has(agentInfo.agent)) {
        // Customize reason based on query content
        let customReason = agentInfo.reason;
        
        if (agentInfo.agent === 'FlightIntelligenceAgent') {
          if (queryLower.includes('premium cabin') || queryLower.includes('business')) {
            customReason = 'Analyzing premium cabin demand';
          } else if (queryLower.includes('route')) {
            customReason = 'Analyzing route performance';
          }
        } else if (agentInfo.agent === 'EconomicIndicatorsAgent') {
          if (queryLower.includes('business travel')) {
            customReason = 'Analyzing business travel indicators';
          }
        } else if (agentInfo.agent === 'LiveEventsAgent') {
          if (queryLower.includes('tech conference')) {
            customReason = 'Finding tech conferences';
          }
        } else if (agentInfo.agent === 'AviationWeatherAgent') {
          if (queryLower.includes('pattern')) {
            customReason = 'Analyzing weather patterns';
          }
        } else if (agentInfo.agent === 'GoogleNewsAgent') {
          if (queryLower.includes('business travel news')) {
            customReason = 'Searching business travel news';
          }
        }
        
        predictions.push({
          agent: agentInfo.agent,
          icon: agentInfo.icon,
          reason: customReason
        });
        matchedAgents.add(agentInfo.agent);
      }
    }

    // For complex analysis queries, ensure we get all relevant agents
    if (queryLower.includes('analyze') && queryLower.includes('demand')) {
      // Make sure we have economic and news agents for comprehensive analysis
      if (!matchedAgents.has('EconomicIndicatorsAgent')) {
        predictions.push({
          agent: 'EconomicIndicatorsAgent',
          icon: '📊',
          reason: 'Analyzing economic factors'
        });
      }
      if (!matchedAgents.has('GoogleNewsAgent')) {
        predictions.push({
          agent: 'GoogleNewsAgent',
          icon: '📰',
          reason: 'Gathering market insights'
        });
      }
    }

    return predictions;
  }

  getProgressMessages(predictions: AgentPrediction[]): string[] {
    const messages: string[] = [];
    
    predictions.forEach((pred, index) => {
      if (index === 0) {
        messages.push(`${pred.icon} ${pred.agent}: ${pred.reason}...`);
      } else {
        messages.push(`${pred.icon} Routing to ${pred.agent}: ${pred.reason}...`);
      }
    });

    messages.push('🔄 Processing responses...');
    messages.push('✨ Preparing final answer...');

    return messages;
  }
}

export const agentPredictor = new AgentPredictor();