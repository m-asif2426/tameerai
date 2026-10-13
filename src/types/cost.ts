/**
 * TameerAI - Cost Intelligence & Commodity Types
 */

export interface PriceTrendPoint {
  month: string;
  steel: number;
  cement: number;
  bricks: number;
}

export interface BudgetComparisonPhase {
  phase: string;
  budget: number;
  estimated: number;
  overrun: number;
}

export interface MaterialCostCard {
  id: string;
  name: string;
  nameUrdu: string;
  spec: string;
  unit: string;
  unitUrdu: string;
  currentPrice: string;
  boqBaseRate: string;
  variance: string;
  trend: "up" | "down" | "neutral";
  quantityRequired: string;
  estimatedImpact: string;
  primaryBrands: string;
  riskLevel: "high" | "medium" | "low";
}

export interface ProjectCostOverview {
  projectBudget: number;
  estimatedCost: number;
  costVariance: number;
  variancePercentage: string;
  riskIndicator: "Low" | "Medium" | "High";
}
