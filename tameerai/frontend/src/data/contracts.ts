import { ContractRiskCard, ContractAnalysisSummary } from "@/types";

export const CONTRACT_ANALYSIS_SUMMARY: ContractAnalysisSummary = {
  contractTitle: "FIDIC Subcontract Agreement (HVAC, Façade & Civil Works)",
  standardFormat: "FIDIC Red Book / Subcontract 2017 Format",
  riskScore: 8,
  riskCategory: "Critical Risk",
  totalClausesAudited: 42,
  flaggedClausesCount: 3,
  lastAudited: "October 07, 2024",
};

export const CONTRACT_RISKS: ContractRiskCard[] = [
  {
    id: "risk-delay",
    clauseTitle: "Delay Clause (Liquidated Damages)",
    clauseTitleUrdu: "تاخیر کا ہرجانہ شق (Delay Clause)",
    fidicReference: "Sub-Clause 8.7 & Clause 14",
    pageNumber: 12,
    riskLevel: "high",
    riskLevelLabel: "Critical Risk (8/10)",
    riskLevelLabelUrdu: "انتہائی خطرہ (8/10)",
    explanation:
      "Contract imposes liquidated damages of 0.5% of total contract value per day of delay WITHOUT an aggregate liability cap. Standard PEC and FIDIC Red Book guidelines mandate a maximum 10% ceiling. Furthermore, the contractor must file extension-of-time (EOT) claims within an unreasonable 7-day window instead of the standard 28 days.",
    explanationUrdu:
      "معاہدے میں تاخیر پر بغیر کسی حد کے یومیہ 0.5 فیصد جرمانہ عائد کیا گیا ہے، جبکہ فڈک اور پی ای سی کے قواعد زیادہ سے زیادہ 10 فیصد حد مقرر کرتے ہیں۔",
    recommendation:
      "Insert an explicit aggregate delay damages cap of 10% of the Final Contract Price, and extend the EOT notification period to 28 days under FIDIC Sub-Clause 20.1.",
    recommendationUrdu:
      "تاخیر کے جرمانے کی کل حد 10 فیصد مقرر کروائیں اور ای او ٹی نوٹس کی مدت 28 دن تک بڑھائیں۔",
    impactMetric: "Potential Uncapped Liability: PKR 24M+",
    rawClauseSnippet:
      "8.7 Delay Damages: If the Subcontractor fails to complete the Works within the Time for Completion, the Subcontractor shall pay to the Main Contractor 0.5% per day of the Subcontract Price without limitation until Completion...",
  },
  {
    id: "risk-payment",
    clauseTitle: "Payment Terms (Certification & Retention)",
    clauseTitleUrdu: "ادائیگی اور کٹوتی کی شرائط (Payment Terms)",
    fidicReference: "Sub-Clause 14.7 & Clause 14.3",
    pageNumber: 18,
    riskLevel: "high",
    riskLevelLabel: "Severe Cash Flow Risk (8/10)",
    riskLevelLabelUrdu: "کیش فلو کا بڑا خطرہ (8/10)",
    explanation:
      "Payment term is set to 90 days following Interim Payment Certificate (IPC) submission (industry norm is 30–45 days). 10% retention money is contingent upon complete tenant occupancy rather than the Taking-Over Certificate (TOC). No financing markup is stipulated for late employer disbursements.",
    explanationUrdu:
      "بل جمع کروانے کے بعد ادائیگی کی مدت 90 دن رکھی گئی ہے اور 10 فیصد کٹوتی کی واپسی بلا جواز تاخیر کا شکار ہو سکتی ہے۔",
    recommendation:
      "Reduce payment timeline to 30 days post-engineer verification. Negotiate release of 50% retention upon TOC issuance and 50% upon Defect Liability Certificate (DLC). Add KIBOR + 2% late payment interest clause.",
    recommendationUrdu:
      "ادائیگی کی مدت 30 دن تک لائیں اور کائبور پلس 2 فیصد تاخیری سود کی شق شامل کروائیں۔",
    impactMetric: "Working Capital Lockup: 90 Days",
    rawClauseSnippet:
      "14.7 Payment: The Main Contractor shall pay the certified amount within 90 days after receiving the Subcontractor's monthly statement. Retention money shall be held until 100% building tenant occupancy is achieved...",
  },
  {
    id: "risk-termination",
    clauseTitle: "Termination Clause (Unilateral Default)",
    clauseTitleUrdu: "معاہدے کی منسوخی کی شق (Termination Clause)",
    fidicReference: "Sub-Clause 15.2 & Clause 16.2",
    pageNumber: 24,
    riskLevel: "high",
    riskLevelLabel: "High Contractual Risk (7/10)",
    riskLevelLabelUrdu: "اعلیٰ قانونی خطرہ (7/10)",
    explanation:
      "The employer reserves unilateral termination rights 'for convenience' with merely 7 days written notice without obligation to reimburse contractor demobilization costs, site overheads, or materials ordered. Conversely, the contractor's right to suspend works for unpaid certified bills requires an onerous 60-day cure period.",
    explanationUrdu:
      "مالک کو محض 7 دن کے نوٹس پر بغیر اخراجات ادا کیے کام ختم کرنے کا یکطرفہ حق دیا گیا ہے۔",
    recommendation:
      "Require that termination for convenience includes full reimbursement of verified site demobilization costs and materials procurement. Standardize contractor work suspension right after 21 days of non-payment.",
    recommendationUrdu:
      "بغیر وجہ کے معاہدہ ختم کرنے پر مٹیریل اور سائٹ خالی کرنے کے اخراجات کی شق شامل کروائیں۔",
    impactMetric: "Zero Demobilization Cost Recovery",
    rawClauseSnippet:
      "15.2 Termination by Main Contractor: The Main Contractor shall be entitled to terminate this Subcontract at any time for convenience upon giving 7 days written notice to the Subcontractor without incurring damages or lost profit...",
  },
];
