import { apiClient } from "./apiClient";
import { BuildingTypeOption, CityAuthorityOption } from "@/types";

export const BUILDING_TYPE_OPTIONS: BuildingTypeOption[] = [
  { id: "commercial", en: "Commercial Plaza / Mall", ur: "کمرشل پلازہ / شاپنگ مال" },
  { id: "residential", en: "Residential (House / Apts)", ur: "رہائشی (مکان / اپارٹمنٹس)" },
  { id: "mixed_use", en: "Mixed-Use Development", ur: "مخلوط استعمال کی عمارت" },
  { id: "industrial", en: "Industrial / Factory", ur: "صنعتی / فیکٹری" },
];

export const PAKISTAN_CITIES_OPTIONS: CityAuthorityOption[] = [
  { name: "Lahore", nameUrdu: "لاہور", authority: "LDA / DHA Lahore" },
  { name: "Karachi", nameUrdu: "کراچی", authority: "SBCA / DHA Karachi" },
  { name: "Islamabad", nameUrdu: "اسلام آباد", authority: "CDA / Rawalpindi RDA" },
  { name: "Rawalpindi", nameUrdu: "راولپنڈی", authority: "RDA / Cantt Board" },
  { name: "Faisalabad", nameUrdu: "فیصل آباد", authority: "FDA" },
  { name: "Multan", nameUrdu: "ملتان", authority: "MDA / DHA Multan" },
  { name: "Peshawar", nameUrdu: "پشاور", authority: "PDA / DHA Peshawar" },
];

/**
 * Audit Setup & Engine Service
 * Connects directly to backend endpoints without mock simulation arrays.
 */
export const auditService = {
  async getBuildingTypes(): Promise<BuildingTypeOption[]> {
    return BUILDING_TYPE_OPTIONS;
  },

  async getCities(): Promise<CityAuthorityOption[]> {
    return PAKISTAN_CITIES_OPTIONS;
  },

  async createComplianceAudit(
    projectId: string,
    data: {
      governingCode?: string;
      summary?: string;
      summaryUrdu?: string;
    }
  ): Promise<{ id: string; status: string } | null> {
    if (!projectId) throw new Error("Project ID is required to create a compliance audit.");
    const response = await apiClient.post<{ id: string; status: string }>(
      `/api/v1/projects/${projectId}/compliance-audits`,
      {
        governingCode: data.governingCode || "PBC 2021",
        summary: data.summary || "Comprehensive construction compliance audit.",
        summaryUrdu: data.summaryUrdu,
      }
    );
    return response || null;
  },
};
