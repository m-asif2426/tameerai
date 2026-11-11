/**
 * TameerAI - Consulting Reports Types & Interfaces
 */

export type ReportCategory = "compliance" | "contract" | "cost";
export type ReportStatus = "certified" | "action_required" | "overrun_alert" | "in_review" | "approved";

export interface ConsultingReport {
  id: string;
  title: string;
  titleUrdu: string;
  category: ReportCategory;
  categoryLabel: string;
  projectName: string;
  projectNameUrdu: string;
  date: string;
  status: ReportStatus;
  statusLabel: string;
  statusLabelUrdu: string;
  fileSize: string;
  pageCount: number;
  author: string;
  executiveSummary: string;
  keyMetric: string;
}
