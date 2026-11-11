/**
 * TameerAI - Audit Setup & Execution Types
 */

export type AnalysisType = "compliance" | "contract" | "cost" | "full";

export interface BuildingTypeOption {
  id: string;
  en: string;
  ur: string;
}

export interface CityAuthorityOption {
  name: string;
  nameUrdu: string;
  authority: string;
}

export interface AuditSubmissionPayload {
  projectName: string;
  buildingType: string;
  city: string;
  area: string;
  budgetCrores: string;
  totalCoveredArea: string;
  floorsCount: string;
  analysisType: AnalysisType;
  uploadedFiles: {
    buildingPlan?: string | null;
    boqExcel?: string | null;
    contractPdf?: string | null;
    siteImages?: string[];
  };
}

export interface AuditSimulationStep {
  task: string;
  taskUrdu: string;
  progress: number;
}
