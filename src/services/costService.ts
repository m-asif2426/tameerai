import { PriceTrendPoint, BudgetComparisonPhase, MaterialCostCard, ProjectCostOverview } from "@/types";
import { PRICE_TRENDS_DATA, BUDGET_COMPARISON_DATA, PROJECT_COST_OVERVIEW, MATERIAL_CARDS_DATA, LIVE_RATES_BY_CITY, MaterialRateItem } from "@/data";

/**
 * Cost Intelligence Service
 * Backend placeholder for FastAPI live market scrapers and BOQ financial calculators.
 */
export const costService = {
  async getCostOverview(projectId?: string): Promise<ProjectCostOverview> {
    return Promise.resolve({ ...PROJECT_COST_OVERVIEW });
  },

  async getPriceTrends(): Promise<PriceTrendPoint[]> {
    return Promise.resolve([...PRICE_TRENDS_DATA]);
  },

  async getBudgetComparison(): Promise<BudgetComparisonPhase[]> {
    return Promise.resolve([...BUDGET_COMPARISON_DATA]);
  },

  async getMaterialCards(city: "Lahore" | "Karachi" | "Islamabad" = "Lahore"): Promise<MaterialCostCard[]> {
    return Promise.resolve([...MATERIAL_CARDS_DATA]);
  },

  async getLiveRates(city: string = "Lahore"): Promise<MaterialRateItem[]> {
    return Promise.resolve(LIVE_RATES_BY_CITY[city] || LIVE_RATES_BY_CITY["Lahore"]);
  },
};
