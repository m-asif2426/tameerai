import { ConsultingReport, ReportCategory } from "@/types";
import { CONSULTING_REPORTS } from "@/data";

/**
 * Consulting Reports Service
 * Backend placeholder for FastAPI PDF report generator and download service.
 */
export const reportService = {
  async getReports(category?: ReportCategory | "all"): Promise<ConsultingReport[]> {
    if (!category || category === "all") {
      return Promise.resolve([...CONSULTING_REPORTS]);
    }
    return Promise.resolve(CONSULTING_REPORTS.filter((r) => r.category === category));
  },

  async getReportById(id: string): Promise<ConsultingReport | null> {
    const report = CONSULTING_REPORTS.find((r) => r.id === id) || null;
    return Promise.resolve(report);
  },

  async downloadReportPdf(id: string): Promise<{ success: boolean; filename: string }> {
    const report = CONSULTING_REPORTS.find((r) => r.id === id);
    return Promise.resolve({
      success: true,
      filename: `${report?.id || "report"}_${report?.projectName.replace(/\s+/g, "_") || "dossier"}.pdf`,
    });
  },
};
