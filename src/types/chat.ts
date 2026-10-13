/**
 * TameerAI - AI Assistant Chat & Message Types
 */

export interface ChatSession {
  id: string;
  title: string;
  titleUrdu: string;
  category: "today" | "yesterday" | "previous";
  timestamp: string;
  preview: string;
  previewUrdu: string;
  type: "code" | "contract" | "cost" | "general";
}

export interface ChatCitation {
  code: string;
  clause: string;
  docId: string;
  page: number;
}

export interface ChatWarningCard {
  title: string;
  titleUrdu: string;
  referenceCode: string;
  referenceSection: string;
  referencePage: number;
  currentValue: string;
  requiredValue: string;
  deficit: string;
  recommendation: string;
  recommendationUrdu: string;
  detailedNotes: string[];
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  contentUrdu?: string;
  timestamp: string;
  warningCard?: ChatWarningCard;
  citations?: ChatCitation[];
  attachments?: string[];
}

export interface QuickPrompt {
  id: string;
  label: string;
  labelUrdu: string;
  prompt: string;
  category: "compliance" | "contract" | "cost";
}
