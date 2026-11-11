import { apiClient } from "./apiClient";
import { ComplianceRuleItem, ComplianceAuditSummary } from "@/types";

/**
 * Compliance Service
 * Interacts with /api/v1/projects/{projectId}/compliance-audits
 */
export const complianceService = {
  async getProjectAudits(projectId: string): Promise<any[]> {
    if (!projectId) return [];
    try {
      const response = await apiClient.get<any[]>(`/api/v1/projects/${projectId}/compliance-audits`);
      return response || [];
    } catch (err) {
      console.warn(`[complianceService] getProjectAudits failed for ${projectId}:`, err);
      return [];
    }
  },

  async getAuditFindings(projectId: string, auditId: string): Promise<any[]> {
    if (!projectId || !auditId) return [];
    try {
      const response = await apiClient.get<any[]>(`/api/v1/projects/${projectId}/compliance-audits/${auditId}/findings`);
      return response || [];
    } catch (err) {
      console.warn(`[complianceService] getAuditFindings failed for ${auditId}:`, err);
      return [];
    }
  },
};
