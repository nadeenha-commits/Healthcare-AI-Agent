import React, { useState, useRef, useEffect } from 'react';
import { api } from '../api';
import '../styles.css';

interface Message {
  type: 'user' | 'assistant';
  text: string;
  toolsCalled?: Array<{
    name: string;
    args: Record<string, any>;
    result_count?: number;
    result?: Record<string, any>;
  }>;
}

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState('demo-session-' + Date.now());
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputValue.trim()) {
      return;
    }

    // Add user message
    const userMessage: Message = {
      type: 'user',
      text: inputValue,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      // Call API
      const response = await api.chat(inputValue, sessionId);

      // Add assistant message
      const assistantMessage: Message = {
        type: 'assistant',
        text: response.reply,
        toolsCalled: response.tools_called,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      const errorMessage: Message = {
        type: 'assistant',
        text: 'Sorry, an error occurred while processing your request.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <h1>Healthcare AI Assistant</h1>
        <p className="subtitle">Chat with our AI to manage appointments and patient information</p>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-welcome">
            <h2>Welcome!</h2>
            <p>Try asking me things like:</p>
            <ul>
              <li>"Show available cardiology appointments"</li>
              <li>"Book an appointment for Sarah Cohen with a cardiologist next week"</li>
              <li>"Show patient history for David Levi"</li>
              <li>"Who has the most appointments next week?"</li>
            </ul>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`message message-${msg.type}`}>
            <div className="message-content">
              <div className="message-text">{msg.text}</div>
              {msg.toolsCalled && msg.toolsCalled.length > 0 && (
                <details className="tools-details">
                  <summary>🔧 Tools Called ({msg.toolsCalled.length})</summary>
                  <div className="tools-list">
                    {msg.toolsCalled.map((tool, toolIdx) => (
                      <div key={toolIdx} className="tool-item">
                        <div className="tool-name">
                          <strong>{tool.name}</strong>
                        </div>
                        <div className="tool-args">
                          <small>Args: {JSON.stringify(tool.args, null, 2)}</small>
                        </div>
                        {tool.result_count !== undefined && (
                          <div className="tool-result">
                            <small>Results: {tool.result_count} items</small>
                          </div>
                        )}
                        {tool.result && (
                          <div className="tool-result">
                            <small>Result: {JSON.stringify(tool.result, null, 2)}</small>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message message-assistant">
            <div className="message-content">
              <div className="loading">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Type your message here..."
          disabled={loading}
          className="chat-input"
          autoFocus
        />
        <button type="submit" disabled={loading} className="chat-send-btn">
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
};

