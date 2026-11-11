"use client";

import { useState, useEffect } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  Scale,
  BookOpen,
  Search,
  Building2,
  FileText,
  BadgeCheck,
  ChevronRight,
  ExternalLink,
  Layers,
  ArrowRight,
  Filter,
} from "lucide-react";
import {
  regulationService,
  RegulatoryAuthorityRead,
  RegulatoryDocumentRead,
  RegulatoryClauseRead,
  RegulatorySearchResult,
} from "@/services/regulationService";

export default function RegulationsPage() {
  const { t, language } = useLanguage();
  const [activeTab, setActiveTab] = useState<"search" | "documents" | "authorities">("search");

  // Search tab state
  const [searchQuery, setSearchQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState<RegulatorySearchResult[]>([]);
  const [searchTotal, setSearchTotal] = useState(0);
  const [selectedJurisdiction, setSelectedJurisdiction] = useState<string>("all");

  // Authorities state
  const [authorities, setAuthorities] = useState<RegulatoryAuthorityRead[]>([]);
  const [loadingAuthorities, setLoadingAuthorities] = useState(false);

  // Documents state
  const [documents, setDocuments] = useState<RegulatoryDocumentRead[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<RegulatoryDocumentRead | null>(null);
  const [docClauses, setDocClauses] = useState<RegulatoryClauseRead[]>([]);
  const [loadingClauses, setLoadingClauses] = useState(false);

  // Load authorities and initial documents on mount
  useEffect(() => {
    setLoadingAuthorities(true);
    regulationService
      .getAuthorities()
      .then((data) => setAuthorities(data))
      .finally(() => setLoadingAuthorities(false));

    setLoadingDocs(true);
    regulationService
      .getDocuments()
      .then((data) => setDocuments(data))
      .finally(() => setLoadingDocs(false));
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setSearching(true);
    try {
      const res = await regulationService.searchRegulations({
        query: searchQuery.trim(),
        jurisdiction_level: selectedJurisdiction === "all" ? undefined : selectedJurisdiction,
        limit: 15,
      });
      setSearchResults(res.results || []);
      setSearchTotal(res.total || 0);
    } finally {
      setSearching(false);
    }
  };

  const handleSelectDocument = async (doc: RegulatoryDocumentRead) => {
    setSelectedDoc(doc);
    setLoadingClauses(true);
    try {
      const clauses = await regulationService.getDocumentClauses(doc.id);
      setDocClauses(clauses || []);
    } finally {
      setLoadingClauses(false);
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-fade-in">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-green-50 dark:bg-green-950/40 border border-green-200 dark:border-green-800 rounded-full mb-2">
            <Scale className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span className="text-[11px] font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">
              {t("Statutory Regulatory Knowledge Base (Phase 03.3)", "عمارتی ضوابط و قوانین نالج بیس")}
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-navy-900 dark:text-white tracking-tight">
            {t("Pakistan Construction Regulations & Bylaws", "پاکستان عمارتی قوانین و ضوابط")}
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400 mt-1 max-w-2xl">
            {t(
              "Centralized legal repository across PEC, CDA, LDA, SBCA, and KPK-EPA bylaws. Search clauses, compare jurisdictions, and cite mandatory statutory rules.",
              "پاکستان کے عمارتی ضوابط کا مرکزی ذخیرہ: پی ای سی، سی ڈی اے، ایل ڈی اے اور ایس بی سی اے قوانین کی شق وار تلاش۔"
            )}
          </p>
        </div>

        {/* Tab switcher */}
        <div className="flex items-center bg-slate-100 dark:bg-navy-900 p-1.5 rounded-xl border border-slate-200 dark:border-slate-800 self-start sm:self-auto">
          <button
            onClick={() => setActiveTab("search")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "search"
                ? "bg-orange-500 text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
            }`}
          >
            {t("Legal Search", "قانونی تلاش")}
          </button>
          <button
            onClick={() => setActiveTab("documents")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "documents"
                ? "bg-orange-500 text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
            }`}
          >
            {t("Bylaw Documents", "دستاویزات")}
          </button>
          <button
            onClick={() => setActiveTab("authorities")}
            className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
              activeTab === "authorities"
                ? "bg-orange-500 text-white shadow-xs"
                : "text-slate-600 dark:text-slate-400 hover:text-navy-900 dark:hover:text-white"
            }`}
          >
            {t("Authorities", "مجاز ادارے")}
          </button>
        </div>
      </div>

      {/* ========================================================================= */}
      {/* TAB 1: HYBRID SEMANTIC & KEYWORD LEGAL SEARCH                             */}
      {/* ========================================================================= */}
      {activeTab === "search" && (
        <div className="space-y-6">
          {/* Search Box */}
          <div className="bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-xs">
            <form onSubmit={handleSearch} className="space-y-3">
              <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                  <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
                  <input
                    type="text"
                    required
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={
                      language === "ur"
                        ? "مثال: کمرشل عمارت میں سیڑھی کی کم از کم چوڑائی اور فائر ڈور ریٹنگ..."
                        : "e.g., Minimum stairway egress width commercial occupancy, fire door rating, setback requirement..."
                    }
                    className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 text-xs sm:text-sm text-navy-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all placeholder:text-slate-400"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <select
                    value={selectedJurisdiction}
                    onChange={(e) => setSelectedJurisdiction(e.target.value)}
                    className="px-3 py-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-navy-950 text-xs font-semibold text-slate-700 dark:text-slate-300"
                  >
                    <option value="all">All Jurisdictions</option>
                    <option value="federal">Federal (PEC / PBC)</option>
                    <option value="punjab">Punjab (LDA)</option>
                    <option value="ict">Islamabad (CDA)</option>
                    <option value="sindh">Sindh (SBCA)</option>
                  </select>

                  <button
                    type="submit"
                    disabled={searching}
                    className="btn-primary text-xs font-bold px-6 py-3 rounded-xl flex items-center justify-center gap-2 flex-shrink-0"
                  >
                    {searching ? (
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    ) : (
                      <>
                        <span>{t("Search Laws", "تلاش کریں")}</span>
                        <Search className="w-4 h-4" />
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Sample Queries */}
              <div className="flex flex-wrap items-center gap-2 pt-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                  {t("Quick Queries:", "فوری سوالات:")}
                </span>
                {[
                  "Commercial building stair width PBC 2021",
                  "Fire rating of egress doors",
                  "LDA setback requirements residential",
                  "CDA basement parking floor area ratio",
                  "Earthquake seismic zone 2B reinforcement",
                ].map((q, idx) => (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => {
                      setSearchQuery(q);
                    }}
                    className="text-[11px] px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-orange-50 hover:text-orange-600 dark:hover:bg-slate-700 text-slate-600 dark:text-slate-300 transition-colors"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </form>
          </div>

          {/* Search Results Listing */}
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-slate-500">
              <span>
                {searchResults.length > 0
                  ? `Showing ${searchResults.length} verified clause matches (Total: ${searchTotal})`
                  : "Enter a query above to search Pakistan's construction regulations."}
              </span>
            </div>

            {searchResults.map((res, i) => (
              <div
                key={i}
                className="bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-xs hover:border-orange-500/40 transition-colors space-y-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-md bg-orange-50 dark:bg-orange-950/50 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-800">
                      {res.citation.authority_code}
                    </span>
                    <span className="text-xs font-bold text-navy-900 dark:text-white">
                      {res.citation.document_title}
                    </span>
                    <span className="text-xs text-slate-400">· Clause {res.citation.clause_number}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                      Score: {Math.round(res.relevance_score * 100)}%
                    </span>
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                      {res.clause.legal_significance.replace(/_/g, " ")}
                    </span>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-100 dark:border-slate-800/80">
                  <p className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed font-serif">
                    &ldquo;{res.clause.original_text}&rdquo;
                  </p>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400 pt-1">
                  <span>
                    Citation: <span className="font-mono text-slate-600 dark:text-slate-300">{res.citation.citation_string}</span>
                  </span>
                  <span>Legal Force: <strong className="text-emerald-600">{res.citation.legal_force_status}</strong></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 2: BYLAW DOCUMENTS & HIERARCHICAL CLAUSE INSPECTOR                     */}
      {/* ========================================================================= */}
      {activeTab === "documents" && (
        <div className="grid lg:grid-cols-12 gap-6 items-start">
          {/* Documents List */}
          <div className="lg:col-span-5 bg-white dark:bg-navy-900 rounded-2xl p-5 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
            <h2 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-orange-500" />
              <span>{t("Authentic Regulatory Documents", "مستند قانونی دستاویزات")}</span>
            </h2>

            {loadingDocs ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading documents...</div>
            ) : (
              <div className="space-y-2.5">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    onClick={() => handleSelectDocument(doc)}
                    className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all ${
                      selectedDoc?.id === doc.id
                        ? "bg-orange-50/70 dark:bg-orange-950/30 border-orange-500 shadow-xs"
                        : "border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-slate-50/40 dark:bg-navy-950/40"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-mono font-bold text-orange-600 dark:text-orange-400">
                        {doc.document_code}
                      </span>
                      <div className="flex items-center gap-1.5 flex-wrap justify-end">
                        {doc.status === "REVIEW_REQUIRED" && (
                          <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                            REVIEW_REQUIRED (Pilot Seed — Binary Checksum Unverified)
                          </span>
                        )}
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300">
                          {doc.legal_force_status}
                        </span>
                      </div>
                    </div>
                    <h3 className="font-bold text-navy-900 dark:text-white text-xs sm:text-sm">
                      {doc.title}
                    </h3>
                    <p className="text-[11px] text-slate-400 mt-1">
                      Category: {doc.document_category} · {doc.jurisdiction_province || "National"}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Clauses Inspector */}
          <div className="lg:col-span-7 bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-xs space-y-4">
            <h2 className="text-sm font-bold text-navy-900 dark:text-white uppercase tracking-wider flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <span>{selectedDoc ? `Clauses: ${selectedDoc.document_code}` : t("Select a Document", "دستاویز منتخب کریں")}</span>
                {selectedDoc?.status === "REVIEW_REQUIRED" && (
                  <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
                    REVIEW_REQUIRED (Pilot Seed — Binary Checksum Unverified)
                  </span>
                )}
              </div>
              {selectedDoc && (
                <span className="text-xs font-normal text-slate-400">
                  {docClauses.length} extracted clauses
                </span>
              )}
            </h2>

            {loadingClauses ? (
              <div className="p-12 text-center text-xs text-slate-400">Loading clauses...</div>
            ) : selectedDoc ? (
              <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
                {docClauses.map((clause) => (
                  <div
                    key={clause.id}
                    className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/60 dark:bg-navy-950/40 space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-xs font-bold text-navy-900 dark:text-white">
                        Clause {clause.clause_number}: {clause.clause_title || "Requirement"}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300">
                        {clause.legal_significance}
                      </span>
                    </div>
                    <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-serif">
                      {clause.original_text}
                    </p>
                    {clause.page_start && (
                      <p className="text-[10px] text-slate-400">
                        Page: {clause.page_start} - {clause.page_end}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-16 text-center text-slate-400">
                <BookOpen className="w-10 h-10 mx-auto mb-3 opacity-30" />
                <p className="text-xs">
                  {t("Click any regulatory document on the left to inspect its extracted statutory clauses.", "شقوں کا جائزہ لینے کے لیے بائیں جانب سے کوئی دستاویز منتخب کریں۔")}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* TAB 3: REGULATORY ISSUING AUTHORITIES                                     */}
      {/* ========================================================================= */}
      {activeTab === "authorities" && (
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {authorities.map((auth) => (
            <div
              key={auth.id}
              className="bg-white dark:bg-navy-900 rounded-2xl p-6 border border-slate-200 dark:border-slate-800 shadow-xs flex flex-col justify-between space-y-4 hover:border-orange-500/40 transition-colors"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono font-black px-2.5 py-1 rounded-md bg-orange-50 dark:bg-orange-950/50 text-orange-600 dark:text-orange-400 border border-orange-200 dark:border-orange-800">
                    {auth.code}
                  </span>
                  <div className="flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
                    <BadgeCheck className="w-3.5 h-3.5" />
                    <span>{auth.verification_status || "VERIFIED"}</span>
                  </div>
                </div>

                <h3 className="text-base font-bold text-navy-900 dark:text-white">
                  {auth.name}
                </h3>
                {auth.name_urdu && (
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {auth.name_urdu}
                  </p>
                )}

                <p className="text-xs text-slate-600 dark:text-slate-300 mt-3 leading-relaxed">
                  Domain: {auth.regulatory_domain || "Building Code Administration"}
                </p>
              </div>

              <div className="pt-3 border-t border-slate-100 dark:border-slate-800 text-xs flex items-center justify-between text-slate-500">
                <span className="capitalize">{auth.jurisdiction_level} Jurisdiction</span>
                {auth.official_website && (
                  <a
                    href={auth.official_website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-orange-500 hover:text-orange-600"
                  >
                    <span>Website</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

