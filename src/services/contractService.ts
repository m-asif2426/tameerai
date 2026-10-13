import { ContractRiskCard, ContractAnalysisSummary } from "@/types";
import { CONTRACT_RISKS, CONTRACT_ANALYSIS_SUMMARY } from "@/data";

/**
 * Contract Service
 * Backend placeholder for FastAPI FIDIC / PEC contract legal NLP analyzer.
 */
export const contractService = {
  async getAnalysisSummary(contractId?: string): Promise<ContractAnalysisSummary> {
    return Promise.resolve({ ...CONTRACT_ANALYSIS_SUMMARY });
  },

  async getRiskCards(contractId?: string): Promise<ContractRiskCard[]> {
    return Promise.resolve([...CONTRACT_RISKS]);
  },
};
