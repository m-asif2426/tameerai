import { apiClient } from "./apiClient";
import { ConsultingReport, ReportCategory } from "@/types";

export interface ReportItem {
  id: string;
  uuid: string;
  projectId?: string;
  complianceAuditId?: string;
  contractAnalysisId?: string;
  boqAnalysisId?: string;
  category: string;
  categoryLabel?: string;
  title: string;
  titleUrdu?: string;
  status: string;
  statusLabel?: string;
  statusLabelUrdu?: string;
  pageCount: number;
  date?: string;
  author: string;
  executiveSummary?: string;
  executiveSummaryUrdu?: string;
  keyMetric?: string;
  storageUrl?: string;
  createdAt: string;
}

/**
 * Consulting Reports Service
 * Communicates with backend endpoints at /api/v1/projects/{projectId}/reports
 * Strictly grounded in real workspace data without dummy fallbacks.
 */
export const reportService = {
  async getReports(projectId: string, category?: string): Promise<ReportItem[]> {
    if (!projectId) return [];
    try {
      const url = category && category !== "all"
        ? `/api/v1/projects/${projectId}/reports?category=${category}`
        : `/api/v1/projects/${projectId}/reports`;
      const response = await apiClient.get<ReportItem[]>(url);
      return response || [];
    } catch (err) {
      console.warn(`[reportService] getReports failed for ${projectId}:`, err);
      return [];
    }
  },

  async getReportById(projectId: string, reportId: string): Promise<ReportItem | null> {
    if (!projectId || !reportId) return null;
    try {
      const response = await apiClient.get<ReportItem>(
        `/api/v1/projects/${projectId}/reports/${reportId}`
      );
      return response || null;
    } catch (err) {
      console.warn(`[reportService] getReportById failed for ${reportId}:`, err);
      return null;
    }
  },

  async createReport(
    projectId: string,
    data: {
      title: string;
      category: string;
      pageCount?: number;
      executiveSummary?: string;
    }
  ): Promise<ReportItem | null> {
    try {
      const response = await apiClient.post<ReportItem>(
        `/api/v1/projects/${projectId}/reports`,
        data
      );
      return response || null;
    } catch (err) {
      console.error("[reportService] createReport failed:", err);
      throw err;
    }
  },
};
