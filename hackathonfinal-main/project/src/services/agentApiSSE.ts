/**
 * Agent API Service with SSE Support
 * Handles communication with the multi-agent system orchestrator using Server-Sent Events
 */

interface AgentResponse {
  success: boolean;
  response?: string;
  error?: string;
  agent?: string;
  tools_used?: string[];
}

interface StreamEvent {
  type: 'thinking' | 'status' | 'complete' | 'error' | 'done';
  agent?: string;
  content?: string;
  result?: any;
}

type StreamCallback = (event: StreamEvent) => void;

class AgentApiSSEService {
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
   * Send a message with streaming support
   */
  async sendMessageStreaming(
    message: string, 
    onStream: StreamCallback
  ): Promise<AgentResponse> {
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

      // Use EventSource for SSE
      const response = await fetch(`${this.baseUrl}/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Process the stream
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let finalResponse: AgentResponse = {
        success: false,
        error: 'No response received'
      };

      if (!reader) {
        throw new Error('No response body');
      }

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        
        // Process complete SSE messages
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              
              // Call the stream callback
              onStream(event);
              
              // Handle different event types
              if (event.type === 'complete') {
                // Extract the final response
                if (event.result && event.result.history && event.result.history.length > 0) {
                  const lastMessage = event.result.history[event.result.history.length - 1];
                  if (lastMessage.role === 'agent' && lastMessage.parts && lastMessage.parts.length > 0) {
                    const textPart = lastMessage.parts.find((part: any) => part.type === 'text');
                    if (textPart) {
                      finalResponse = {
                        success: true,
                        response: textPart.text,
                        agent: lastMessage.agent || 'orchestrator',
                        tools_used: lastMessage.tools_used
                      };
                    }
                  }
                } else if (event.content) {
                  finalResponse = {
                    success: true,
                    response: event.content,
                    agent: event.agent || 'orchestrator'
                  };
                }
              } else if (event.type === 'error') {
                finalResponse = {
                  success: false,
                  error: event.content || 'Unknown error occurred'
                };
              }
            } catch (e) {
              console.error('Error parsing SSE event:', e);
            }
          }
        }
      }

      return finalResponse;
    } catch (error) {
      console.error('Agent API SSE Error:', error);
      
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
   * Send a message to the orchestrator (non-streaming fallback)
   */
  async sendMessage(message: string): Promise<AgentResponse> {
    // Use streaming with a simple collector
    const events: StreamEvent[] = [];
    return this.sendMessageStreaming(message, (event) => {
      events.push(event);
    });
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
export const agentApiSSE = new AgentApiSSEService();
export type { AgentResponse, StreamEvent, StreamCallback };