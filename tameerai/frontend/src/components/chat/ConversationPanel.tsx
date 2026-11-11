/* eslint-disable @next/next/no-img-element */
"use client";

import React from "react";
import { User } from "lucide-react";
import { MessageContentRenderer } from "./MessageContentRenderer";
import { MessageActions } from "./MessageActions";
import { cn } from "@/lib/utils";

export interface DisplayMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  contentUrdu?: string;
  timestamp: string;
  citations?: Array<{
    code: string;
    clause: string;
    docId: string;
    page: number;
    year?: string | number;
    jurisdiction?: string;
    isVerified?: boolean;
  }>;
}

interface ConversationPanelProps {
  messages: DisplayMessage[];
  copiedId: string | null;
  onCopyMessage: (id: string, text: string) => void;
  chatBottomRef: React.RefObject<HTMLDivElement>;
  language: "en" | "ur";
}

export function ConversationPanel({
  messages,
  chatBottomRef,
  language,
}: ConversationPanelProps) {
  const isUrdu = language === "ur";

  return (
    <div
      data-testid="conversation-panel"
      className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5"
    >
      {messages.map((msg) => {
        const isUser = msg.role === "user";
        const textToDisplay = isUrdu && msg.contentUrdu ? msg.contentUrdu : msg.content;

        return (
          <div
            key={msg.id}
            data-testid={isUser ? "user-message" : "assistant-message"}
            className={cn(
              "flex gap-3 max-w-4xl",
              isUser ? "ml-auto flex-row-reverse" : "mr-auto",
              isUrdu && (isUser ? "mr-auto flex-row" : "ml-auto flex-row-reverse")
            )}
          >
            {isUser ? (
              <div className="w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold shadow-2xs bg-navy-900 text-white dark:bg-white dark:text-navy-900">
                <User className="w-4 h-4" />
              </div>
            ) : (
              <img
                src="/orange_robot_mascot.svg"
                alt="TameerAI"
                width={40}
                height={27}
                className="w-[40px] h-[27px] object-contain flex-shrink-0 mt-0.5"
              />
            )}

            <div
              className={cn(
                "space-y-1.5 min-w-0",
                isUser ? "max-w-xl" : "max-w-2xl lg:max-w-3xl flex-1"
              )}
            >
              <div
                className={cn(
                  "p-4 rounded-2xl text-xs leading-relaxed shadow-2xs transition-all",
                  isUser
                    ? "bg-orange-500 text-white rounded-tr-xs"
                    : "bg-slate-50 dark:bg-navy-900 border border-slate-200/80 dark:border-slate-800 text-slate-800 dark:text-slate-200 rounded-tl-xs"
                )}
              >
                {isUser ? (
                  <p className="whitespace-pre-wrap">{textToDisplay}</p>
                ) : (
                  <MessageContentRenderer
                    content={textToDisplay}
                    citations={msg.citations}
                    language={language}
                  />
                )}
              </div>

              {/* Timestamp & Actions */}
              <div
                className={cn(
                  "flex items-center gap-2 text-[10px] text-slate-400 px-1",
                  isUser ? "justify-end" : "justify-between"
                )}
              >
                <span>{msg.timestamp}</span>

                {!isUser && (
                  <MessageActions
                    messageId={msg.id}
                    content={textToDisplay}
                    language={language}
                  />
                )}
              </div>
            </div>
          </div>
        );
      })}
      <div ref={chatBottomRef} />
    </div>
  );
}
