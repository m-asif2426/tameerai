/**
 * TameerAI - Project Types & Interfaces
 */

export type ProjectCity = "Lahore" | "Karachi" | "Islamabad";
export type ProjectStatus = "Under Analysis" | "Active" | "Planning" | "Completed";
export type ProjectRisk = "Low" | "Medium" | "High";
export type WorkspaceTab = "overview" | "ai_chat" | "documents" | "compliance" | "contract" | "cost" | "reports";

export interface Project {
  id: string;
  name: string;
  nameUrdu: string;
  location: string;
  locationUrdu?: string;
  city: ProjectCity;
  cityUrdu: string;
  type: string;
  typeUrdu: string;
  budgetCrore: number;
  budgetRaw: number;
  spentCrore: number;
  status: ProjectStatus;
  statusUrdu: string;
  risk: ProjectRisk;
  riskUrdu: string;
  complianceScore: number;
  lastUpdate: string;
  lastUpdateUrdu: string;
  floors: number;
  areaSqft: string;
  engineer: string;
  governingAuthority?: string;
  handoverDate?: string;
}

export interface ProjectDocument {
  id: string;
  name: string;
  type: string;
  size: string;
  uploadedBy: string;
  uploadTime: string;
  status: "Verified" | "Review Required" | "Pending Analysis";
}

export interface ProjectMilestone {
  title: string;
  date: string;
  status: "completed" | "in_progress" | "pending";
}

export interface ProjectActivity {
  action: string;
  time: string;
  user: string;
  type: "compliance" | "contract" | "cost" | "upload";
}

export interface CreateProjectPayload {
  name: string;
  location: string;
  city: ProjectCity;
  type: string;
  budgetCrore: number;
  floors?: number;
  areaSqft?: string;
}
