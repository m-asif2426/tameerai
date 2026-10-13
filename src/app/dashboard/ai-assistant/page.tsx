"use client";

import { useState, useRef, useEffect } from "react";
import { useLanguage } from "@/contexts/LanguageContext";
import {
  Send,
  Bot,
  User,
  BookOpen,
  Sparkles,
  MessageSquare,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RefreshCw,
  Mic,
  MicOff,
  Paperclip,
  AlertTriangle,
  CheckCircle2,
  FileText,
  Plus,
  Search,
  Trash2,
  Download,
  ZoomIn,
  ZoomOut,
  TrendingUp,
  TrendingDown,
  ShieldAlert,
  Calculator,
  PanelRightClose,
  PanelRightOpen,
  PanelLeftClose,
  PanelLeftOpen,
  Building,
  Check,
  X,
  Volume2,
} from "lucide-react";
import { cn } from "@/lib/utils";

// --- Chat History Sessions ---
interface ChatSession {
  id: string;
  title: string;
  titleUrdu: string;
  category: "today" | "yesterday" | "previous";
  timestamp: string;
  preview: string;
  previewUrdu: string;
  type: "code" | "contract" | "cost" | "general";
}

const CHAT_SESSIONS: ChatSession[] = [
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

// --- Live Rates Data by City ---
interface MaterialRate {
  name: string;
  nameUrdu: string;
  unit: string;
  unitUrdu: string;
  rate: string;
  change: string;
  trend: "up" | "down" | "neutral";
  brand: string;
}

const LIVE_RATES: Record<string, MaterialRate[]> = {
  Lahore: [
    {
      name: "Deformed Steel Gr.60",
      nameUrdu: "ڈیفارمڈ سٹیل گریڈ 60",
      unit: "per Ton",
      unitUrdu: "فی ٹن",
      rate: "PKR 248,500",
      change: "+1.2%",
      trend: "up",
      brand: "Mughal / Ittefaq",
    },
    {
      name: "OPC Cement (50kg)",
      nameUrdu: "او پی سی سیمنٹ (50 کلو)",
      unit: "per Bag",
      unitUrdu: "فی بوری",
      rate: "PKR 1,420",
      change: "-0.7%",
      trend: "down",
      brand: "Bestway / Lucky",
    },
    {
      name: "Awwal Red Bricks",
      nameUrdu: "اول اینٹیں",
      unit: "per 1,000 pcs",
      unitUrdu: "فی ہزار",
      rate: "PKR 14,500",
      change: "0.0%",
      trend: "neutral",
      brand: "Bhatta Kiln A+",
    },
    {
      name: "Crush Aggregate (Bajri)",
      nameUrdu: "کرش بجری",
      unit: "per cu.ft",
      unitUrdu: "فی مکعب فٹ",
      rate: "PKR 125",
      change: "+0.8%",
      trend: "up",
      brand: "Margalla Hills",
    },
    {
      name: "River Sand (Ravi)",
      nameUrdu: "دریائی ریت (راوی)",
      unit: "per cu.ft",
      unitUrdu: "فی مکعب فٹ",
      rate: "PKR 65",
      change: "0.0%",
      trend: "neutral",
      brand: "Fine Washed",
    },
  ],
  Karachi: [
    {
      name: "Deformed Steel Gr.60",
      nameUrdu: "ڈیفارمڈ سٹیل گریڈ 60",
      unit: "per Ton",
      unitUrdu: "فی ٹن",
      rate: "PKR 252,000",
      change: "+1.5%",
      trend: "up",
      brand: "Amreli / Razno",
    },
    {
      name: "OPC Cement (50kg)",
      nameUrdu: "او پی سی سیمنٹ (50 کلو)",
      unit: "per Bag",
      unitUrdu: "فی بوری",
      rate: "PKR 1,450",
      change: "-0.3%",
      trend: "down",
      brand: "Lucky / Falcon",
    },
    {
      name: "Awwal Red Bricks",
      nameUrdu: "اول اینٹیں",
      unit: "per 1,000 pcs",
      unitUrdu: "فی ہزار",
      rate: "PKR 15,200",
      change: "+0.5%",
      trend: "up",
      brand: "Thatta Kiln",
    },
    {
      name: "Crush Aggregate (Bajri)",
      nameUrdu: "کرش بجری",
      unit: "per cu.ft",
      unitUrdu: "فی مکعب فٹ",
      rate: "PKR 135",
      change: "+1.0%",
      trend: "up",
      brand: "Hub River Zone",
    },
    {
      name: "River Sand (Bholari)",
      nameUrdu: "ریت (بھولاری)",
      unit: "per cu.ft",
      unitUrdu: "فی مکعب فٹ",
      rate: "PKR 72",
      change: "+0.2%",
      trend: "up",
      brand: "Coarse Grain",
    },
  ],
  Islamabad: [
    {
      name: "Deformed Steel Gr.60",
      nameUrdu: "ڈیفارمڈ سٹیل گریڈ 60",
      unit: "per Ton",
      unitUrdu: "فی ٹن",
      rate: "PKR 250,000",
      change: "+0.9%",
      trend: "up",
      brand: "Pak Steel / KSBL",
    },
    {
      name: "OPC Cement (50kg)",
      nameUrdu: "او پی سی سیمنٹ (50 کلو)",
      unit: "per Bag",
      unitUrdu: "فی بوری",
      rate: "PKR 1,410",
      change: "-0.5%",
      trend: "down",
      brand: "Fauji / Bestway",
    },
    {
      name: "Awwal Red Bricks",
      nameUrdu: "اول اینٹیں",
      unit: "per 1,000 pcs",
      unitUrdu: "فی ہزار",
      rate: "PKR 14,800",
      change: "0.0%",
      trend: "neutral",
      brand: "Rawat Kiln",
    },
    {
      name: "Crush Aggregate (Bajri)",
      nameUrdu: "کرش بجری",
      unit: "per cu.ft",
      unitUrdu: "فی مکعب فٹ",
      rate: "PKR 118",
      change: "0.0%",
      trend: "neutral",
      brand: "Taxila Quarry",
    },
    {
      name: "River Sand (Lawrencepur)",
      nameUrdu: "لارنس پور ریت",
      unit: "per cu.ft",
      unitUrdu: "فی مکعب فٹ",
      rate: "PKR 78",
      change: "+0.5%",
      trend: "up",
      brand: "Premium Plaster",
    },
  ],
};

// --- Message Structure ---
interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  contentUrdu?: string;
  timestamp: string;
  warningCard?: {
    title: string;
    titleUrdu: string;
    referenceCode: string;
    referenceSection: string;
    referencePage: number;
    currentValue: string;
    requiredValue: string;
    deficit: string;
    recommendation: string;
    recommendationUrdu: string;
    detailedNotes: string[];
  };
  citations?: {
    code: string;
    clause: string;
    docId: string;
    page: number;
  }[];
  attachments?: string[];
}

export default function AIAssistantPage() {
  const { t, language } = useLanguage();

  // Panel layout toggles
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [activeSessionId, setActiveSessionId] = useState("session-1");
  const [searchHistoryQuery, setSearchHistoryQuery] = useState("");

  // Right panel state
  const [selectedCity, setSelectedCity] = useState<"Lahore" | "Karachi" | "Islamabad">("Lahore");
  const [pdfZoom, setPdfZoom] = useState(100);
  const [activePdfDoc, setActivePdfDoc] = useState("pbc_2021");
  const [highlightClause, setHighlightClause] = useState<string | null>("4.2.1");

  // Chat input and state
  const [inputMessage, setInputMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [uploadedFile, setUploadedFile] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  // Initial Conversation containing the EXACT requested example
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-1",
      role: "user",
      content: "My staircase width is 3.5 feet. Is it okay?",
      contentUrdu: "میری سیڑھی کی چوڑائی 3.5 فٹ ہے۔ کیا یہ درست ہے؟",
      timestamp: "10:32 AM",
    },
    {
      id: "msg-2",
      role: "assistant",
      content:
        "I audited your staircase dimension against the official **Pakistan Building Code (PBC 2021)** and provincial development authority standards (LDA/CDA).",
      contentUrdu:
        "میں نے پاکستان بلڈنگ کوڈ (PBC 2021) اور ایل ڈی اے/سی ڈی اے کے معیارات کے مطابق آپ کی سیڑھی کی پیمائش کی جانچ کی ہے۔",
      timestamp: "10:32 AM",
      warningCard: {
        title: "Compliance Issue Found",
        titleUrdu: "تعمیل کا سنگین مسئلہ ملا (Non-Compliant)",
        referenceCode: "PBC 2021",
        referenceSection: "Section 4.2.1",
        referencePage: 42,
        currentValue: "3.5 ft (42 inches / 1,067 mm)",
        requiredValue: "4.0 ft (48 inches / 1,220 mm) minimum",
        deficit: "-6.0 inches (-153 mm) Deficit",
        recommendation: "Increase width.",
        recommendationUrdu: "سیڑھی کی چوڑائی میں اضافہ کریں۔",
        detailedNotes: [
          "Under PBC 2021 Section 4.2.1, stairways serving commercial, educational, or multi-family buildings with occupant load > 50 must have a clear width of not less than 4.0 ft (48 inches / 1,220 mm) measured between finished handrails.",
          "Clearance deficit of 6 inches will cause failure during Municipal / CDA / LDA plan approval and fire clearance inspection.",
          "If the building exceeds 4 stories (e.g. DHA Commercial Plaza), provision for a secondary 4.5 ft pressurized emergency egress stairwell is also mandatory.",
        ],
      },
      citations: [
        {
          code: "PBC 2021",
          clause: "Section 4.2.1",
          docId: "pbc_2021",
          page: 42,
        },
        {
          code: "LDA By-Laws 2020",
          clause: "Clause 26(b)",
          docId: "lda_bylaws",
          page: 18,
        },
        {
          code: "NFPA 101",
          clause: "Life Safety Code 7.2.2",
          docId: "nfpa_101",
          page: 95,
        },
      ],
    },
  ]);

  // Voice recording simulation
  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | undefined;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } else {
      setRecordingSeconds(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRecording]);

  const toggleRecording = () => {
    if (isRecording) {
      setIsRecording(false);
      if (!inputMessage) {
        setInputMessage(
          language === "ur"
            ? "کیا 5 منزلہ عمارت میں بیم اور کالم کا سائز کوڈ کے مطابق ہے؟"
            : "Check minimum column size and fire rating for 5-story building"
        );
      }
    } else {
      setIsRecording(true);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file.name);
    }
  };

  const scrollToBottom = () => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSendMessage = (customText?: string) => {
    const textToSend = customText || inputMessage;
    if (!textToSend.trim() && !uploadedFile) return;

    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: "user",
      content: textToSend || (uploadedFile ? `Uploaded ${uploadedFile} for AI review.` : ""),
      contentUrdu: textToSend,
      timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      attachments: uploadedFile ? [uploadedFile] : undefined,
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage("");
    setUploadedFile(null);
    setIsTyping(true);

    // Realistic construction AI responses depending on query
    setTimeout(() => {
      let aiResponse: ChatMessage;
      const lower = textToSend.toLowerCase();

      if (lower.includes("code") || lower.includes("building") || lower.includes("stair") || lower.includes("height")) {
        aiResponse = {
          id: `msg-${Date.now() + 1}`,
          role: "assistant",
          content:
            "I checked your query against the **Pakistan Building Code (PBC 2021 - Chapter 4)** and **NESPAK Structural Standards**.",
          contentUrdu: "میں نے پی بی سی 2021 اور نیسپاک معیارات کے تحت آپ کی تصدیق کی ہے۔",
          timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
          warningCard: {
            title: "Compliance Verification Complete",
            titleUrdu: "تعمیل کی تصدیق مکمل",
            referenceCode: "PBC 2021",
            referenceSection: "Section 3.4 & Table 4.1",
            referencePage: 38,
            currentValue: "Standard Specification Check",
            requiredValue: "PBC Seismic Zone 2B Factor (Z = 0.20g)",
            deficit: "Compliant with minor note on tie reinforcement",
            recommendation: "Ensure Grade 60 rebar with minimum 40mm clear cover in foundation footings.",
            recommendationUrdu: "بنیاد میں کم از کم 40 ملی میٹر کور کے ساتھ گریڈ 60 اسٹیل استعمال کریں۔",
            detailedNotes: [
              "Column ties must be spaced at maximum 100mm c/c within critical beam-column joint zones.",
              "Concrete compressive strength must not be less than f'c = 3,000 psi (20.7 MPa) at 28 days.",
            ],
          },
          citations: [
            { code: "PBC 2021", clause: "Section 3.4.2", docId: "pbc_2021", page: 38 },
            { code: "ACI 318-19", clause: "Chapter 18 Seismic", docId: "aci_318", page: 112 },
          ],
        };
      } else if (lower.includes("contract") || lower.includes("penalty") || lower.includes("fidic")) {
        aiResponse = {
          id: `msg-${Date.now() + 1}`,
          role: "assistant",
          content:
            "Contract risk scanning completed on **FIDIC Red Book 2017 & PEC Standard Bidding Documents**.",
          contentUrdu: "معاہدے کے خطرات کا جائزہ مکمل کر لیا گیا ہے۔",
          timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
          warningCard: {
            title: "Contract Risk Alert: Liquidated Damages",
            titleUrdu: "معاہدے کا خطرہ: حتمی ہرجانہ",
            referenceCode: "PEC Contract Guidelines",
            referenceSection: "Clause 14.3 & Clause 8.7",
            referencePage: 64,
            currentValue: "Unlimited delay penalty clause detected",
            requiredValue: "Maximum 10% contract price cap recommended",
            deficit: "High Financial Exposure for Contractor",
            recommendation: "Negotiate a standard 10% maximum penalty cap and 14-day cure notice period before damages apply.",
            recommendationUrdu: "معاہدے میں تاخیر کے ہرجانے کی زیادہ سے زیادہ حد 10 فیصد مقرر کروائیں۔",
            detailedNotes: [
              "Subcontractor agreement lacks price escalation clause for rebar and cement spikes.",
              "Force Majeure clause does not clearly cover currency devaluation or import restrictions.",
            ],
          },
          citations: [
            { code: "PEC Bidding Doc", clause: "Special Provisions Cl. 8.7", docId: "pec_contract", page: 64 },
          ],
        };
      } else {
        aiResponse = {
          id: `msg-${Date.now() + 1}`,
          role: "assistant",
          content:
            `Calculated cost forecast using current market rates in **${selectedCity}**:\n\n` +
            "• **Deformed Steel Gr.60:** " + LIVE_RATES[selectedCity][0].rate + " " + LIVE_RATES[selectedCity][0].unit + "\n" +
            "• **OPC Cement (50kg):** " + LIVE_RATES[selectedCity][1].rate + " " + LIVE_RATES[selectedCity][1].unit + "\n" +
            "• **Awwal Red Bricks:** " + LIVE_RATES[selectedCity][2].rate + " " + LIVE_RATES[selectedCity][2].unit + "\n\n" +
            "*Estimated material buffer: 5% recommended due to weekly fuel & transport variance.*",
          contentUrdu: `موجودہ مارکیٹ ریٹس کے مطابق لاگت کا تخمینہ تیار کر لیا گیا ہے۔`,
          timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
          citations: [
            { code: "Pakistan Steel Mills Assoc.", clause: "Weekly Index", docId: "market_rates", page: 1 },
          ],
        };
      }

      setMessages((prev) => [...prev, aiResponse]);
      setIsTyping(false);
    }, 1200);
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleQuickPrompt = (promptType: "code" | "contract" | "cost") => {
    if (promptType === "code") {
      handleSendMessage("Check Building Code: What are the fire egress and setback regulations for commercial buildings in PBC 2021?");
    } else if (promptType === "contract") {
      handleSendMessage("Analyze Contract: What are the critical risk clauses to look out for regarding subcontractor delays and retention money?");
    } else if (promptType === "cost") {
      handleSendMessage(`Calculate Cost: Estimate current steel and cement material expenditure for a 12,000 sq ft RCC frame in ${selectedCity}`);
    }
  };

  const handleStartNewChat = () => {
    setActiveSessionId(`session-${Date.now()}`);
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        role: "assistant",
        content:
          "Salam Aslam Bhai! I am **TameerAI Engineering Assistant**. Ask me about:\n\n" +
          "1. **Pakistan Building Code (PBC 2021)** compliance & zoning\n" +
          "2. **FIDIC & Subcontractor Agreement** risk audit\n" +
          "3. **Real-time Material Cost Estimation** (Steel, Cement, Bricks in Lahore, Karachi, Islamabad)",
        contentUrdu:
          "سلام اسلم بھائی! میں تعمیر اے آئی اسسٹنٹ ہوں۔ آپ بلڈنگ کوڈ، معاہدہ جات اور ریئل ٹائم مٹیریل ریٹس کے بارے میں سوال پوچھ سکتے ہیں۔",
        timestamp: new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" }),
      },
    ]);
  };

  const filteredSessions = CHAT_SESSIONS.filter((s) => {
    if (!searchHistoryQuery) return true;
    const q = searchHistoryQuery.toLowerCase();
    return s.title.toLowerCase().includes(q) || s.preview.toLowerCase().includes(q);
  });

  return (
    <div className="-m-4 sm:-m-6 lg:-m-8 h-[calc(100vh-4rem)] flex overflow-hidden bg-slate-50 dark:bg-navy-950 text-slate-800 dark:text-slate-100 font-sans">
      {/* Hidden file input */}
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileUpload}
        className="hidden"
        accept=".pdf,.dwg,.docx,.txt,.csv"
      />

      {/* ========================================================================= */}
      {/* SECTION 1: LEFT SIDEBAR - CHAT HISTORY (ChatGPT / Perplexity Style)       */}
      {/* ========================================================================= */}
      <aside
        className={cn(
          "h-full border-r border-slate-200/80 dark:border-slate-800/80 bg-white/95 dark:bg-navy-900/95 backdrop-blur-md flex flex-col transition-all duration-300 z-20 flex-shrink-0",
          leftSidebarOpen ? "w-60 xl:w-64" : "w-0 -translate-x-full overflow-hidden"
        )}
      >
        {/* Sidebar Header */}
        <div className="p-3 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between gap-2">
          <button
            onClick={handleStartNewChat}
            className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl bg-orange-500 hover:bg-orange-600 active:scale-[0.98] text-white text-xs font-bold transition-all shadow-sm shadow-orange-500/20 group"
          >
            <Plus className="w-3.5 h-3.5 transition-transform group-hover:rotate-90" />
            <span>{t("+ New Chat", "+ نئی گفتگو")}</span>
          </button>
          <button
            onClick={() => setLeftSidebarOpen(false)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Collapse history"
          >
            <PanelLeftClose className="w-4 h-4" />
          </button>
        </div>

        {/* History Search */}
        <div className="p-2.5 border-b border-slate-100 dark:border-slate-800/60">
          <div className="relative">
            <Search className="w-3 h-3 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchHistoryQuery}
              onChange={(e) => setSearchHistoryQuery(e.target.value)}
              placeholder={t("Search chats...", "تلاش کریں...")}
              className="w-full pl-8 pr-2.5 py-1.5 text-xs bg-slate-100/80 dark:bg-navy-950/70 border border-slate-200 dark:border-slate-800 rounded-lg placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-orange-500 text-slate-800 dark:text-slate-200"
            />
          </div>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto px-2 py-2.5 space-y-3.5 text-xs">
          {/* Today Group */}
          <div>
            <div className="px-2 py-0.5 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              {t("Today", "آج")}
            </div>
            <div className="space-y-0.5 mt-1">
              {filteredSessions
                .filter((s) => s.category === "today")
                .map((session) => {
                  const isActive = activeSessionId === session.id;
                  return (
                    <button
                      key={session.id}
                      onClick={() => setActiveSessionId(session.id)}
                      className={cn(
                        "w-full text-left px-2.5 py-2 rounded-xl transition-all flex items-start gap-2 group relative",
                        isActive
                          ? "bg-orange-50 dark:bg-orange-950/40 text-orange-600 dark:text-orange-400 font-semibold border border-orange-200/80 dark:border-orange-800/60 shadow-2xs"
                          : "text-slate-600 dark:text-slate-400 hover:bg-slate-100/70 dark:hover:bg-slate-800/50 hover:text-navy-900 dark:hover:text-white"
                      )}
                    >
                      <MessageSquare
                        className={cn(
                          "w-3.5 h-3.5 flex-shrink-0 mt-0.5",
                          isActive ? "text-orange-500" : "text-slate-400 group-hover:text-slate-600 dark:group-hover:text-slate-300"
                        )}
                      />
                      <div className="flex-1 min-w-0 pr-1">
                        <div className="truncate font-medium text-[11.5px]">
                          {t(session.title, session.titleUrdu)}
                        </div>
                        <div className="text-[10.5px] text-slate-400 dark:text-slate-500 truncate">
                          {t(session.preview, session.previewUrdu)}
                        </div>
                      </div>
                    </button>
                  );
                })}
            </div>
          </div>

          {/* Yesterday Group */}
          <div>
            <div className="px-2 py-0.5 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              {t("Yesterday", "گزشتہ کل")}
            </div>
            <div className="space-y-0.5 mt-1">
              {filteredSessions
                .filter((s) => s.category === "yesterday")
                .map((session) => {
                  const isActive = activeSessionId === session.id;
                  return (
                    <button
                      key={session.id}
                      onClick={() => setActiveSessionId(session.id)}
                      className={cn(
                        "w-full text-left px-2.5 py-2 rounded-xl transition-all flex items-start gap-2 group",
                        isActive
                          ? "bg-orange-50 dark:bg-orange-950/40 text-orange-600 dark:text-orange-400 font-semibold border border-orange-200/80 dark:border-orange-800/60"
                          : "text-slate-600 dark:text-slate-400 hover:bg-slate-100/70 dark:hover:bg-slate-800/50 hover:text-navy-900 dark:hover:text-white"
                      )}
                    >
                      <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-slate-400 group-hover:text-slate-600" />
                      <div className="flex-1 min-w-0 pr-1">
                        <div className="truncate font-medium text-[11.5px]">
                          {t(session.title, session.titleUrdu)}
                        </div>
                        <div className="text-[10.5px] text-slate-400 dark:text-slate-500 truncate">
                          {t(session.preview, session.previewUrdu)}
                        </div>
                      </div>
                    </button>
                  );
                })}
            </div>
          </div>

          {/* Previous 7 Days Group */}
          <div>
            <div className="px-2 py-0.5 text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider">
              {t("Previous 7 Days", "گزشتہ 7 دن")}
            </div>
            <div className="space-y-0.5 mt-1">
              {filteredSessions
                .filter((s) => s.category === "previous")
                .map((session) => {
                  const isActive = activeSessionId === session.id;
                  return (
                    <button
                      key={session.id}
                      onClick={() => setActiveSessionId(session.id)}
                      className={cn(
                        "w-full text-left px-2.5 py-2 rounded-xl transition-all flex items-start gap-2 group",
                        isActive
                          ? "bg-orange-50 dark:bg-orange-950/40 text-orange-600 dark:text-orange-400 font-semibold border border-orange-200/80 dark:border-orange-800/60"
                          : "text-slate-600 dark:text-slate-400 hover:bg-slate-100/70 dark:hover:bg-slate-800/50 hover:text-navy-900 dark:hover:text-white"
                      )}
                    >
                      <MessageSquare className="w-3.5 h-3.5 flex-shrink-0 mt-0.5 text-slate-400 group-hover:text-slate-600" />
                      <div className="flex-1 min-w-0 pr-1">
                        <div className="truncate font-medium text-[11.5px]">
                          {t(session.title, session.titleUrdu)}
                        </div>
                      </div>
                    </button>
                  );
                })}
            </div>
          </div>
        </div>

        {/* Sidebar Footer Badge */}
        <div className="p-2.5 border-t border-slate-100 dark:border-slate-800 bg-slate-50/60 dark:bg-navy-950/50 flex items-center justify-between text-[11px]">
          <div className="flex items-center gap-1.5 text-slate-500 dark:text-slate-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-medium">{t("PBC 2021 Active", "پی بی سی فعال")}</span>
          </div>
          <button
            onClick={() => setMessages([])}
            className="p-1 rounded text-slate-400 hover:text-rose-500 transition-colors"
            title="Clear current view"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </aside>

      {/* ========================================================================= */}
      {/* SECTION 2: CENTER - CONVERSATION STREAM & INPUT (Perplexity / ChatGPT)    */}
      {/* ========================================================================= */}
      <main className="flex-1 flex flex-col h-full min-w-0 bg-white dark:bg-navy-900 relative">
        {/* Top Chat Header */}
        <header className="h-12 px-3 sm:px-5 border-b border-slate-200/80 dark:border-slate-800/80 flex items-center justify-between bg-white/80 dark:bg-navy-900/80 backdrop-blur-md z-10 flex-shrink-0">
          <div className="flex items-center gap-2 min-w-0">
            {!leftSidebarOpen && (
              <button
                onClick={() => setLeftSidebarOpen(true)}
                className="p-1.5 rounded-xl text-slate-500 hover:text-navy-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                title="Open history sidebar"
              >
                <PanelLeftOpen className="w-4 h-4" />
              </button>
            )}
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center text-white shadow-xs flex-shrink-0">
              <Bot className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-1.5">
                <h1 className="text-xs sm:text-sm font-bold text-navy-900 dark:text-white truncate">
                  {t("Staircase Compliance Audit · PBC 2021", "سیڑھی تعمیل آڈٹ · پی بی سی 2021")}
                </h1>
                <span className="hidden sm:inline-flex items-center gap-1 px-1.5 py-0.5 rounded-full text-[9px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                  <Check className="w-2.5 h-2.5" /> {t("Verified", "مستند")}
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0">
            <button
              onClick={() => handleStartNewChat()}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 transition-all border border-slate-200 dark:border-slate-700"
            >
              <RefreshCw className="w-3 h-3 text-slate-400" />
              <span className="hidden sm:inline text-[11px]">{t("Reset", "دوبارہ")}</span>
            </button>
            <button
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              className={cn(
                "p-1.5 rounded-lg transition-all border",
                rightPanelOpen
                  ? "bg-orange-50 dark:bg-orange-950/40 text-orange-600 dark:text-orange-400 border-orange-200 dark:border-orange-800"
                  : "text-slate-600 dark:text-slate-400 border-slate-200 dark:border-slate-800 hover:bg-slate-100 dark:hover:bg-slate-800"
              )}
              title={rightPanelOpen ? "Close info panel" : "Open info panel"}
            >
              {rightPanelOpen ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
            </button>
          </div>
        </header>

        {/* Conversation Stream Scroll Area */}
        <div className="flex-1 overflow-y-auto px-3 sm:px-6 py-4 space-y-5">
          {messages.map((msg) => {
            const isUser = msg.role === "user";

            return (
              <div
                key={msg.id}
                className={cn(
                  "flex gap-2.5 sm:gap-3.5 max-w-4xl mx-auto transition-all",
                  isUser ? "flex-row-reverse" : "flex-row"
                )}
              >
                {/* Avatar */}
                <div
                  className={cn(
                    "w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 text-xs font-bold shadow-xs",
                    isUser
                      ? "bg-navy-900 dark:bg-slate-700 text-white"
                      : "bg-gradient-to-br from-orange-500 to-amber-600 text-white"
                  )}
                >
                  {isUser ? "AB" : <Bot className="w-4 h-4" />}
                </div>

                {/* Message Body Container */}
                <div className={cn("space-y-2.5 min-w-0 flex-1", isUser ? "items-end max-w-[85%]" : "max-w-full")}>
                  {/* Message Bubble */}
                  <div
                    className={cn(
                      "rounded-2xl p-4 text-xs sm:text-sm leading-relaxed shadow-xs",
                      isUser
                        ? "bg-navy-900 dark:bg-orange-600 text-white rounded-tr-xs ml-auto"
                        : "bg-slate-50 dark:bg-navy-950/70 border border-slate-200/90 dark:border-slate-800 text-slate-800 dark:text-slate-200 rounded-tl-xs"
                    )}
                  >
                    {/* User Attachment Chips */}
                    {msg.attachments && msg.attachments.length > 0 && (
                      <div className="mb-2 flex flex-wrap gap-1.5">
                        {msg.attachments.map((att, i) => (
                          <span
                            key={i}
                            className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white/20 text-white text-[11px] font-medium"
                          >
                            <Paperclip className="w-3 h-3" />
                            {att}
                          </span>
                        ))}
                      </div>
                    )}

                    {/* Text Content */}
                    <div className="whitespace-pre-wrap font-normal">
                      {t(msg.content, msg.contentUrdu || msg.content)}
                    </div>

                    {/* ========================================================== */}
                    {/* THE REQUESTED WARNING CARD: COMPLIANCE ISSUE FOUND          */}
                    {/* ========================================================== */}
                    {msg.warningCard && (
                      <div className="mt-3.5 p-3.5 sm:p-4 rounded-xl border border-amber-500/40 bg-amber-500/10 dark:bg-amber-950/30 text-amber-950 dark:text-amber-100 space-y-3">
                        {/* Header: Warning Card Title */}
                        <div className="flex items-center justify-between flex-wrap gap-2 pb-2 border-b border-amber-500/20">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-lg bg-amber-500 text-white flex items-center justify-center flex-shrink-0 shadow-xs">
                              <AlertTriangle className="w-4 h-4" />
                            </div>
                            <div>
                              <h3 className="font-extrabold text-xs sm:text-sm text-amber-900 dark:text-amber-200 flex items-center gap-1.5">
                                <span>{t(msg.warningCard.title, msg.warningCard.titleUrdu)}</span>
                              </h3>
                              <p className="text-[10px] text-amber-700 dark:text-amber-400">
                                {t("Critical Non-Compliance Detected", "سنگین عدم تعمیل کی نشاندہی")}
                              </p>
                            </div>
                          </div>

                          <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider bg-amber-500/20 text-amber-800 dark:text-amber-300 border border-amber-500/30">
                            PBC-SEC-4.2.1
                          </span>
                        </div>

                        {/* Reference & Values Grid */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                          {/* Reference Block */}
                          <div className="p-2.5 rounded-lg bg-white/80 dark:bg-navy-900/80 border border-amber-500/20">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                              {t("Reference", "حوالہ")}
                            </span>
                            <div className="font-bold text-navy-900 dark:text-white flex items-center gap-1.5">
                              <BookOpen className="w-3.5 h-3.5 text-orange-500" />
                              <span>{msg.warningCard.referenceCode}</span>
                            </div>
                            <p className="text-[11px] font-medium text-slate-600 dark:text-slate-300 mt-0.5">
                              {msg.warningCard.referenceSection}
                            </p>
                          </div>

                          {/* Dimensions & Deficit */}
                          <div className="p-2.5 rounded-lg bg-white/80 dark:bg-navy-900/80 border border-amber-500/20">
                            <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-0.5">
                              {t("Clear Width Comparison", "چوڑائی کا موازنہ")}
                            </span>
                            <div className="flex items-center justify-between text-[11px]">
                              <span>
                                {t("Current:", "موجودہ:")}{" "}
                                <strong className="text-rose-600 dark:text-rose-400 font-bold">
                                  {msg.warningCard.currentValue}
                                </strong>
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-[11px] mt-0.5">
                              <span>
                                {t("Required:", "مطلوبہ:")}{" "}
                                <strong className="text-emerald-600 dark:text-emerald-400 font-bold">
                                  {msg.warningCard.requiredValue}
                                </strong>
                              </span>
                              <span className="font-bold text-rose-600 dark:text-rose-400">
                                {msg.warningCard.deficit}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Recommendation Block */}
                        <div className="p-3 rounded-lg bg-amber-500/15 border border-amber-500/30">
                          <div className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 text-amber-600 dark:text-amber-400 flex-shrink-0 mt-0.5" />
                            <div>
                              <p className="font-bold text-xs text-amber-950 dark:text-amber-200">
                                {t("Recommendation:", "تجویز:")}{" "}
                                <span className="underline decoration-amber-500 font-black text-amber-900 dark:text-amber-100">
                                  {t(msg.warningCard.recommendation, msg.warningCard.recommendationUrdu)}
                                </span>
                              </p>
                              <p className="text-[11px] text-amber-850 dark:text-amber-300/90 mt-1 leading-relaxed">
                                {t(
                                  "Increase clear stairway width to at least 4.0 feet (48 inches) between finished handrails to satisfy commercial egress exit capacity.",
                                  "کمرشل اخراج کی ضروریات پوری کرنے کے لیے سیڑھی کی چوڑائی کم از کم 4.0 فٹ (48 انچ) تک بڑھائیں۔"
                                )}
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* Bullet Details */}
                        <ul className="space-y-1 text-[11px] text-amber-900/90 dark:text-amber-200/90 pl-1">
                          {msg.warningCard.detailedNotes.map((note, idx) => (
                            <li key={idx} className="flex items-start gap-1.5">
                              <span className="text-amber-500 font-bold">•</span>
                              <span>{note}</span>
                            </li>
                          ))}
                        </ul>

                        {/* Card Buttons */}
                        <div className="pt-1 flex flex-wrap gap-2">
                          <button
                            onClick={() => {
                              setRightPanelOpen(true);
                              setActivePdfDoc("pbc_2021");
                              setHighlightClause("4.2.1");
                            }}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-600 text-white text-[11px] font-bold transition-all shadow-xs"
                          >
                            <BookOpen className="w-3 h-3" />
                            <span>{t("Highlight in PDF Preview", "پی ڈی ایف میں شق دیکھیں")}</span>
                          </button>
                          <button
                            onClick={() =>
                              handleSendMessage("Calculate cost impact of increasing staircase width from 3.5ft to 4.0ft in concrete and shuttering")
                            }
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white dark:bg-navy-900 hover:bg-amber-100 dark:hover:bg-navy-800 text-amber-900 dark:text-amber-200 border border-amber-500/30 text-[11px] font-semibold transition-all"
                          >
                            <Calculator className="w-3 h-3" />
                            <span>{t("Calculate Cost Impact", "لاگت کا تخمینہ")}</span>
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Citations Pills */}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-2.5 border-t border-slate-200/60 dark:border-slate-800/80 flex flex-wrap items-center gap-1.5">
                        <span className="text-[10px] font-bold text-slate-400 mr-1 flex items-center gap-1">
                          <BookOpen className="w-3 h-3 text-orange-500" />
                          {t("Citations:", "حوالہ جات:")}
                        </span>
                        {msg.citations.map((cite, i) => (
                          <button
                            key={i}
                            onClick={() => {
                              setRightPanelOpen(true);
                              setActivePdfDoc(cite.docId);
                              setHighlightClause(cite.clause);
                            }}
                            className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md text-[10px] font-medium bg-slate-200/70 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-orange-100 dark:hover:bg-orange-950/60 hover:text-orange-600 transition-colors"
                          >
                            <span>
                              [{i + 1}] {cite.code} · {cite.clause}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Actions Bar (Assistant Only) */}
                  {!isUser && (
                    <div className="flex items-center gap-2 text-[11px] text-slate-400 pl-1">
                      <span>{msg.timestamp}</span>
                      <span className="text-slate-300 dark:text-slate-700">•</span>
                      <button
                        onClick={() => copyToClipboard(msg.content, msg.id)}
                        className="p-1 rounded hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors flex items-center gap-1"
                        title="Copy text"
                      >
                        {copiedId === msg.id ? (
                          <Check className="w-3 h-3 text-emerald-500" />
                        ) : (
                          <Copy className="w-3 h-3" />
                        )}
                        <span className="text-[10px]">{copiedId === msg.id ? t("Copied", "کاپی ہو گیا") : t("Copy", "کاپی")}</span>
                      </button>
                      <button
                        className="p-1 rounded hover:text-emerald-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        title="Helpful"
                      >
                        <ThumbsUp className="w-3 h-3" />
                      </button>
                      <button
                        className="p-1 rounded hover:text-rose-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        title="Not helpful"
                      >
                        <ThumbsDown className="w-3 h-3" />
                      </button>
                      <button
                        className="p-1 rounded hover:text-orange-500 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                        title="Read aloud"
                      >
                        <Volume2 className="w-3 h-3" />
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}

          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex gap-3 max-w-4xl mx-auto">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 text-white flex items-center justify-center flex-shrink-0 shadow-xs">
                <Bot className="w-4 h-4 animate-spin" />
              </div>
              <div className="p-3 rounded-2xl rounded-tl-xs bg-slate-100 dark:bg-navy-950/80 border border-slate-200/60 dark:border-slate-800 flex items-center gap-2 text-xs text-slate-500">
                <span className="inline-block w-2 h-2 rounded-full bg-orange-500 animate-bounce" />
                <span className="inline-block w-2 h-2 rounded-full bg-orange-500 animate-bounce [animation-delay:150ms]" />
                <span className="inline-block w-2 h-2 rounded-full bg-orange-500 animate-bounce [animation-delay:300ms]" />
                <span className="text-[11px] text-slate-400 ml-1">
                  {t("Checking PBC 2021 database & market indexes...", "پی بی سی 2021 اور ریٹ انڈیکس کی جانچ جاری...")}
                </span>
              </div>
            </div>
          )}

          <div ref={chatBottomRef} />
        </div>

        {/* ========================================================================= */}
        {/* BOTTOM SECTION: QUICK PROMPTS + INPUT BOX (Microphone, Upload, Send)     */}
        {/* ========================================================================= */}
        <div className="p-3 sm:p-4 border-t border-slate-200/80 dark:border-slate-800/80 bg-white/95 dark:bg-navy-900/95 backdrop-blur-md flex-shrink-0">
          <div className="max-w-4xl mx-auto space-y-2.5">
            {/* Quick Prompts Row */}
            <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex-shrink-0 flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-orange-500" />
                {t("Quick Prompts:", "فوری سوالات:")}
              </span>
              <button
                onClick={() => handleQuickPrompt("code")}
                className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-navy-950 hover:bg-orange-50 dark:hover:bg-orange-950/50 text-slate-700 dark:text-slate-300 hover:text-orange-600 dark:hover:text-orange-400 border border-slate-200 dark:border-slate-800 transition-all hover:border-orange-500/40 shadow-2xs"
              >
                <ShieldAlert className="w-3.5 h-3.5 text-orange-500" />
                <span>{t("Check Building Code", "بلڈنگ کوڈ چیک کریں")}</span>
              </button>
              <button
                onClick={() => handleQuickPrompt("contract")}
                className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-navy-950 hover:bg-orange-50 dark:hover:bg-orange-950/50 text-slate-700 dark:text-slate-300 hover:text-orange-600 dark:hover:text-orange-400 border border-slate-200 dark:border-slate-800 transition-all hover:border-orange-500/40 shadow-2xs"
              >
                <FileText className="w-3.5 h-3.5 text-blue-500" />
                <span>{t("Analyze Contract", "معاہدے کا تجزیہ کریں")}</span>
              </button>
              <button
                onClick={() => handleQuickPrompt("cost")}
                className="flex-shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-slate-100 dark:bg-navy-950 hover:bg-orange-50 dark:hover:bg-orange-950/50 text-slate-700 dark:text-slate-300 hover:text-orange-600 dark:hover:text-orange-400 border border-slate-200 dark:border-slate-800 transition-all hover:border-orange-500/40 shadow-2xs"
              >
                <Calculator className="w-3.5 h-3.5 text-emerald-500" />
                <span>{t("Calculate Cost", "لاگت کا تخمینہ لگائیں")}</span>
              </button>
            </div>

            {/* Uploaded File Chip Banner */}
            {uploadedFile && (
              <div className="flex items-center justify-between px-3 py-1.5 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-600 dark:text-orange-400 text-xs font-medium">
                <div className="flex items-center gap-2 truncate">
                  <Paperclip className="w-3.5 h-3.5 flex-shrink-0" />
                  <span className="truncate">{uploadedFile}</span>
                  <span className="text-[10px] text-slate-400">({t("Ready for AI audit", "تیار برائے تجزیہ")})</span>
                </div>
                <button
                  onClick={() => setUploadedFile(null)}
                  className="p-1 hover:text-rose-500 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

            {/* Microphone Listening State Pill */}
            {isRecording && (
              <div className="flex items-center justify-between px-3.5 py-1.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-400 text-xs font-bold animate-pulse">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
                  <span>
                    {t("Listening... Speak your construction question", "سن رہا ہوں... اپنا سوال بولیں")}
                  </span>
                </div>
                <span className="text-xs font-mono">00:0{recordingSeconds}s</span>
              </div>
            )}

            {/* Chat Input Container */}
            <div className="relative rounded-2xl border border-slate-300 dark:border-slate-700/80 bg-slate-50/70 dark:bg-navy-950/70 focus-within:border-orange-500 focus-within:ring-2 focus-within:ring-orange-500/20 transition-all shadow-xs">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
                placeholder={t(
                  "Ask about staircase width, steel grades, FIDIC contract clauses, or cement rates...",
                  "سیڑھی کی چوڑائی، سٹیل گریڈ، معاہدات، یا سیمنٹ کے ریٹس کے بارے میں سوال پوچھیں..."
                )}
                rows={2}
                className="w-full px-3.5 pt-2.5 pb-11 bg-transparent text-xs sm:text-sm text-navy-900 dark:text-white placeholder-slate-400 focus:outline-none resize-none leading-relaxed"
              />

              {/* Bottom Toolbar inside Input Box */}
              <div className="absolute left-2.5 right-2.5 bottom-2 flex items-center justify-between">
                {/* Left Action Buttons: Microphone + Upload File */}
                <div className="flex items-center gap-1">
                  {/* Microphone Button */}
                  <button
                    type="button"
                    onClick={toggleRecording}
                    className={cn(
                      "p-1.5 sm:px-2.5 sm:py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5",
                      isRecording
                        ? "bg-rose-500 text-white shadow-xs"
                        : "text-slate-500 hover:text-navy-900 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-slate-800"
                    )}
                    title={isRecording ? "Stop voice recording" : "Record voice question (Microphone)"}
                  >
                    {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                    <span className="hidden sm:inline text-[11px] font-medium">
                      {isRecording ? t("Stop", "روکیں") : t("Microphone", "مائیکروفون")}
                    </span>
                  </button>

                  {/* Upload File Button */}
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="p-1.5 sm:px-2.5 sm:py-1.5 rounded-xl text-slate-500 hover:text-navy-900 dark:hover:text-white hover:bg-slate-200/70 dark:hover:bg-slate-800 transition-all flex items-center gap-1.5"
                    title="Upload drawing or contract file (PDF, DWG)"
                  >
                    <Paperclip className="w-4 h-4" />
                    <span className="hidden sm:inline text-[11px] font-medium">
                      {t("Upload File", "فائل اپ لوڈ")}
                    </span>
                  </button>
                </div>

                {/* Right Action: Send Button */}
                <button
                  type="button"
                  onClick={() => handleSendMessage()}
                  disabled={!inputMessage.trim() && !uploadedFile}
                  className={cn(
                    "flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all shadow-sm",
                    inputMessage.trim() || uploadedFile
                      ? "bg-orange-500 hover:bg-orange-600 text-white shadow-orange-500/20 active:scale-95"
                      : "bg-slate-200 dark:bg-slate-800 text-slate-400 cursor-not-allowed"
                  )}
                >
                  <span>{t("Send", "بھیجیں")}</span>
                  <Send className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Helper Disclaimer */}
            <p className="text-[10.5px] text-center text-slate-400 dark:text-slate-500">
              {t(
                "TameerAI is grounded in Pakistan Building Code 2021, NESPAK standards & daily commodity market data.",
                "تعمیر اے آئی پاکستان بلڈنگ کوڈ 2021، نیسپاک معیارات اور یومیہ مارکیٹ ڈیٹا پر مبنی ہے۔"
              )}
            </p>
          </div>
        </div>
      </main>

      {/* ========================================================================= */}
      {/* SECTION 3: RIGHT INFORMATION PANEL (Live Rates & PDF Preview)            */}
      {/* ========================================================================= */}
      <aside
        className={cn(
          "h-full border-l border-slate-200/80 dark:border-slate-800/80 bg-slate-50/90 dark:bg-navy-950/90 backdrop-blur-md flex flex-col transition-all duration-300 z-20 flex-shrink-0 overflow-hidden",
          rightPanelOpen ? "w-80 lg:w-[350px] xl:w-[380px]" : "w-0 translate-x-full overflow-hidden"
        )}
      >
        {/* Right Panel Header */}
        <div className="h-12 px-3.5 border-b border-slate-200/80 dark:border-slate-800 flex items-center justify-between bg-white dark:bg-navy-900">
          <div className="flex items-center gap-2">
            <Building className="w-4 h-4 text-orange-500" />
            <h2 className="text-xs font-bold text-navy-900 dark:text-white uppercase tracking-wider">
              {t("Information Panel", "معلومات اور دستاویزات")}
            </h2>
          </div>
          <button
            onClick={() => setRightPanelOpen(false)}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            title="Close information panel"
          >
            <PanelRightClose className="w-4 h-4" />
          </button>
        </div>

        {/* Scrollable Information Body */}
        <div className="flex-1 overflow-y-auto p-3.5 space-y-4">
          {/* ------------------------------------------------------------- */}
          {/* SUB-SECTION A: LIVE RATES (Steel, Cement, Bricks)             */}
          {/* ------------------------------------------------------------- */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 p-3.5 shadow-2xs space-y-2.5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xs font-bold text-navy-900 dark:text-white flex items-center gap-1.5">
                  <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
                  <span>{t("Live Material Rates", "مارکیٹ ریٹس (لائیو)")}</span>
                </h3>
                <p className="text-[10px] text-slate-400">
                  {t("Updated today · Verified Pakistan Market", "آج تصدیق شدہ مارکیٹ ریٹس")}
                </p>
              </div>

              {/* City Selector */}
              <div className="flex bg-slate-100 dark:bg-navy-950 p-0.5 rounded-lg text-[10px] font-bold">
                {(["Lahore", "Karachi", "Islamabad"] as const).map((city) => (
                  <button
                    key={city}
                    onClick={() => setSelectedCity(city)}
                    className={cn(
                      "px-2 py-0.5 rounded-md transition-all",
                      selectedCity === city
                        ? "bg-white dark:bg-navy-800 text-orange-600 dark:text-orange-400 shadow-2xs font-bold"
                        : "text-slate-500 hover:text-navy-900 dark:hover:text-white"
                    )}
                  >
                    {city === "Lahore" ? "LHR" : city === "Karachi" ? "KHI" : "ISB"}
                  </button>
                ))}
              </div>
            </div>

            {/* Rates Table / List */}
            <div className="space-y-1.5">
              {LIVE_RATES[selectedCity].map((item, idx) => (
                <div
                  key={idx}
                  className="p-2 rounded-xl bg-slate-50 dark:bg-navy-950/70 border border-slate-200/70 dark:border-slate-800/80 flex items-center justify-between text-xs hover:border-orange-500/40 transition-colors"
                >
                  <div className="min-w-0 pr-2">
                    <p className="font-bold text-navy-900 dark:text-white truncate text-[11.5px]">
                      {t(item.name, item.nameUrdu)}
                    </p>
                    <p className="text-[10px] text-slate-400 truncate">
                      {item.brand} · {t(item.unit, item.unitUrdu)}
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="font-extrabold text-navy-900 dark:text-white font-mono text-xs">
                      {item.rate}
                    </p>
                    <span
                      className={cn(
                        "inline-flex items-center gap-0.5 text-[9.5px] font-bold",
                        item.trend === "up"
                          ? "text-rose-500"
                          : item.trend === "down"
                          ? "text-emerald-500"
                          : "text-slate-400"
                      )}
                    >
                      {item.trend === "up" && <TrendingUp className="w-2.5 h-2.5" />}
                      {item.trend === "down" && <TrendingDown className="w-2.5 h-2.5" />}
                      {item.change}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Rate Insight Footer */}
            <div className="pt-1 flex items-center justify-between text-[10px] text-slate-400 border-t border-slate-100 dark:border-slate-800">
              <span>{t("City: ", "شہر: ")}<strong>{selectedCity}</strong></span>
              <button
                onClick={() =>
                  handleSendMessage(`Provide historical 30-day price trend analysis for Grade 60 steel and OPC cement in ${selectedCity}`)
                }
                className="text-orange-500 hover:underline font-semibold"
              >
                {t("Ask AI to Forecast →", "اے آئی پیشگوئی دیکھیں →")}
              </button>
            </div>
          </div>

          {/* ------------------------------------------------------------- */}
          {/* SUB-SECTION B: PDF PREVIEW AREA                               */}
          {/* ------------------------------------------------------------- */}
          <div className="rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-900 overflow-hidden shadow-2xs flex flex-col">
            {/* PDF Toolbar */}
            <div className="p-2.5 border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-navy-950/80 flex items-center justify-between flex-wrap gap-1.5 text-xs">
              <div className="flex items-center gap-1.5 min-w-0">
                <FileText className="w-3.5 h-3.5 text-orange-500 flex-shrink-0" />
                <div className="min-w-0">
                  <p className="font-bold text-navy-900 dark:text-white truncate text-[11px]">
                    {activePdfDoc === "pbc_2021"
                      ? "PBC_2021_Ch4_Egress.pdf"
                      : "DHA_Commercial_Plaza_Arch.pdf"}
                  </p>
                  <p className="text-[9.5px] text-slate-400">
                    {t("Page 42 of 188 · Grounded PDF", "صفحہ 42 از 188")}
                  </p>
                </div>
              </div>

              {/* Controls */}
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPdfZoom((z) => Math.max(80, z - 10))}
                  className="p-1 rounded text-slate-400 hover:text-navy-900 dark:hover:text-white"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-3.5 h-3.5" />
                </button>
                <span className="text-[10px] font-mono text-slate-500 px-1">{pdfZoom}%</span>
                <button
                  onClick={() => setPdfZoom((z) => Math.min(130, z + 10))}
                  className="p-1 rounded text-slate-400 hover:text-navy-900 dark:hover:text-white"
                  title="Zoom In"
                >
                  <ZoomIn className="w-3.5 h-3.5" />
                </button>
                <button
                  className="p-1 rounded text-slate-400 hover:text-navy-900 dark:hover:text-white ml-0.5"
                  title="Download PDF"
                >
                  <Download className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Document Select tabs */}
            <div className="px-3 pt-2 pb-1 border-b border-slate-100 dark:border-slate-800/80 flex gap-2 text-[10px]">
              <button
                onClick={() => {
                  setActivePdfDoc("pbc_2021");
                  setHighlightClause("4.2.1");
                }}
                className={cn(
                  "px-2.5 py-1 rounded-md font-semibold transition-all",
                  activePdfDoc === "pbc_2021"
                    ? "bg-orange-500 text-white"
                    : "text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                )}
              >
                PBC 2021 (Clause 4.2.1)
              </button>
              <button
                onClick={() => {
                  setActivePdfDoc("dha_plan");
                  setHighlightClause(null);
                }}
                className={cn(
                  "px-2.5 py-1 rounded-md font-semibold transition-all",
                  activePdfDoc === "dha_plan"
                    ? "bg-orange-500 text-white"
                    : "text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
                )}
              >
                DHA Plaza Plan
              </button>
            </div>

            {/* Simulated PDF Viewer Sheet */}
            <div className="p-3 bg-slate-200/60 dark:bg-navy-950 flex justify-center overflow-x-auto min-h-[290px] max-h-[350px] overflow-y-auto">
              <div
                style={{ transform: `scale(${pdfZoom / 100})`, transformOrigin: "top center" }}
                className="w-full max-w-[340px] bg-white text-slate-900 p-3.5 shadow-md rounded-xs border border-slate-300 font-serif text-[10px] leading-relaxed select-text transition-transform duration-200"
              >
                {/* PDF Header Stamp */}
                <div className="border-b-2 border-slate-900 pb-1.5 mb-2.5 text-center">
                  <div className="text-[7.5px] font-sans font-bold tracking-widest uppercase text-slate-600">
                    GOVERNMENT OF PAKISTAN · MINISTRY OF HOUSING & WORKS
                  </div>
                  <div className="text-[10.5px] font-sans font-black tracking-tight mt-0.5 text-slate-900">
                    PAKISTAN BUILDING CODE (PBC 2021)
                  </div>
                  <div className="text-[7.5px] italic text-slate-500">
                    Part 4: Life Safety & Means of Egress Regulations
                  </div>
                </div>

                {/* Section Content */}
                <div className="space-y-2">
                  <div className="font-sans font-bold text-[8.5px] text-slate-800 uppercase tracking-wide">
                    CHAPTER 4 — STAIRWAYS & VERTICAL CIRCULATION
                  </div>

                  {/* HIGHLIGHTED CLAUSE */}
                  <div
                    className={cn(
                      "p-2 rounded-xs border transition-all",
                      highlightClause === "4.2.1"
                        ? "bg-amber-100 border-amber-400 ring-2 ring-amber-400/50 shadow-xs"
                        : "border-transparent"
                    )}
                  >
                    <div className="font-sans font-bold text-slate-900 flex items-center justify-between">
                      <span>SECTION 4.2.1: MINIMUM STAIRWAY WIDTH</span>
                      {highlightClause === "4.2.1" && (
                        <span className="text-[7.5px] font-sans font-black bg-amber-500 text-white px-1.5 py-0.2 rounded-xs">
                          CITED CLAUSE
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-slate-800 text-[9.5px]">
                      &quot;Stairways serving an occupant load of more than 50 persons shall not be less
                      than <strong className="underline decoration-amber-600 font-bold">48 inches (1,220 mm / 4.0 feet)</strong> in
                      clear width. In commercial, institutional, and high-density residential buildings, no
                      required stairway shall be constructed with a clear unobstructed width of less than
                      4.0 feet measured between finished handrails and edge reveals.&quot;
                    </p>
                  </div>

                  <div className="text-[9px] text-slate-700 pl-1 border-l-2 border-slate-300">
                    <span className="font-sans font-semibold">4.2.2 Handrail Projections:</span> Handrails may
                    project not more than 4.5 inches (114 mm) into required clear width at or below handrail
                    height.
                  </div>

                  <div className="text-[9px] text-slate-700 pl-1 border-l-2 border-slate-300">
                    <span className="font-sans font-semibold">4.2.3 Enclosed Emergency Stairs:</span> For
                    structures exceeding four (4) occupiable stories, dual pressurized smoke-proof stairwells
                    with self-closing 2-hour fire doors are compulsory.
                  </div>

                  <div className="pt-2 text-[8px] text-slate-400 font-sans flex justify-between border-t border-slate-200">
                    <span>PBC-2021-REG-04</span>
                    <span>Page 42</span>
                  </div>
                </div>
              </div>
            </div>

            {/* PDF Card Footer */}
            <div className="p-2 bg-white dark:bg-navy-900 border-t border-slate-200 dark:border-slate-800 text-[10px] text-slate-500 dark:text-slate-400 flex items-center justify-between">
              <span>{t("Clause highlighted by TameerAI RAG", "تعمیر اے آئی کی جانب سے ہائی لائٹ شدہ شق")}</span>
              <button
                onClick={() => setHighlightClause(highlightClause ? null : "4.2.1")}
                className="text-orange-500 hover:underline font-bold"
              >
                {highlightClause ? t("Clear Highlight", "نشان ہٹائیں") : t("Highlight Again", "دوبارہ نمایاں کریں")}
              </button>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}
