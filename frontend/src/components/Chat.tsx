import React, { useEffect, useRef, useState } from 'react';
import { api, ToolCall } from '../api';

interface Message {
  type: 'user' | 'assistant';
  text: string;
  toolsCalled?: ToolCall[];
  timestamp: Date;
}

interface ActivityStep {
  label: string;
  status: 'done' | 'active' | 'failed';
  detail?: string;
}

interface ActivityEntry {
  id: string;
  userText: string;
  startedAt: Date;
  status: 'running' | 'completed' | 'failed';
  steps: ActivityStep[];
  toolsCalled: ToolCall[];
  replyPreview?: string;
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

const inferIntent = (messageText: string, tools: ToolCall[]): string => {
  const text = messageText.toLowerCase();

  if (tools.some((tool) => tool.name === 'book_appointment')) {
    return 'Detected an appointment booking request.';
  }

  if (tools.some((tool) => tool.name === 'busiest_doctor')) {
    return 'Detected an analytics request about doctor workload.';
  }

  if (tools.some((tool) => tool.name === 'department_load')) {
    return 'Detected an analytics request about department load.';
  }

  if (tools.some((tool) => tool.name === 'search_patient')) {
    return 'Detected a patient lookup request.';
  }

  if (text.includes('help')) {
    return 'Handled as a general capability question.';
  }

  return 'Analyzed the user request and selected the response path.';
};

export const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [activityLogs, setActivityLogs] = useState<ActivityEntry[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(`frontend-session-${Date.now()}`);

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
      toolsCalled: [],
      steps: [
        {
          label: 'Received request',
          status: 'done',
          detail: 'Captured the user message for processing.',
        },
        {
          label: 'Analyzing request',
          status: 'active',
          detail: 'Understanding the request and deciding whether tools are needed.',
        },
      ],
    };

    setMessages((previousMessages) => [...previousMessages, userMessage]);
    setActivityLogs((previousLogs) => [runningActivity, ...previousLogs]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await api.chat(textToSend, sessionId);
      const toolsCalled = response.tools_called || [];

      const assistantMessage: Message = {
        type: 'assistant',
        text: response.reply,
        toolsCalled,
        timestamp: new Date(),
      };

      setMessages((previousMessages) => [...previousMessages, assistantMessage]);

      const completedSteps: ActivityStep[] = [
        {
          label: 'Received request',
          status: 'done',
          detail: 'Captured the user message for processing.',
        },
        {
          label: 'Analyzed intent',
          status: 'done',
          detail: inferIntent(textToSend, toolsCalled),
        },
        {
          label: toolsCalled.length > 0 ? 'Selected tool workflow' : 'Direct response path',
          status: 'done',
          detail:
            toolsCalled.length > 0
              ? 'This request required structured tool usage.'
              : 'This request was answered directly without tool calls.',
        },
        ...toolsCalled.map((tool): ActivityStep => ({
          label: `Called ${formatToolName(tool.name)}`,
          status: 'done',
          detail:
            typeof tool.result_count === 'number'
              ? `Returned ${tool.result_count} result${tool.result_count === 1 ? '' : 's'}.`
              : 'Tool executed successfully.',
        })),
        {
          label: 'Generated final response',
          status: 'done',
          detail: 'Prepared the final answer for the chat UI.',
        },
      ];

      setActivityLogs((previousLogs) =>
        previousLogs.map((entry) =>
          entry.id === requestId
            ? {
                ...entry,
                status: 'completed',
                toolsCalled,
                replyPreview: response.reply,
                steps: completedSteps,
              }
            : entry
        )
      );
    } catch (error) {
      console.error('Agent chat error:', error);

      const errorMessage: Message = {
        type: 'assistant',
        text: 'Sorry, I could not connect to the Healthcare AI Agent backend. Please make sure the Flask server is running on http://localhost:8000.',
        toolsCalled: [],
        timestamp: new Date(),
      };

      setMessages((previousMessages) => [...previousMessages, errorMessage]);

      setActivityLogs((previousLogs) =>
        previousLogs.map((entry) =>
          entry.id === requestId
            ? {
                ...entry,
                status: 'failed',
                steps: [
                  {
                    label: 'Received request',
                    status: 'done',
                    detail: 'Captured the user message for processing.',
                  },
                  {
                    label: 'Connection failed',
                    status: 'failed',
                    detail: 'Could not reach the backend service.',
                  },
                ],
              }
            : entry
        )
      );
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
          {/* Left Panel: Agent Activity */}
          <aside className="col-12 col-lg-3 border-end bg-light-subtle d-flex flex-column h-100 overflow-hidden">
            <div className="border-bottom bg-white px-4 py-3 flex-shrink-0">
              <div className="d-flex align-items-center gap-2 mb-1">
                <span className="badge text-bg-primary px-3 py-2 rounded-pill">
                  Agent Activity
                </span>

                {loading && (
                  <span className="badge text-bg-warning rounded-pill px-3 py-2">
                    Running
                  </span>
                )}
              </div>

              <h2 className="h6 fw-bold mb-1 text-dark">
                Agent workflow and tool progress
              </h2>

              <p className="small text-secondary mb-0">
                This panel shows how the AI Agent handled each request, including tool usage and execution progress.
              </p>
            </div>

            <div className="flex-grow-1 overflow-auto p-3">
              {activityLogs.length === 0 ? (
                <div className="text-center text-secondary py-5">
                  <div className="fs-3 mb-2">⚙</div>
                  <div className="fw-semibold mb-1">No Agent activity yet</div>
                  <div className="small">
                    Send a message to see the Agent workflow and tool-calling progress.
                  </div>
                </div>
              ) : (
                <div className="d-flex flex-column gap-3">
                  {activityLogs.map((entry) => (
                    <div key={entry.id} className="card shadow-sm border-0">
                      <div className="card-body">
                        <div className="d-flex align-items-start justify-content-between gap-2 mb-2">
                          <div>
                            <div className="small text-secondary mb-1">User request</div>
                            <div className="fw-semibold text-dark">{entry.userText}</div>
                          </div>

                          <span
                            className={`badge rounded-pill px-3 py-2 ${
                              entry.status === 'completed'
                                ? 'text-bg-success'
                                : entry.status === 'failed'
                                  ? 'text-bg-danger'
                                  : 'text-bg-warning'
                            }`}
                          >
                            {entry.status === 'completed'
                              ? 'Completed'
                              : entry.status === 'failed'
                                ? 'Failed'
                                : 'Running'}
                          </span>
                        </div>

                        <div className="small text-secondary mb-3">
                          Started at {formatTime(entry.startedAt)}
                        </div>

                        <div className="d-flex flex-column gap-2">
                          {entry.steps.map((step, stepIndex) => (
                            <div key={`${entry.id}-step-${stepIndex}`} className="d-flex gap-2">
                              <div className="pt-1">
                                <span
                                  className={`badge rounded-pill ${
                                    step.status === 'done'
                                      ? 'text-bg-success'
                                      : step.status === 'failed'
                                        ? 'text-bg-danger'
                                        : 'text-bg-primary'
                                  }`}
                                >
                                  {step.status === 'done'
                                    ? '✓'
                                    : step.status === 'failed'
                                      ? '!'
                                      : '…'}
                                </span>
                              </div>

                              <div>
                                <div className="fw-semibold small text-dark">{step.label}</div>
                                {step.detail && (
                                  <div className="small text-secondary">{step.detail}</div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>

                        {entry.toolsCalled.length > 0 && (
                          <div className="mt-3">
                            <div className="small text-uppercase fw-bold text-secondary mb-2">
                              Tools Called
                            </div>

                            <div className="d-flex flex-wrap gap-2">
                              {entry.toolsCalled.map((tool, toolIndex) => (
                                <span
                                  key={`${entry.id}-tool-${toolIndex}`}
                                  className="badge rounded-pill bg-white text-primary border border-primary-subtle px-3 py-2 fw-semibold"
                                  title={JSON.stringify(tool.args || {})}
                                >
                                  <span className="me-1">{getToolIcon(tool.name)}</span>
                                  {formatToolName(tool.name)}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {entry.replyPreview && (
                          <div className="mt-3">
                            <div className="small text-uppercase fw-bold text-secondary mb-2">
                              Final Reply Preview
                            </div>

                            <div className="small text-dark bg-light rounded-3 p-2 border">
                              {entry.replyPreview}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </aside>

          {/* Right Panel: Chat */}
          <section className="col-12 col-lg-9 d-flex flex-column bg-white h-100 overflow-hidden">
            <header className="border-bottom bg-white flex-shrink-0">
              <div className="d-flex align-items-center justify-content-between gap-3 px-4 py-3">
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

                <span className="badge rounded-pill text-bg-success d-none d-md-inline-flex align-items-center gap-2 px-3 py-2">
                  <span>●</span>
                  Gemini Connected
                </span>
              </div>
            </header>

            <section className="flex-grow-1 overflow-auto px-3 px-md-4 py-4">
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
                            onClick={() => {
                              void sendMessage(prompt);
                            }}
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
                      message.type === 'user'
                        ? 'justify-content-end'
                        : 'justify-content-start'
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
                        <div className="mb-0 small lh-lg text-break">
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
                                  className="badge rounded-pill bg-light text-primary border border-primary-subtle px-3 py-2 fw-semibold"
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
                      <span
                        className="spinner-grow spinner-grow-sm text-secondary me-1"
                        role="status"
                        aria-hidden="true"
                      ></span>
                      <span
                        className="spinner-grow spinner-grow-sm text-secondary me-1"
                        role="status"
                        aria-hidden="true"
                      ></span>
                      <span
                        className="spinner-grow spinner-grow-sm text-secondary"
                        role="status"
                        aria-hidden="true"
                      ></span>
                    </div>
                  </article>
                )}

                <div ref={messagesEndRef} />
              </div>
            </section>

            <footer className="border-top bg-white px-3 px-md-4 py-3 flex-shrink-0">
              <div className="d-flex gap-2 overflow-auto pb-2">
                {quickPrompts.map((prompt) => (
                  <button
                    key={prompt}
                    type="button"
                    className="btn btn-outline-secondary btn-sm rounded-pill flex-shrink-0"
                    onClick={() => {
                      void sendMessage(prompt);
                    }}
                    disabled={loading}
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              <form
                className="d-flex align-items-end gap-2 border rounded-4 shadow-sm p-2"
                onSubmit={handleSubmit}
              >
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