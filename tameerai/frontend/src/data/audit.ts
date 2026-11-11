import { BuildingTypeOption, CityAuthorityOption, AuditSimulationStep } from "@/types";

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
  { name: "Multan", nameUrdu: "multan", authority: "MDA / DHA Multan" },
  { name: "Peshawar", nameUrdu: "پشاور", authority: "PDA / DHA Peshawar" },
];

export const AUDIT_SIMULATION_STEPS: AuditSimulationStep[] = [
  { task: "Parsing Architectural CAD Vectors & Dimensions...", taskUrdu: "آرکیٹیکچرل نقشے کے ویکٹرز کا تجزیہ...", progress: 25 },
  { task: "Auditing against Pakistan Building Code (PBC 2021)...", taskUrdu: "پاکستان بلڈنگ کوڈ 2021 کے ضوابط کی جانچ...", progress: 55 },
  { task: "Scanning FIDIC Subcontract Clauses & Penalties...", taskUrdu: "فڈک کنٹریکٹ کی شقوں اور جرمانوں کا جائزہ...", progress: 80 },
  { task: "Benchmarking BOQ Rates against Market Indices...", taskUrdu: "مارکیٹ ریٹس کے مطابق لاگت کا حتمی موازنہ...", progress: 100 },
];
