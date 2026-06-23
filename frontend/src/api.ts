const API_BASE_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export interface ToolCall {
  name: string;
  args: Record<string, any>;
  result_count?: number;
  result?: Record<string, any>;
}

export interface ActivityStep {
  label: string;
  status: 'done' | 'running' | 'active' | 'failed';
  detail?: string;
}

export interface MemoryInfo {
  zep_enabled: boolean;
}

export interface ChatResponse {
  reply: string;
  tools_called: ToolCall[];
  activity_steps?: ActivityStep[];
  memory?: MemoryInfo;
}

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  role: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface RegisterResponse {
  message: string;
  user: AuthUser;
}

export interface ProfileResponse {
  message: string;
  user: AuthUser;
}

interface ChatMessage {
  message: string;
  session_id?: string;
}

interface HistoryItem {
  role: 'user' | 'assistant';
  text: string;
}

interface StreamHandlers {
  onActivity?: (step: ActivityStep) => void;
  onFinal?: (response: ChatResponse) => void;
  onError?: (message: string) => void;
}

const getAuthHeaders = (token?: string): Record<string, string> => {
  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
};

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

  chatStream(
    message: string,
    sessionId?: string,
    handlers?: StreamHandlers
  ): Promise<ChatResponse> {
    return new Promise((resolve, reject) => {
      const params = new URLSearchParams({
        message,
        session_id: sessionId || 'default-session',
      });

      const eventSource = new EventSource(
        `${API_BASE_URL}/agent/chat/stream?${params.toString()}`
      );

      let finalResponse: ChatResponse | null = null;
      let completed = false;

      const closeStream = () => {
        completed = true;
        eventSource.close();
      };

      eventSource.addEventListener('activity', (event) => {
        try {
          const step = JSON.parse((event as MessageEvent).data) as ActivityStep;
          handlers?.onActivity?.(step);
        } catch (error) {
          console.error('Failed to parse SSE activity event:', error);
        }
      });

      eventSource.addEventListener('final', (event) => {
        try {
          finalResponse = JSON.parse((event as MessageEvent).data) as ChatResponse;
          handlers?.onFinal?.(finalResponse);
        } catch (error) {
          closeStream();
          reject(new Error('Failed to parse SSE final response.'));
        }
      });

      eventSource.addEventListener('done', () => {
        closeStream();

        if (finalResponse) {
          resolve(finalResponse);
        } else {
          reject(new Error('SSE stream ended without a final Agent response.'));
        }
      });

      eventSource.addEventListener('error', (event) => {
        if (completed) {
          return;
        }

        let messageText = 'SSE connection failed.';
        const messageEvent = event as MessageEvent;

        if (messageEvent.data) {
          try {
            const payload = JSON.parse(messageEvent.data) as { message?: string };
            messageText = payload.message || messageText;
          } catch {
            messageText = String(messageEvent.data);
          }
        }

        handlers?.onError?.(messageText);
        closeStream();
        reject(new Error(messageText));
      });
    });
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

  async register(fullName: string, email: string, password: string): Promise<RegisterResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        full_name: fullName,
        email,
        password,
      }),
    });

    if (!response.ok) {
      throw new Error(`Register failed: ${response.statusText}`);
    }

    return response.json();
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email,
        password,
      }),
    });

    if (!response.ok) {
      throw new Error(`Login failed: ${response.statusText}`);
    }

    return response.json();
  },

  async getCurrentUser(token: string): Promise<AuthUser> {
    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      method: 'GET',
      headers: {
        ...getAuthHeaders(token),
      },
    });

    if (!response.ok) {
      throw new Error(`Current user request failed: ${response.statusText}`);
    }

    return response.json();
  },

  async updateProfile(token: string, fullName: string): Promise<ProfileResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/profile`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(token),
      },
      body: JSON.stringify({
        full_name: fullName,
      }),
    });

    if (!response.ok) {
      throw new Error(`Profile update failed: ${response.statusText}`);
    }

    return response.json();
  },
};