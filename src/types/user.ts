/**
 * TameerAI - User Profile & Configuration Types
 */

export interface UserProfile {
  fullName: string;
  role: string;
  company: string;
  pecNumber: string;
  email: string;
  phone: string;
  city: string;
  bio: string;
}

export interface UserNotificationPreferences {
  pbcViolations: boolean;
  fidicRisks: boolean;
  priceSpikes: boolean;
  weeklyDigest: boolean;
  whatsappAlerts: boolean;
}

export interface UserAISettings {
  strictness: "strict" | "consultative";
  fidicThreshold: "6" | "8" | "9";
  autoCitations: boolean;
  marketRegion: "lahore" | "karachi" | "islamabad";
  aiTone: "professional" | "practical" | "legal";
}

export interface ActiveDeviceSession {
  id: string;
  device: string;
  location: string;
  ip: string;
  lastActive: string;
  isCurrent: boolean;
}
