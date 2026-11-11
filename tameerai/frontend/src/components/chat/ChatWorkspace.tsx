"use client";

import React from "react";
import { Send, ShieldAlert } from "lucide-react";
import { ChatHeader } from "./ChatHeader";
import { ChatWelcome } from "./ChatWelcome";
import { ConversationPanel, DisplayMessage } from "./ConversationPanel";

interface ChatWorkspaceProps {
  messages: DisplayMessage[];
  activeSessionId: string;
  activeSessionTitle?: string | null;
  inputMessage: string;
  onInputChange: (val: string) => void;
  onSendMessage: (customText?: string) => void;
  leftSidebarOpen: boolean;
  rightPanelOpen: boolean;
  onToggleLeftSidebar: () => void;
  onToggleRightPanel: () => void;
  copiedId: string | null;
  onCopyMessage: (id: string, text: string) => void;
  chatBottomRef: React.RefObject<HTMLDivElement>;
  language: "en" | "ur";
}

export function ChatWorkspace({
  messages,
  activeSessionId,
  activeSessionTitle,
  inputMessage,
  onInputChange,
  onSendMessage,
  leftSidebarOpen,
  rightPanelOpen,
  onToggleLeftSidebar,
  onToggleRightPanel,
  copiedId,
  onCopyMessage,
  chatBottomRef,
  language,
}: ChatWorkspaceProps) {
  const isUrdu = language === "ur";

  return (
    <div
      data-testid="chat-workspace"
      className="flex-1 flex flex-col min-w-0 bg-white dark:bg-navy-950 overflow-hidden"
    >
      {/* 1. Compact Chat Header */}
      <ChatHeader
        activeSessionTitle={activeSessionTitle}
        leftSidebarOpen={leftSidebarOpen}
        rightPanelOpen={rightPanelOpen}
        onToggleLeftSidebar={onToggleLeftSidebar}
        onToggleRightPanel={onToggleRightPanel}
        language={language}
      />

      {/* 2. Safety Policy Mode Banner */}
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-4 py-2 flex items-center gap-2 text-xs font-bold text-amber-800 dark:text-amber-300 flex-shrink-0">
        <ShieldAlert className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0" />
        <span className="text-[11px] sm:text-xs">
          {isUrdu
            ? "حکومتی پالیسی کے تحت اے آئی ماڈل آف لائن ہے: مستند قوانین اور ریگولیٹری اصولوں پر مبنی خودکار رہنمائی فعال ہے۔"
            : "Deterministic Rule-Based Advisory Mode (AI Neural Features Offline per Safety Policy: ENABLE_GEMINI_API=False)"}
        </span>
      </div>

      {/* 3. Main Workspace Area: Welcome Screen vs Conversation Stream */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden">
        {messages.length === 0 ? (
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 flex flex-col justify-center">
            <ChatWelcome language={language} />
          </div>
        ) : (
          <ConversationPanel
            messages={messages}
            copiedId={copiedId}
            onCopyMessage={onCopyMessage}
            chatBottomRef={chatBottomRef}
            language={language}
          />
        )}
      </div>

      {/* 4. Existing Message Composer */}
      <div className="p-3 border-t border-slate-200/80 dark:border-slate-800 bg-white dark:bg-navy-950 flex items-center gap-2 flex-shrink-0">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => onInputChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              onSendMessage();
            }
          }}
          placeholder={
            isUrdu
              ? "پی بی سی 2021، سیڑھی کی چوڑائی، کنکریٹ تناسب یا قانونی شرائط کے بارے میں پوچھیں..."
              : "Ask about PBC 2021, staircase width, concrete mixes, setbacks, or FIDIC terms..."
          }
          className="flex-1 text-xs px-3.5 py-2.5 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-900 text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-orange-500/20"
        />
        <button
          type="button"
          onClick={() => onSendMessage()}
          disabled={!inputMessage.trim()}
          className="p-2.5 rounded-xl bg-orange-500 hover:bg-orange-600 disabled:opacity-40 text-white transition-all shadow-xs flex-shrink-0 cursor-pointer disabled:cursor-not-allowed"
          title={isUrdu ? "پیغام بھیجیں" : "Send message"}
          aria-label={isUrdu ? "پیغام بھیجیں" : "Send message"}
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

