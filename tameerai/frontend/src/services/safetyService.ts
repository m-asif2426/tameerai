import { apiClient } from "@/services/apiClient";

export interface DamageIndicatorItem {
  code: string;
  category: string;
  description: string;
}

export interface SafetyEvaluationRequest {
  query: string;
  language?: string;
  project_id?: string | null;
}

export interface SafetyEvaluationResponse {
  risk_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL";
  severity_level: string;
  severity_code: number;
  severity_name: string;
  hazard_category: string;
  is_critical: boolean;
  is_high_risk: boolean;
  damage_indicators: string[];
  triggered_rule_identifiers: string[];
  missing_engineering_variables: string[];
  safety_advisory: string | null;
  requires_immediate_evacuation: boolean;
  requires_professional_inspection: boolean;
  pec_review_required: boolean;
  is_diy_hazard: boolean;
  diy_hazard_type: string | null;
  rationale: string;
  policy_version: string;
}

export interface PECVerificationRequest {
  pec_number: string;
  engineer_name?: string | null;
}

export interface PECVerificationResponse {
  is_format_valid: boolean;
  is_valid: boolean;
  is_verified: boolean;
  verification_status: string;
  pec_number: string;
  normalized_number?: string | null;
  detected_discipline?: string | null;
  structural_authorization_eligible: boolean;
  error_message?: string | null;
  regulatory_body: string;
  verification_disclaimer: string;
}

export interface PECSignOffRequest {
  pec_number: string;
  engineer_name: string;
  project_id?: string | null;
  physical_site_inspection_conducted: boolean;
  inspection_date?: string | null;
  findings_summary?: string | null;
  formal_clearance_issued?: boolean;
  attestation_statement?: string | null;
}

export interface PECSignOffResponse {
  sign_off_id: string;
  is_authorized: boolean;
  formal_clearance_issued: boolean;
  clearance_status: string;
  engineer_name: string;
  pec_registration_number: string;
  detected_discipline?: string | null;
  physical_site_inspection_conducted: boolean;
  attestation_submitted: boolean;
  submitted_by_authenticated_professional: boolean;
  independent_inspection_verified: boolean;
  attestation_verified: boolean;
  provenance_hash?: string | null;
  integrity_fingerprint?: string | null;
  regulatory_notice: string;
  error_message?: string | null;
}

export interface SafetyAuditRecordRead {
  assessment_id: string;
  timestamp: string;
  project_id?: string | null;
  user_id?: string | null;
  input_category: string;
  query_snippet: string;
  advisory_language: string;
  severity_classification: string;
  severity_code: number;
  severity_name: string;
  detected_indicators: string[];
  triggered_rule_identifiers: string[];
  is_diy_hazard: boolean;
  ai_usage_status: string;
  fallback_status: string;
  professional_escalation_status: string;
  pec_review_required: boolean;
  policy_version: string;
}

/**
 * Structural Safety Service (Phase 03.4B4)
 * Directly connects to FastAPI Phase 03.2 Structural Safety Engine endpoints.
 */
export const safetyService = {
  /**
   * Retrieves the comprehensive 38-indicator structural damage taxonomy.
   */
  async getIndicators(): Promise<DamageIndicatorItem[]> {
    try {
      return await apiClient.get<DamageIndicatorItem[]>("/safety/indicators");
    } catch (err) {
      console.warn("[safetyService] getIndicators error:", err);
      return [];
    }
  },

  /**
   * Deterministically evaluates a structural query for life-safety hazards.
   */
  async evaluate(payload: SafetyEvaluationRequest): Promise<SafetyEvaluationResponse> {
    return await apiClient.post<SafetyEvaluationResponse>("/safety/evaluate", payload);
  },

  /**
   * Validates Pakistan Engineering Council (PEC) registration formatting.
   */
  async verifyPec(payload: PECVerificationRequest): Promise<PECVerificationResponse> {
    return await apiClient.post<PECVerificationResponse>("/safety/verify-pec", payload);
  },

  /**
   * Submits attributable physical inspection observations.
   * Under Phase 03.2.3, formal clearance remains disabled and returns ADVISORY_ATTRIBUTABLE_RECORD_ONLY.
   */
  async submitInspectionRecord(payload: PECSignOffRequest): Promise<PECSignOffResponse> {
    return await apiClient.post<PECSignOffResponse>("/safety/sign-off", payload);
  },

  /**
   * Reads safety evaluation audit records.
   */
  async getAuditRecords(limit: number = 50, projectId?: string): Promise<SafetyAuditRecordRead[]> {
    try {
      return await apiClient.get<SafetyAuditRecordRead[]>("/safety/audit-records", {
        limit,
        projectId,
      });
    } catch (err) {
      console.warn("[safetyService] getAuditRecords error:", err);
      return [];
    }
  },
};

