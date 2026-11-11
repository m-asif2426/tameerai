import { PriceTrendPoint, BudgetComparisonPhase, MaterialCostCard, ProjectCostOverview } from "@/types";

export const PRICE_TRENDS_DATA: PriceTrendPoint[] = [
  { month: "May", steel: 232000, cement: 1350, bricks: 13800 },
  { month: "Jun", steel: 235000, cement: 1370, bricks: 14000 },
  { month: "Jul", steel: 238000, cement: 1390, bricks: 14200 },
  { month: "Aug", steel: 242000, cement: 1410, bricks: 14400 },
  { month: "Sep", steel: 245000, cement: 1430, bricks: 14500 },
  { month: "Oct (Now)", steel: 248500, cement: 1420, bricks: 14500 },
  { month: "Nov (AI)", steel: 251000, cement: 1435, bricks: 14600 },
  { month: "Dec (AI)", steel: 254000, cement: 1450, bricks: 14750 },
];

export const BUDGET_COMPARISON_DATA: BudgetComparisonPhase[] = [
  { phase: "Foundation & Raft", budget: 28.5, estimated: 29.2, overrun: 0.7 },
  { phase: "RCC Superstructure", budget: 45.0, estimated: 49.8, overrun: 4.8 },
  { phase: "Brick Masonry", budget: 14.5, estimated: 15.2, overrun: 0.7 },
  { phase: "Plumbing & Electrical", budget: 16.0, estimated: 17.1, overrun: 1.1 },
  { phase: "Finishing & Façade", budget: 16.0, estimated: 17.15, overrun: 1.15 },
];

export const PROJECT_COST_OVERVIEW: ProjectCostOverview = {
  projectBudget: 120000000, // 12 Crore PKR
  estimatedCost: 128450000, // 12.845 Crore PKR
  costVariance: 8450000, // +8.45M PKR Overrun
  variancePercentage: "+7.04%",
  riskIndicator: "Medium",
};

export const MATERIAL_CARDS_DATA: MaterialCostCard[] = [
  {
    id: "steel",
    name: "Steel (Deformed Gr.60)",
    nameUrdu: "اسٹیل (ڈیفارمڈ گریڈ 60)",
    spec: "ASTM A615 / BS 4449 (60,000 psi)",
    unit: "per Ton",
    unitUrdu: "فی ٹن",
    currentPrice: "PKR 248,500",
    boqBaseRate: "PKR 236,000",
    variance: "+5.3%",
    trend: "up",
    quantityRequired: "340 Tons",
    estimatedImpact: "+PKR 4,250,000 Overrun",
    primaryBrands: "Mughal, Ittefaq, Amreli",
    riskLevel: "high",
  },
  {
    id: "cement",
    name: "Cement (OPC 50kg Bag)",
    nameUrdu: "سیمنٹ (او پی سی 50 کلو بوری)",
    spec: "ASTM C150 / PS 232 Type-1",
    unit: "per Bag",
    unitUrdu: "فی بوری",
    currentPrice: "PKR 1,420",
    boqBaseRate: "PKR 1,340",
    variance: "+5.9%",
    trend: "up",
    quantityRequired: "18,500 Bags",
    estimatedImpact: "+PKR 1,480,000 Overrun",
    primaryBrands: "Bestway, Lucky, Fauji",
    riskLevel: "medium",
  },
  {
    id: "bricks",
    name: "Red Clay Bricks (Awwal)",
    nameUrdu: "اول سرخ اینٹیں (9x4.5x3)",
    spec: "Grade A Hand-Moulded Kiln Burnt",
    unit: "per 1,000 pcs",
    unitUrdu: "فی ہزار اینٹ",
    currentPrice: "PKR 14,500",
    boqBaseRate: "PKR 14,000",
    variance: "+3.5%",
    trend: "neutral",
    quantityRequired: "220,000 pcs",
    estimatedImpact: "+PKR 110,000 Variance",
    primaryBrands: "Bhatta Kiln A+, Multan Clay",
    riskLevel: "low",
  },
];
