/**
 * API Client for Healthcare AI Agent Backend
 * Handles all HTTP requests to the Flask backend
 */

const API_BASE_URL = (process.env.REACT_APP_API_URL || 'http://localhost:8000').replace(/\/$/, '');

interface ChatResponse {
  reply: string;
  tools_called: Array<{
    name: string;
    args: Record<string, any>;
    result_count?: number;
    result?: Record<string, any>;
  }>;
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
  // Chat endpoint
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

  // Get conversation history
  async getHistory(sessionId?: string): Promise<HistoryItem[]> {
    const sid = sessionId || 'default-session';
    const response = await fetch(`${API_BASE_URL}/agent/history?session_id=${encodeURIComponent(sid)}`);

    if (!response.ok) {
      throw new Error(`History request failed: ${response.statusText}`);
    }

    return response.json();
  },

  // Auth endpoints
  async register(fullName: string, email: string, password: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ full_name: fullName, email, password }),
    });
    return response.json();
  },

  async login(email: string, password: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    return response.json();
  },

  // Patient endpoints
  async getPatients(query?: string): Promise<any[]> {
    const url = query ? `${API_BASE_URL}/patients?q=${encodeURIComponent(query)}` : `${API_BASE_URL}/patients`;
    const response = await fetch(url);
    return response.json();
  },

  // Doctor endpoints
  async getDoctors(specialty?: string): Promise<any[]> {
    const url = specialty
      ? `${API_BASE_URL}/doctors?specialty=${encodeURIComponent(specialty)}`
      : `${API_BASE_URL}/doctors`;
    const response = await fetch(url);
    return response.json();
  },

  // Appointment endpoints
  async getAppointments(): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/appointments`);
    return response.json();
  },

  // Analytics endpoints
  async getBusiestDoctor(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/analytics/busiest-doctor`);
    return response.json();
  },

  async getMonthlyAppointments(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/analytics/monthly-appointments`);
    return response.json();
  },

  async getDepartmentLoad(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/analytics/department-load`);
    return response.json();
  },
};

