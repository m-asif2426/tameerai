import { UserProfile, UserNotificationPreferences, UserAISettings, ActiveDeviceSession } from "@/types";

export const DEFAULT_USER_PROFILE: UserProfile = {
  fullName: "Aslam Bhai (Thekedar)",
  role: "Lead Contractor & Managing Partner",
  company: "Aslam Construction & Engineering Associates",
  pecNumber: "PEC/REG/CIVIL-44910",
  email: "aslam.thekedar@tameerai.pk",
  phone: "+92 300 8492011",
  city: "Lahore, Punjab (LDA Jurisdiction)",
  bio: "Specializing in commercial plaza structural framing, LDA compliance approvals, and FIDIC contractor administration in Lahore & Rawalpindi.",
};

export const DEFAULT_NOTIFICATION_PREFS: UserNotificationPreferences = {
  pbcViolations: true,
  fidicRisks: true,
  priceSpikes: true,
  weeklyDigest: false,
  whatsappAlerts: true,
};

export const DEFAULT_AI_SETTINGS: UserAISettings = {
  strictness: "strict",
  fidicThreshold: "8",
  autoCitations: true,
  marketRegion: "lahore",
  aiTone: "professional",
};

export const ACTIVE_DEVICE_SESSIONS: ActiveDeviceSession[] = [
  {
    id: "session-win",
    device: "Chrome 128 on Windows 11 (Lahore, Pakistan)",
    location: "Lahore, Pakistan",
    ip: "182.185.120.45",
    lastActive: "Current Active Session",
    isCurrent: true,
  },
  {
    id: "session-ios",
    device: "TameerAI App on iPhone 15 Pro (DHA Lahore Site)",
    location: "Lahore, Pakistan",
    ip: "39.40.112.89",
    lastActive: "2 hours ago",
    isCurrent: false,
  },
];
