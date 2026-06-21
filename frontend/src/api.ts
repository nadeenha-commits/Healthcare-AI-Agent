const API_BASE_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export interface ToolCall {
  name: string;
  args: Record<string, any>;
  result_count?: number;
  result?: Record<string, any>;
}

export interface ChatResponse {
  reply: string;
  tools_called: ToolCall[];
}

interface ChatMessage {
  message: string;
  session_id?: string;
}

interface HistoryItem {
  role: 'user' | 'assistant';
  text: string;
}

export const api = {
  async chat(message: string, sessionId?: string): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message,
        session_id: sessionId || 'default-session',
      } as ChatMessage),
    });

    if (!response.ok) {
      throw new Error(`Chat request failed: ${response.statusText}`);
    }

    return response.json();
  },

  async getHistory(sessionId?: string): Promise<HistoryItem[]> {
    const sid = sessionId || 'default-session';

    const response = await fetch(
      `${API_BASE_URL}/agent/history?session_id=${encodeURIComponent(sid)}`
    );

    if (!response.ok) {
      throw new Error(`History request failed: ${response.statusText}`);
    }

    return response.json();
  },
};