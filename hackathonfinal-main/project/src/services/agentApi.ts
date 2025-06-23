/**
 * Agent API Service
 * Handles communication with the multi-agent system orchestrator
 */

interface AgentResponse {
  success: boolean;
  response?: string;
  error?: string;
  agent?: string;
  tools_used?: string[];
}

class AgentApiService {
  private baseUrl: string;
  private sessionId: string;

  constructor() {
    // Use the Vite proxy to avoid CORS issues
    this.baseUrl = '/api';
    // Generate a unique session ID for this browser session
    this.sessionId = this.generateSessionId();
  }

  private generateSessionId(): string {
    return `web-ui-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Send a message to the orchestrator
   */
  async sendMessage(message: string): Promise<AgentResponse> {
    try {
      const taskId = `task-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      
      const payload = {
        jsonrpc: "2.0",
        id: taskId,
        method: "tasks/send",
        params: {
          id: taskId,
          sessionId: this.sessionId,
          message: {
            role: "user",
            parts: [
              {
                type: "text",
                text: message
              }
            ]
          }
        }
      };

      const response = await fetch(this.baseUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        return {
          success: false,
          error: data.error.message || 'Unknown error occurred'
        };
      }

      // Extract response from A2A protocol format
      if (data.result && data.result.history && data.result.history.length > 0) {
        // Get the last message in history (should be the agent's response)
        const lastMessage = data.result.history[data.result.history.length - 1];
        
        if (lastMessage.role === 'agent' && lastMessage.parts && lastMessage.parts.length > 0) {
          const textPart = lastMessage.parts.find((part: any) => part.type === 'text');
          if (textPart) {
            return {
              success: true,
              response: textPart.text,
              agent: lastMessage.agent || 'orchestrator',
              tools_used: lastMessage.tools_used
            };
          }
        }
      }

      return {
        success: false,
        error: 'Invalid response format'
      };
    } catch (error) {
      console.error('Agent API Error:', error);
      
      // Check if it's a connection error
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        return {
          success: false,
          error: 'Cannot connect to the agent system. Please ensure the orchestrator is running on port 10000.'
        };
      }
      
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error occurred'
      };
    }
  }

  /**
   * Check if the orchestrator is available
   */
  async checkHealth(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseUrl}/.well-known/agent.json`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        }
      });
      
      return response.ok;
    } catch (error) {
      console.error('Health check failed:', error);
      return false;
    }
  }

  /**
   * Get current session ID
   */
  getSessionId(): string {
    return this.sessionId;
  }

  /**
   * Reset session (generate new session ID)
   */
  resetSession(): void {
    this.sessionId = this.generateSessionId();
  }
}

// Export singleton instance
export const agentApi = new AgentApiService();
export type { AgentResponse };