import { AuditSubmissionPayload, AuditSimulationStep, BuildingTypeOption, CityAuthorityOption } from "@/types";
import { BUILDING_TYPE_OPTIONS, PAKISTAN_CITIES_OPTIONS, AUDIT_SIMULATION_STEPS } from "@/data";

/**
 * Audit Setup & Engine Service
 * Backend placeholder for FastAPI audit job scheduler.
 */
export const auditService = {
  async getBuildingTypes(): Promise<BuildingTypeOption[]> {
    return Promise.resolve([...BUILDING_TYPE_OPTIONS]);
  },

  async getCities(): Promise<CityAuthorityOption[]> {
    return Promise.resolve([...PAKISTAN_CITIES_OPTIONS]);
  },

  async getSimulationSteps(): Promise<AuditSimulationStep[]> {
    return Promise.resolve([...AUDIT_SIMULATION_STEPS]);
  },

  async submitAudit(payload: AuditSubmissionPayload): Promise<{ jobId: string; status: string }> {
    return Promise.resolve({
      jobId: `JOB-${Date.now()}`,
      status: "processing",
    });
  },
};
