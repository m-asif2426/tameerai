import { apiClient } from "./apiClient";
import { ContractRiskCard, ContractAnalysisSummary } from "@/types";

export interface ContractAnalysis {
  id: string;
  uuid: string;
  projectId: string;
  contractTitle: string;
  contractTitleUrdu?: string;
  standardFormat: string;
  standardFormatUrdu?: string;
  riskScore?: number;
  riskCategory?: string;
  riskCategoryUrdu?: string;
  totalClausesAudited: number;
  flaggedClausesCount: number;
  status: string;
  documentId?: string;
  lastAudited?: string;
  createdAt: string;
  riskCards?: ContractRiskCard[];
}

/**
 * TameerAI - Contract Intelligence Service
 * Communicates with backend endpoints at /api/v1/projects/{projectId}/contract-analyses
 * Strictly grounded in real workspace data without dummy fallbacks.
 */
export const contractService = {
  async getProjectAnalyses(projectId: string): Promise<ContractAnalysis[]> {
    if (!projectId) return [];
    try {
      const response = await apiClient.get<ContractAnalysis[]>(
        `/api/v1/projects/${projectId}/contract-analyses`
      );
      return response || [];
    } catch (err) {
      console.warn(`[contractService] getProjectAnalyses failed for ${projectId}:`, err);
      return [];
    }
  },

  async getAnalysisById(projectId: string, analysisId: string): Promise<ContractAnalysis | null> {
    if (!projectId || !analysisId) return null;
    try {
      const response = await apiClient.get<ContractAnalysis>(
        `/api/v1/projects/${projectId}/contract-analyses/${analysisId}`
      );
      return response || null;
    } catch (err) {
      console.warn(`[contractService] getAnalysisById failed for ${analysisId}:`, err);
      return null;
    }
  },

  async getRiskCards(projectId: string, analysisId: string): Promise<ContractRiskCard[]> {
    if (!projectId || !analysisId) return [];
    try {
      const response = await apiClient.get<ContractRiskCard[]>(
        `/api/v1/projects/${projectId}/contract-analyses/${analysisId}/risk-cards`
      );
      return response || [];
    } catch (err) {
      console.warn(`[contractService] getRiskCards failed for ${analysisId}:`, err);
      return [];
    }
  },

  async createAnalysis(
    projectId: string,
    data: {
      contractTitle: string;
      standardFormat: string;
      documentId?: string;
    }
  ): Promise<ContractAnalysis | null> {
    try {
      const response = await apiClient.post<ContractAnalysis>(
        `/api/v1/projects/${projectId}/contract-analyses`,
        data
      );
      return response || null;
    } catch (err) {
      console.error("[contractService] createAnalysis failed:", err);
      throw err;
    }
  },
};
