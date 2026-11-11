import { apiClient } from "@/services/apiClient";
import {
  PriceTrendPoint,
  BudgetComparisonPhase,
  MaterialCostCard,
  ProjectCostOverview,
} from "@/types";

export interface CanonicalRateSnapshot {
  product_id: string;
  product_code: string;
  product_name: string;
  category: string;
  city: string;
  rate_pkr: number;
  prev_rate_pkr: number | null;
  unit: string;
  trend: "up" | "down" | "stable" | null;
  verification_status: string;
  confidence_score: number;
  observation_count: number;
  price_range: {
    min: number;
    max: number;
  };
  is_conflicted: boolean;
  snapshot_at: string;
}

export interface MaterialRateProduct {
  id: string;
  code: string;
  category: string;
  subcategory?: string;
  canonical_name: string;
  canonical_name_urdu?: string;
  standard_unit: string;
  standard_unit_urdu?: string;
  volatility_tier?: string;
}

export interface PriceHistoryPoint {
  period: string;
  median_pkr: number;
  mean_pkr: number;
  min_pkr: number;
  max_pkr: number;
  observation_count: number;
}

export interface PriceHistoryResponse {
  product_code: string;
  product_name: string;
  category: string;
  city: string;
  interval: string;
  total_observations: number;
  data_points: PriceHistoryPoint[];
  price_change_pct: number;
  volatility_pkr: number;
  trend_confidence: number;
}

export interface CrossCityComparisonResponse {
  product_code: string;
  product_name: string;
  category: string;
  standard_unit: string;
  national_median_pkr: number;
  cities: {
    city: string;
    rate_pkr: number;
    unit: string;
    trend: string;
    verification_status: string;
    confidence_score: number;
    observation_count: number;
    is_conflicted: boolean;
  }[];
}

/**
 * Cost & Material Rate Intelligence Service (Phase 03.4E)
 * Wires frontend directly to FastAPI Phase 03.1 rate intelligence endpoints.
 */
export const costService = {
  /**
   * Fetch canonical market rate snapshots (Phase 03.1 multi-source weighted composite).
   */
  async getSnapshots(city?: string, category?: string): Promise<CanonicalRateSnapshot[]> {
    try {
      const data = await apiClient.get<CanonicalRateSnapshot[]>("/material-rates/snapshots", {
        city: city || undefined,
        category: category || undefined,
      });
      return Array.isArray(data) ? data : [];
    } catch (err) {
      console.warn("[costService] getSnapshots network error, returning empty set:", err);
      return [];
    }
  },

  /**
   * Fetch registered canonical construction material products catalog.
   */
  async getProducts(category?: string): Promise<MaterialRateProduct[]> {
    try {
      return await apiClient.get<MaterialRateProduct[]>("/material-rates/products", {
        category: category || undefined,
      });
    } catch (err) {
      console.warn("[costService] getProducts error:", err);
      return [];
    }
  },

  /**
   * Fetch historical price time-series and volatility curves for Recharts.
   */
  async getPriceHistory(
    productCode: string = "STEEL_REBAR_G60",
    city: string = "Lahore",
    interval: string = "weekly"
  ): Promise<PriceHistoryResponse | null> {
    try {
      return await apiClient.get<PriceHistoryResponse>("/material-rates/history", {
        product_code: productCode,
        city,
        interval,
      });
    } catch (err) {
      console.warn("[costService] getPriceHistory error:", err);
      return null;
    }
  },

  /**
   * Compare a single product across Lahore, Karachi, and Islamabad.
   */
  async getCityComparison(productCode: string = "STEEL_REBAR_G60"): Promise<CrossCityComparisonResponse | null> {
    try {
      return await apiClient.get<CrossCityComparisonResponse>("/material-rates/compare", {
        product_code: productCode,
      });
    } catch (err) {
      console.warn("[costService] getCityComparison error:", err);
      return null;
    }
  },

  /**
   * Dynamically maps authentic canonical snapshots for a given city to frontend MaterialCostCards.
   */
  async getDynamicMaterialCards(city: "Lahore" | "Karachi" | "Islamabad" = "Lahore"): Promise<MaterialCostCard[]> {
    const snapshots = await this.getSnapshots(city);
    if (!snapshots || snapshots.length === 0) return [];

    return snapshots.map((s) => {
      const varianceVal = s.prev_rate_pkr
        ? (((s.rate_pkr - s.prev_rate_pkr) / s.prev_rate_pkr) * 100).toFixed(1)
        : "0.0";
      const varianceStr = s.prev_rate_pkr
        ? `${Number(varianceVal) >= 0 ? "+" : ""}${varianceVal}%`
        : "Benchmark";

      return {
        id: s.product_code.toLowerCase(),
        name: s.product_name,
        nameUrdu: s.product_name,
        spec: `${s.category.toUpperCase()} • Confidence ${s.confidence_score}% • ${s.observation_count} obs`,
        unit: `per ${s.unit.replace("_", " ")}`,
        unitUrdu: `فی ${s.unit.replace("_", " ")}`,
        currentPrice: `PKR ${s.rate_pkr.toLocaleString("en-PK", { maximumFractionDigits: 1 })}`,
        boqBaseRate: s.prev_rate_pkr
          ? `PKR ${s.prev_rate_pkr.toLocaleString("en-PK", { maximumFractionDigits: 1 })}`
          : "N/A",
        variance: varianceStr,
        trend: (s.trend === "up" ? "up" : s.trend === "down" ? "down" : "neutral") as "up" | "down" | "neutral",
        quantityRequired: `${s.observation_count} Source Verified`,
        estimatedImpact: `Spread: PKR ${s.price_range.min.toLocaleString()} - ${s.price_range.max.toLocaleString()}`,
        primaryBrands: s.verification_status,
        riskLevel: s.confidence_score < 70 ? "high" : s.confidence_score < 85 ? "medium" : "low",
      };
    });
  },

  // Project-level BOQ Financial Computations (returns null if project has no attached BOQ)
  async getCostOverview(projectId?: string): Promise<ProjectCostOverview | null> {
    // Phase 03.4E: Do not fabricate PKR 120M / 128.45M for unpopulated projects.
    return null;
  },

  async getPriceTrends(): Promise<PriceTrendPoint[]> {
    return [];
  },

  async getBudgetComparison(): Promise<BudgetComparisonPhase[]> {
    return [];
  },

  async getMaterialCards(city: "Lahore" | "Karachi" | "Islamabad" = "Lahore"): Promise<MaterialCostCard[]> {
    return this.getDynamicMaterialCards(city);
  },
};
