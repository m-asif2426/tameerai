import { ChatSession, ChatMessage, QuickPrompt } from "@/types";

export const CHAT_SESSIONS: ChatSession[] = [
  {
    id: "session-1",
    title: "Staircase Width & PBC 2021",
    titleUrdu: "سیڑھی کی چوڑائی اور پی بی سی 2021",
    category: "today",
    timestamp: "10:32 AM",
    preview: "My staircase width is 3.5 feet. Is it okay?",
    previewUrdu: "میری سیڑھی کی چوڑائی 3.5 فٹ ہے۔ کیا یہ درست ہے؟",
    type: "code",
  },
  {
    id: "session-2",
    title: "DHA Plaza Steel Rebar Rates",
    titleUrdu: "ڈی ایچ اے پلازہ سٹیل ریبار ریٹس",
    category: "today",
    timestamp: "9:15 AM",
    preview: "What is current Gr.60 rate in Lahore?",
    previewUrdu: "لاہور میں موجودہ گریڈ 60 کا ریٹ کیا ہے؟",
    type: "cost",
  },
  {
    id: "session-3",
    title: "FIDIC Clause 14 Penalty Audit",
    titleUrdu: "فڈک شق 14 جرمانہ آڈٹ",
    category: "yesterday",
    timestamp: "Yesterday",
    preview: "Review liquidated damages cap in draft",
    previewUrdu: "ڈرافٹ میں حتمی نقصانات کی حد کا جائزہ لیں",
    type: "contract",
  },
  {
    id: "session-4",
    title: "Concrete Mix Ratio M25 vs M30",
    titleUrdu: "کنکریٹ مکس تناسب M25 بمقابلہ M30",
    category: "yesterday",
    timestamp: "Yesterday",
    preview: "Cost comparison for 5,000 sq ft slab",
    previewUrdu: "5,000 مربع فٹ سلیب کی لاگت کا موازنہ",
    type: "cost",
  },
  {
    id: "session-5",
    title: "Model Town Setback Requirements",
    titleUrdu: "ماڈل ٹاؤن سیٹ بیک تقاضے",
    category: "previous",
    timestamp: "Oct 05",
    preview: "LDA front and rear setback regulations",
    previewUrdu: "ایل ڈی اے فرنٹ اور ریئر سیٹ بیک قواعد",
    type: "code",
  },
];

export const DEFAULT_CHAT_MESSAGES: ChatMessage[] = [
  {
    id: "msg-1",
    role: "user",
    content: "My staircase width is 3.5 feet. Is it okay for my commercial plaza?",
    contentUrdu: "میری سیڑھی کی چوڑائی 3.5 فٹ ہے۔ کیا یہ کمرشل پلازہ کے لیے درست ہے؟",
    timestamp: "10:32 AM",
  },
  {
    id: "msg-2",
    role: "assistant",
    content:
      "Under the Pakistan Building Code (PBC 2021) and LDA Commercial Regulations, a 3.5-foot staircase in a commercial building with occupant load > 50 persons is non-compliant. A minimum clear width of 4.0 feet (48 inches) between finished handrails is mandatory.",
    contentUrdu:
      "پاکستان بلڈنگ کوڈ (PBC 2021) اور ایل ڈی اے کمرشل قواعد کے مطابق، کمرشل عمارت میں 3.5 فٹ کی سیڑھی قانونی تقاضے پورے نہیں کرتی۔ کم از کم 4.0 فٹ (48 انچ) چوڑائی لازمی ہے۔",
    timestamp: "10:32 AM",
    warningCard: {
      title: "Compliance Issue Found",
      titleUrdu: "بلڈنگ کوڈ کی خلاف ورزی (غیر قانونی پیمائش)",
      referenceCode: "PBC 2021",
      referenceSection: "Section 4.2.1",
      referencePage: 142,
      currentValue: "3.5 feet (42 inches)",
      requiredValue: "4.0 feet (48 inches)",
      deficit: "6 inches (152 mm) Deficit",
      recommendation:
        "Increase staircase clear width to at least 4.0 feet (48 inches). If physical column relocation is impossible, provide an alternate secondary fire escape exit or apply for an LDA variance before structural slab casting.",
      recommendationUrdu:
        "سیڑھی کی چوڑائی کو کم از کم 4.0 فٹ (48 انچ) تک بڑھائیں۔ گرڈ 4B کی دیوار کو پیچھے ہٹا کر چوڑائی پوری کریں۔",
      detailedNotes: [
        "PBC 2021 Section 4.2.1 mandates 44 inches clear width for occupant load < 50, and 48 inches for occupant load ≥ 50.",
        "NFPA 101 Life Safety Code Table 7.2.2.2.1 requires minimum 48 inches between handrails.",
        "LDA Building Regulations 2020 Clause 34 enforces immediate site plan rejection if commercial stairs are under 4 ft.",
      ],
    },
    citations: [
      { code: "PBC 2021", clause: "Sec 4.2.1", docId: "PBC-2021-Main.pdf", page: 142 },
      { code: "LDA Regulations 2020", clause: "Clause 34", docId: "LDA-Bylaws-2020.pdf", page: 28 },
    ],
  },
];

export const QUICK_PROMPTS: QuickPrompt[] = [
  {
    id: "qp-1",
    label: "Check Building Code",
    labelUrdu: "بلڈنگ کوڈ چیک کریں",
    prompt: "Check Pakistan Building Code (PBC 2021) compliance for commercial stairs and fire exits.",
    category: "compliance",
  },
  {
    id: "qp-2",
    label: "Analyze Contract",
    labelUrdu: "معاہدے کا تجزیہ کریں",
    prompt: "Analyze FIDIC Subcontract delay penalties and payment milestone clauses.",
    category: "contract",
  },
  {
    id: "qp-3",
    label: "Calculate Cost",
    labelUrdu: "لاگت کا تخمینہ لگائیں",
    prompt: "Calculate estimated cost impact of recent Grade-60 steel price hike in Lahore.",
    category: "cost",
  },
];
