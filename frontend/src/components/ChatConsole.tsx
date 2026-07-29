import React, { useState, useRef, useEffect } from 'react';
import { UserContext, Message, AgentStepTrace } from '../types';
import { apiService } from '../services/api';
import { Send, Bot, User, Sparkles, ShieldAlert, FileText, CheckCircle2, ChevronRight } from 'lucide-react';

interface ChatConsoleProps {
  userContext: UserContext;
  onNewApprovalNeeded: () => void;
}

export const ChatConsole: React.FC<ChatConsoleProps> = ({ userContext, onNewApprovalNeeded }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 'welcome-1',
      role: 'assistant',
      content: `Hello! I am your **Enterprise AI Worker**. I have access to your organization's tools (Slack, Gmail, Calendar, SQL, Jira, GitHub, Documents) under strict tenant isolation. How can I assist you today?`,
      timestamp: new Date().toLocaleTimeString(),
    },
  ]);

  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [agentTraces, setAgentTraces] = useState<AgentStepTrace[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, agentTraces]);

  const handleSend = (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || isStreaming) return;

    const userMsg: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: query,
      timestamp: new Date().toLocaleTimeString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsStreaming(true);
    setAgentTraces([]);

    const assistantMsgId = `assistant-${Date.now()}`;
    let accumulatedText = '';

    setMessages((prev) => [
      ...prev,
      {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);

    apiService.streamChat(
      userContext,
      'conv-session-100',
      query,
      // Status Event
      (statusEvent) => {
        setAgentTraces((prev) => [
          ...prev,
          {
            agent: statusEvent.agent || 'system',
            status: statusEvent.status,
            message: statusEvent.message || 'Processing step...',
            trace_id: statusEvent.trace_id,
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
      },
      // Token Event
      (delta) => {
        accumulatedText += delta;
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId ? { ...msg, content: accumulatedText } : msg
          )
        );
      },
      // Approval Event
      (approvalEvent) => {
        onNewApprovalNeeded();
        setAgentTraces((prev) => [
          ...prev,
          {
            agent: approvalEvent.agent || 'approval_gateway',
            status: 'paused',
            message: '⚠️ Action paused awaiting human approval.',
            timestamp: new Date().toLocaleTimeString(),
          },
        ]);
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId
              ? {
                  ...msg,
                  content:
                    msg.content +
                    `\n\n> ⚠️ **Human Approval Required**: The requested action (\`${approvalEvent.approval_request?.requested_action}\`) requires human review before execution. Please review the pending request in the **HITL Approvals** tab.`,
                }
              : msg
          )
        );
        setIsStreaming(false);
      },
      // Complete Event
      (resultEvent) => {
        if (resultEvent.final_response) {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: resultEvent.final_response,
                    citations: resultEvent.citations,
                  }
                : msg
            )
          );
        }
        setIsStreaming(false);
      }
    );
  };

  const quickPrompts = [
    "What does the security policy say about tenant isolation?",
    "Send an email to client@acme.com confirming 3 PM meeting",
    "Show conversations database metrics for my tenant",
    "Open a PR for issue JIRA-404 on enterprise/app",
  ];

  return (
    <div className="flex-1 flex overflow-hidden">
      {/* Main Chat Stream Container */}
      <div className="flex-1 flex flex-col justify-between bg-slate-50">
        {/* Messages Feed */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex items-start space-x-3.5 max-w-4xl ${
                msg.role === 'user' ? 'ml-auto flex-row-reverse space-x-reverse' : ''
              }`}
            >
              <div
                className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-md ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white shadow-indigo-500/20'
                    : 'bg-slate-900 text-white shadow-slate-900/20'
                }`}
              >
                {msg.role === 'user' ? <User className="w-5 h-5" /> : <Bot className="w-5 h-5" />}
              </div>

              <div
                className={`flex-1 rounded-2xl p-4 border text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 border-indigo-700 text-white font-medium shadow-sm'
                    : 'bg-white border-slate-200 text-slate-800 shadow-xs'
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Citations section */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-4 pt-3 border-t border-slate-200 space-y-2">
                    <div className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
                      <FileText className="w-3.5 h-3.5 text-indigo-600" />
                      <span>Cited Sources ({msg.citations.length})</span>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                      {msg.citations.map((cite, i) => (
                        <div key={i} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs shadow-xs">
                          <div className="font-semibold text-indigo-700 truncate">{cite.title}</div>
                          <div className="text-slate-600 text-[11px] mt-1 line-clamp-2">{cite.snippet}</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className={`mt-2 text-[10px] text-right ${msg.role === 'user' ? 'text-indigo-200' : 'text-slate-400'}`}>
                  {msg.timestamp}
                </div>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        {/* Quick Prompts Bar */}
        <div className="px-6 py-3 border-t border-slate-200 bg-slate-100/90 flex items-center space-x-2 overflow-x-auto">
          <span className="text-xs font-medium text-slate-500 flex items-center space-x-1 shrink-0">
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Try:</span>
          </span>
          {quickPrompts.map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(prompt)}
              disabled={isStreaming}
              className="px-3.5 py-1.5 rounded-lg bg-white border border-slate-200 text-xs text-slate-700 hover:text-indigo-600 hover:border-indigo-300 transition-all shrink-0 shadow-xs font-medium"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Chat Input Bar */}
        <div className="p-4 border-t border-slate-200 bg-white">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSend();
            }}
            className="flex items-center space-x-3 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 focus-within:border-indigo-500 focus-within:ring-2 focus-within:ring-indigo-500/20 transition-all"
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask Enterprise AI Worker to search docs, write SQL, draft emails, or open PRs..."
              disabled={isStreaming}
              className="flex-1 bg-transparent text-sm text-slate-900 placeholder-slate-400 focus:outline-none"
            />
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className="w-9 h-9 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md shadow-indigo-500/20"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>
        </div>
      </div>

      {/* Live Agent Reasoning Trace Panel */}
      <div className="w-80 border-l border-slate-200 bg-slate-100/90 p-4 hidden lg:flex flex-col space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 pb-3">
          <div className="flex items-center space-x-2 text-xs font-bold uppercase tracking-wider text-slate-700">
            <Sparkles className="w-4 h-4 text-indigo-600" />
            <span>Agent Execution Trace</span>
          </div>
          {isStreaming && <div className="w-2 h-2 rounded-full bg-indigo-600 animate-ping" />}
        </div>

        <div className="flex-1 overflow-y-auto space-y-3 pr-1">
          {agentTraces.length === 0 ? (
            <div className="text-center py-12 text-slate-400 text-xs">
              No active agent traces. Send a prompt to watch the Planner and Specialist agents execute in real time.
            </div>
          ) : (
            agentTraces.map((trace, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-white border border-slate-200 text-xs space-y-1.5 shadow-xs">
                <div className="flex items-center justify-between">
                  <span className="font-semibold uppercase text-[10px] tracking-wider px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                    {trace.agent}
                  </span>
                  <span className="text-[10px] text-slate-400">{trace.timestamp}</span>
                </div>
                <p className="text-slate-700 text-[11px] leading-relaxed">{trace.message}</p>
                {trace.trace_id && (
                  <div className="text-[9px] text-slate-400 font-mono truncate">
                    Trace: {trace.trace_id}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
