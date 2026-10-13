/**
 * TameerAI - Building Code & Compliance Types
 */

export type ComplianceCategory = "egress" | "structural" | "zoning" | "fire";
export type ComplianceStatus = "violation" | "warning" | "passed";

export interface CompliancePinCoordinates {
  x: number;
  y: number;
}

export interface ComplianceRuleItem {
  id: string;
  category: ComplianceCategory;
  categoryName: string;
  categoryNameUrdu: string;
  title: string;
  titleUrdu: string;
  status: ComplianceStatus;
  requiredValue: string;
  currentValue: string;
  variance?: string;
  referenceCode: string;
  referenceClause: string;
  locationGrid: string;
  description: string;
  descriptionUrdu: string;
  remedy: string;
  remedyUrdu: string;
  pinCoordinates: CompliancePinCoordinates;
}

export interface ComplianceAuditSummary {
  projectName: string;
  projectNameUrdu: string;
  overallScore: number;
  totalChecks: number;
  passedCount: number;
  warningCount: number;
  violationCount: number;
  lastAudited: string;
  governingCode: string;
}
