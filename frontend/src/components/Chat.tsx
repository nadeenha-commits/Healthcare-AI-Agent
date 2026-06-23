import React, { useEffect, useRef, useState } from 'react';
import { api, ActivityStep, AuthUser, ToolCall } from '../api';
import { AuthPanel } from './AuthPanel';

interface Message {
  type: 'user' | 'assistant';
  text: string;
  toolsCalled?: ToolCall[];
  timestamp: Date;
}

interface ActivityEntry {
  id: string;
  userText: string;
  startedAt: Date;
  status: 'running' | 'completed' | 'failed';
  steps: ActivityStep[];
  toolsCalled: ToolCall[];
  replyPreview?: string;
  zepEnabled?: boolean;
}

const quickPrompts = [
  'Book Sarah Cohen with a cardiologist next week',
  'Who is the busiest doctor?',
  'What can you help me with?',
  'Show departments',
];

const formatTime = (date: Date): string => {
  return date.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });
};

const formatToolName = (name: string): string => {
  return name.replace(/_/g, ' ');
};

const getToolIcon = (toolName: string): string => {
  if (toolName.includes('search')) return '⌕';
  if (toolName.includes('slot') || toolName.includes('schedule')) return '◷';
  if (toolName.includes('book') || toolName.includes('appointment')) return '▣';
  if (toolName.includes('doctor')) return '⚕';
  if (toolName.includes('patient')) return '⊕';
  if (toolName.includes('busiest') || toolName.includes('load')) return '◈';
  if (toolName.includes('treatment')) return '✚';

  return '◆';
};

const renderMultilineText = (text: string) => {
  return text.split('\n').map((line, index, lines) => (
    <React.Fragment key={`line-${index}`}>
      {line}
      {index < lines.length - 1 && <br />}
    </React.Fragment>
  ));
};

const getActivityStatusClass = (status: ActivityEntry['status']): string => {
  if (status === 'completed') return 'text-bg-success';
  if (status === 'failed') return 'text-bg-danger';
  return 'text-bg-primary';
};

const getStepDotClass = (status: ActivityStep['status']): string => {
  if (status === 'done') return 'bg-success';
  if (status === 'failed') return 'bg-danger';
  return 'bg-primary';
};

const getStepBadgeClass = (status: ActivityStep['status']): string => {
  if (status === 'done') return 'text-bg-success';
  if (status === 'failed') return 'text-bg-danger';
  return 'text-bg-primary';
};

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [activityLogs, setActivityLogs] = useState<ActivityEntry[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(`frontend-session-${Date.now()}`);
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({
      behavior: 'smooth',
      block: 'end',
    });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const updateActivityEntry = (
    requestId: string,
    updater: (entry: ActivityEntry) => ActivityEntry
  ) => {
    setActivityLogs((previousLogs) =>
      previousLogs.map((entry) => (entry.id === requestId ? updater(entry) : entry))
    );
  };

  const sendMessage = async (messageText?: string) => {
    const textToSend = (messageText ?? inputValue).trim();

    if (!textToSend || loading) {
      return;
    }

    const requestId = `req-${Date.now()}`;
    const startedAt = new Date();

    const userMessage: Message = {
      type: 'user',
      text: textToSend,
      timestamp: startedAt,
    };

    const runningActivity: ActivityEntry = {
      id: requestId,
      userText: textToSend,
      startedAt,
      status: 'running',
      steps: [],
      toolsCalled: [],
    };

    setMessages((previousMessages) => [...previousMessages, userMessage]);
    setActivityLogs((previousLogs) => [runningActivity, ...previousLogs]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await api.chatStream(textToSend, sessionId, {
        onActivity: (step) => {
          updateActivityEntry(requestId, (entry) => ({
            ...entry,
            steps: [...entry.steps, step],
          }));
        },
        onFinal: (finalResponse) => {
          updateActivityEntry(requestId, (entry) => ({
            ...entry,
            status: 'completed',
            steps: finalResponse.activity_steps || entry.steps,
            toolsCalled: finalResponse.tools_called || [],
            replyPreview: finalResponse.reply,
            zepEnabled: finalResponse.memory?.zep_enabled,
          }));
        },
        onError: (message) => {
          updateActivityEntry(requestId, (entry) => ({
            ...entry,
            status: 'failed',
            steps: [
              ...entry.steps,
              {
                label: 'SSE connection failed',
                status: 'failed',
                detail: message,
              },
            ],
          }));
        },
      });

      const assistantMessage: Message = {
        type: 'assistant',
        text: response.reply,
        toolsCalled: response.tools_called || [],
        timestamp: new Date(),
      };

      setMessages((previousMessages) => [...previousMessages, assistantMessage]);

      updateActivityEntry(requestId, (entry) => ({
        ...entry,
        status: 'completed',
        steps: response.activity_steps || entry.steps,
        toolsCalled: response.tools_called || [],
        replyPreview: response.reply,
        zepEnabled: response.memory?.zep_enabled,
      }));
    } catch (error) {
      console.error('Agent SSE chat error:', error);

      const errorMessage: Message = {
        type: 'assistant',
        text: 'Sorry, I could not connect to the Healthcare AI Agent backend. Please make sure the Flask server is running on http://localhost:8000.',
        toolsCalled: [],
        timestamp: new Date(),
      };

      setMessages((previousMessages) => [...previousMessages, errorMessage]);

      updateActivityEntry(requestId, (entry) => ({
        ...entry,
        status: 'failed',
        steps:
          entry.steps.length > 0
            ? entry.steps
            : [
                {
                  label: 'Connection failed',
                  status: 'failed',
                  detail: 'Could not reach the backend SSE stream.',
                },
              ],
      }));
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    void sendMessage();
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  };

  return (
    <main className="bg-white vh-100 overflow-hidden">
      <section className="container-fluid px-0 h-100">
        <div className="row g-0 h-100 overflow-hidden">
          <aside className="col-12 col-lg-3 border-end bg-light-subtle d-flex flex-column h-100 overflow-hidden">
            <header className="border-bottom bg-white px-3 py-3 flex-shrink-0">
              <div className="d-flex align-items-center justify-content-between gap-2">
                <div>
                  <h2 className="h6 fw-bold text-dark mb-1">Agent Activity</h2>
                  <p className="small text-secondary mb-0">Live backend SSE workflow trace</p>
                </div>

                <span className="badge rounded-pill text-bg-primary">SSE</span>
              </div>
            </header>

            <div className="border-bottom bg-white p-3 flex-shrink-0">
              <AuthPanel
                onAuthChange={(user, token) => {
                  setCurrentUser(user);
                  setAuthToken(token);
                }}
              />
            </div>

            <div className="flex-grow-1 overflow-auto p-3">
              {activityLogs.length === 0 && (
                <div className="border rounded-4 bg-white p-3 shadow-sm text-center">
                  <div className="fs-3 mb-2">◈</div>
                  <h3 className="h6 fw-bold mb-2">No activity yet</h3>
                  <p className="small text-secondary mb-0">
                    Send a message to see the real backend Agent workflow.
                  </p>
                </div>
              )}

              <div className="d-flex flex-column gap-3">
                {activityLogs.map((entry) => (
                  <article key={entry.id} className="border rounded-4 bg-white shadow-sm overflow-hidden">
                    <div className="border-bottom p-3">
                      <div className="d-flex align-items-start justify-content-between gap-2 mb-2">
                        <div className="text-truncate">
                          <div className="small text-secondary mb-1">Request</div>
                          <div className="fw-semibold small text-dark text-truncate" title={entry.userText}>
                            {entry.userText}
                          </div>
                        </div>

                        <span className={`badge rounded-pill ${getActivityStatusClass(entry.status)}`}>
                          {entry.status}
                        </span>
                      </div>

                      <div className="d-flex align-items-center justify-content-between gap-2">
                        <span className="small text-secondary">{formatTime(entry.startedAt)}</span>
                        <span className="small text-secondary">
                          {entry.zepEnabled ? 'Zep on' : 'Zep off'}
                        </span>
                      </div>
                    </div>

                    <div className="p-3">
                      {entry.steps.length === 0 && (
                        <div className="d-flex align-items-center gap-2 text-secondary small">
                          <span className="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                          Opening SSE stream...
                        </div>
                      )}

                      <div className="d-flex flex-column gap-3">
                        {entry.steps.map((step, stepIndex) => (
                          <div key={`${entry.id}-step-${stepIndex}`} className="d-flex gap-2">
                            <div className="pt-1">
                              <span
                                className={`d-inline-block rounded-circle ${getStepDotClass(step.status)}`}
                                style={{ width: '10px', height: '10px' }}
                              ></span>
                            </div>

                            <div className="flex-grow-1">
                              <div className="d-flex align-items-center justify-content-between gap-2 mb-1">
                                <div className="fw-semibold small text-dark">{step.label}</div>
                                <span className={`badge rounded-pill ${getStepBadgeClass(step.status)}`}>
                                  {step.status}
                                </span>
                              </div>

                              {step.detail && (
                                <p className="small text-secondary mb-0 lh-sm">{step.detail}</p>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>

                      {entry.toolsCalled.length > 0 && (
                        <div className="border-top mt-3 pt-3">
                          <div className="text-uppercase text-secondary fw-bold small mb-2">Tools</div>
                          <div className="d-flex flex-wrap gap-2">
                            {entry.toolsCalled.map((tool, index) => (
                              <span
                                key={`${entry.id}-${tool.name}-${index}`}
                                className="badge rounded-pill text-primary border border-primary-subtle bg-primary-subtle px-2 py-2 fw-semibold"
                              >
                                <span className="me-1">{getToolIcon(tool.name)}</span>
                                {formatToolName(tool.name)}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </aside>

          <section className="col-12 col-lg-9 d-flex flex-column bg-white h-100 overflow-hidden">
            <header className="border-bottom bg-white px-3 px-md-4 py-3 flex-shrink-0">
              <div className="d-flex align-items-center justify-content-between gap-3">
                <div className="d-flex align-items-center gap-3">
                  <div
                    className="d-flex align-items-center justify-content-center rounded-4 bg-primary text-white fw-bold shadow-sm"
                    style={{ width: '42px', height: '42px' }}
                  >
                    ✚
                  </div>

                  <div>
                    <h1 className="h5 fw-bold mb-1 text-dark">Healthcare AI Agent</h1>
                    <p className="small text-secondary mb-0">
                      Book appointments, check doctors, and manage patient requests
                    </p>
                  </div>
                </div>

                <div className="d-none d-md-flex align-items-center gap-2">
                  {currentUser && (
                    <span className="badge rounded-pill text-bg-light border text-secondary px-3 py-2">
                      Signed in: {currentUser.full_name}
                    </span>
                  )}
                  {authToken && (
                    <span className="badge rounded-pill text-bg-light border text-secondary px-3 py-2">
                      JWT Active
                    </span>
                  )}
                  <span className="badge rounded-pill text-bg-success px-3 py-2">Gemini Connected</span>
                  <span className="badge rounded-pill text-bg-primary px-3 py-2">SSE Enabled</span>
                </div>
              </div>
            </header>

            <div className="flex-grow-1 overflow-auto px-3 px-md-4 py-4">
              {messages.length === 0 && (
                <div className="h-100 d-flex align-items-center justify-content-center text-center">
                  <div className="w-100" style={{ maxWidth: '760px' }}>
                    <div
                      className="mx-auto mb-3 d-flex align-items-center justify-content-center rounded-4 bg-primary-subtle text-primary fs-3"
                      style={{ width: '58px', height: '58px' }}
                    >
                      ⚕
                    </div>

                    <h2 className="fw-bold text-dark mb-2">
                      How can I help with clinic workflows today?
                    </h2>

                    <p className="text-secondary mb-4">
                      Ask me to book appointments, search patients, check doctor availability,
                      or generate clinic analytics.
                    </p>

                    <div className="row g-2">
                      {quickPrompts.map((prompt) => (
                        <div key={prompt} className="col-12 col-md-6">
                          <button
                            type="button"
                            className="btn btn-light border shadow-sm rounded-4 w-100 text-start p-3"
                            onClick={() => sendMessage(prompt)}
                            disabled={loading}
                          >
                            {prompt}
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              <div className="d-flex flex-column gap-4">
                {messages.map((message, index) => (
                  <article
                    key={`${message.type}-${index}`}
                    className={`d-flex gap-2 ${
                      message.type === 'user' ? 'justify-content-end' : 'justify-content-start'
                    }`}
                  >
                    {message.type === 'assistant' && (
                      <div
                        className="d-none d-sm-flex align-items-center justify-content-center rounded-circle bg-primary-subtle text-primary fw-bold flex-shrink-0"
                        style={{ width: '36px', height: '36px' }}
                      >
                        ✚
                      </div>
                    )}

                    <div
                      className={`d-flex flex-column ${
                        message.type === 'user' ? 'align-items-end' : 'align-items-start'
                      }`}
                      style={{ maxWidth: '78%' }}
                    >
                      <div
                        className={`rounded-4 px-3 py-3 border ${
                          message.type === 'user'
                            ? 'bg-light text-dark'
                            : 'bg-white text-dark shadow-sm'
                        }`}
                      >
                        <div className="mb-0 small lh-lg text-break" style={{ whiteSpace: 'pre-wrap' }}>
                          {renderMultilineText(message.text)}
                        </div>
                      </div>

                      {message.type === 'assistant' &&
                        message.toolsCalled &&
                        message.toolsCalled.length > 0 && (
                          <div className="mt-2">
                            <div className="text-uppercase text-secondary fw-bold small mb-2">
                              Tools Used
                            </div>

                            <div className="d-flex flex-wrap gap-2">
                              {message.toolsCalled.map((tool, toolIndex) => (
                                <span
                                  key={`${tool.name}-${toolIndex}`}
                                  className="badge rounded-pill text-primary border border-primary-subtle bg-primary-subtle px-3 py-2 fw-semibold"
                                  title={JSON.stringify(tool.args || {})}
                                >
                                  <span className="me-1">{getToolIcon(tool.name)}</span>
                                  {formatToolName(tool.name)}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                      <time className="text-secondary small mt-1">
                        {formatTime(message.timestamp)}
                      </time>
                    </div>

                    {message.type === 'user' && (
                      <div
                        className="d-none d-sm-flex align-items-center justify-content-center rounded-circle bg-light border text-secondary fw-bold flex-shrink-0 small"
                        style={{ width: '36px', height: '36px' }}
                      >
                        You
                      </div>
                    )}
                  </article>
                ))}

                {loading && (
                  <article className="d-flex gap-2 justify-content-start">
                    <div
                      className="d-none d-sm-flex align-items-center justify-content-center rounded-circle bg-primary-subtle text-primary fw-bold flex-shrink-0"
                      style={{ width: '36px', height: '36px' }}
                    >
                      ✚
                    </div>

                    <div className="rounded-4 px-3 py-3 border bg-white shadow-sm">
                      <span className="spinner-grow spinner-grow-sm text-secondary me-1" role="status" aria-hidden="true"></span>
                      <span className="spinner-grow spinner-grow-sm text-secondary me-1" role="status" aria-hidden="true"></span>
                      <span className="spinner-grow spinner-grow-sm text-secondary" role="status" aria-hidden="true"></span>
                    </div>
                  </article>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>

            <footer className="border-top bg-white px-3 px-md-4 py-3 flex-shrink-0">
              <div className="d-flex gap-2 overflow-auto pb-2">
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="btn btn-outline-secondary btn-sm rounded-pill flex-shrink-0"
                    onClick={() => sendMessage(prompt)}
                    disabled={loading}
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              <form className="d-flex align-items-end gap-2 border rounded-4 shadow-sm p-2" onSubmit={handleSubmit}>
                <textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(event) => setInputValue(event.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder="Ask me to book, cancel, or check an appointment..."
                  disabled={loading}
                  rows={1}
                  className="form-control border-0 shadow-none"
                  autoFocus
                />

                <button
                  type="submit"
                  disabled={loading || !inputValue.trim()}
                  className="btn btn-primary rounded-4 px-3 py-2"
                >
                  {loading ? '...' : '➤'}
                </button>
              </form>

              <p className="text-center text-secondary small mb-0 mt-2">
                AI assistant responses should be reviewed for important medical or scheduling decisions.
              </p>
            </footer>
          </section>
        </div>
      </section>
    </main>
  );
};