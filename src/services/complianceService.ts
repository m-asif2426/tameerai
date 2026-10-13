import { ComplianceRuleItem, ComplianceAuditSummary } from "@/types";
import { COMPLIANCE_ITEMS, COMPLIANCE_AUDIT_SUMMARY } from "@/data";

/**
 * Compliance Service
 * Backend placeholder for FastAPI CAD / Architectural blueprint parser.
 */
export const complianceService = {
  async getAuditSummary(projectId?: string): Promise<ComplianceAuditSummary> {
    return Promise.resolve({ ...COMPLIANCE_AUDIT_SUMMARY });
  },

  async getRuleItems(projectId?: string): Promise<ComplianceRuleItem[]> {
    return Promise.resolve([...COMPLIANCE_ITEMS]);
  },
};
