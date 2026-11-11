import { apiClient } from "@/services/apiClient";

export interface RegulatoryAuthorityRead {
  id: string;
  code: string;
  name: string;
  name_urdu?: string;
  jurisdiction_level: string;
  province?: string;
  city?: string;
  official_website?: string;
  regulatory_domain?: string;
  credibility_tier?: string;
  verification_status?: string;
}

export interface RegulatoryDocumentRead {
  id: string;
  authority_id: string;
  document_code: string;
  title: string;
  title_urdu?: string;
  official_document_number?: string;
  document_category: string;
  legal_instrument_type?: string;
  legal_force_status: string;
  jurisdiction_province?: string;
  jurisdiction_city?: string;
  status: string;
  created_at?: string;
  authority?: RegulatoryAuthorityRead;
}

export interface RegulatoryClauseRead {
  id: string;
  version_id: string;
  chapter_number?: string;
  chapter_title?: string;
  section_number?: string;
  section_title?: string;
  clause_number: string;
  clause_title?: string;
  subclause_number?: string;
  page_start?: number;
  page_end?: number;
  original_text: string;
  normalized_text?: string;
  content_type?: string;
  table_data_json?: any;
  legal_significance: string;
  review_status: string;
}

export interface RegulatoryCitation {
  citation_string: string;
  authority_code: string;
  authority_name: string;
  document_code: string;
  document_title: string;
  version_label?: string;
  section_identifier?: string;
  clause_number: string;
  page_start?: number;
  page_end?: number;
  legal_force_status: string;
  legal_significance: string;
  credibility_tier?: string;
}

export interface RegulatorySearchResult {
  clause: RegulatoryClauseRead;
  citation: RegulatoryCitation;
  relevance_score: number;
  matched_terms: string[];
}

export interface RegulatorySearchResponse {
  total: number;
  page: number;
  limit: number;
  results: RegulatorySearchResult[];
  jurisdiction_filtered: boolean;
  applied_filters: Record<string, any>;
}

export interface RegulatorySearchQuery {
  query: string;
  jurisdiction_level?: string;
  province?: string;
  city?: string;
  authority_codes?: string[];
  document_codes?: string[];
  content_types?: string[];
  legal_significance?: string;
  is_current_only?: boolean;
  limit?: number;
  offset?: number;
}

/**
 * Statutory Regulatory Knowledge Base Service (Phase 03.4B4)
 * Directly connects to FastAPI Phase 03.3 regulatory endpoints.
 */
export const regulationService = {
  /**
   * Retrieves official Pakistani regulatory issuing authorities (PEC, CDA, LDA, SBCA, etc.)
   */
  async getAuthorities(): Promise<RegulatoryAuthorityRead[]> {
    try {
      return await apiClient.get<RegulatoryAuthorityRead[]>("/regulations/authorities");
    } catch (err) {
      console.warn("[regulationService] getAuthorities error:", err);
      return [];
    }
  },

  /**
   * Retrieves authentic regulatory documents (building bylaws, acts, fire codes).
   */
  async getDocuments(authorityCode?: string, jurisdiction?: string): Promise<RegulatoryDocumentRead[]> {
    try {
      return await apiClient.get<RegulatoryDocumentRead[]>("/regulations/documents", {
        authority_code: authorityCode || undefined,
        jurisdiction: jurisdiction || undefined,
      });
    } catch (err) {
      console.warn("[regulationService] getDocuments error:", err);
      return [];
    }
  },

  /**
   * Lists extracted clauses for a specific regulatory document.
   */
  async getDocumentClauses(documentId: string): Promise<RegulatoryClauseRead[]> {
    try {
      return await apiClient.get<RegulatoryClauseRead[]>(`/regulations/documents/${documentId}/clauses`);
    } catch (err) {
      console.warn(`[regulationService] getDocumentClauses(${documentId}) error:`, err);
      return [];
    }
  },

  /**
   * Performs hybrid semantic and keyword search across Pakistani construction regulations.
   */
  async searchRegulations(payload: RegulatorySearchQuery): Promise<RegulatorySearchResponse> {
    try {
      return await apiClient.post<RegulatorySearchResponse>("/regulations/search", payload);
    } catch (err) {
      console.warn("[regulationService] searchRegulations error:", err);
      return {
        total: 0,
        page: 1,
        limit: 20,
        results: [],
        jurisdiction_filtered: false,
        applied_filters: {},
      };
    }
  },

  /**
   * Retrieves statutory safety guidance for a specific hazard category.
   */
  async getSafetyGuidance(hazardCategory: string, jurisdiction?: string): Promise<any> {
    try {
      return await apiClient.get<any>("/regulations/safety-guidance", {
        hazard_category: hazardCategory,
        jurisdiction: jurisdiction || undefined,
      });
    } catch (err) {
      console.warn("[regulationService] getSafetyGuidance error:", err);
      return null;
    }
  },
};

