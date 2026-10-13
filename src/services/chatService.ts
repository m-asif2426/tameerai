import { ChatSession, ChatMessage, QuickPrompt } from "@/types";
import { CHAT_SESSIONS, DEFAULT_CHAT_MESSAGES, QUICK_PROMPTS } from "@/data";

/**
 * AI Assistant Chat Service
 * Backend placeholder for FastAPI LLM / Gemini / PBC 2021 RAG router.
 */
export const chatService = {
  async getSessions(): Promise<ChatSession[]> {
    return Promise.resolve([...CHAT_SESSIONS]);
  },

  async getMessages(sessionId: string): Promise<ChatMessage[]> {
    return Promise.resolve([...DEFAULT_CHAT_MESSAGES]);
  },

  async sendMessage(sessionId: string, prompt: string): Promise<ChatMessage> {
    const responseMessage: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "assistant",
      content: `AI analysis response for: "${prompt}". Validated against Pakistan Building Code (PBC 2021).`,
      timestamp: "Just now",
    };
    return Promise.resolve(responseMessage);
  },

  async getQuickPrompts(): Promise<QuickPrompt[]> {
    return Promise.resolve([...QUICK_PROMPTS]);
  },
};
