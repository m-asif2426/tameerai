/**
 * TameerAI - FIDIC Contract & Legal Risk Types
 */

export type ContractRiskLevel = "high" | "medium" | "low";

export interface ContractRiskCard {
  id: string;
  clauseTitle: string;
  clauseTitleUrdu: string;
  fidicReference: string;
  pageNumber: number;
  riskLevel: ContractRiskLevel;
  riskLevelLabel: string;
  riskLevelLabelUrdu: string;
  explanation: string;
  explanationUrdu: string;
  recommendation: string;
  recommendationUrdu: string;
  impactMetric: string;
  rawClauseSnippet: string;
}

export interface ContractAnalysisSummary {
  contractTitle: string;
  standardFormat: string;
  riskScore: number; // e.g. 8 out of 10
  riskCategory: "Critical Risk" | "Moderate Risk" | "Low Risk";
  totalClausesAudited: number;
  flaggedClausesCount: number;
  lastAudited: string;
}
