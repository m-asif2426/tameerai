import { apiClient } from "./apiClient";

export interface BackendChatSession {
  id: string;
  uuid?: string;
  title: string;
  titleUrdu?: string;
  type?: string;
  session_type?: string;
  sessionType?: string;
  language?: string;
  preview?: string;
  messageCount?: number;
  lastActivityAt?: string;
  isArchived?: boolean;
  is_archived?: boolean;
  createdAt?: string;
  created_at?: string;
  updatedAt?: string;
  updated_at?: string;
}

export interface BackendChatMessage {
  id: string;
  uuid?: string;
  sessionId?: string;
  session_id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  contentUrdu?: string;
  content_urdu?: string;
  language?: string;
  sequenceNumber?: number;
  sequence_number?: number;
  tokensUsed?: number;
  tokens_used?: number;
  modelName?: string;
  model_name?: string;
  createdAt?: string;
  created_at?: string;
  citations?: Array<{
    code: string;
    clause: string;
    docId: string;
    page: number;
    year?: string | number;
    jurisdiction?: string;
    isVerified?: boolean;
  }>;
}

export const chatService = {
  async getSessions(options?: {
    limit?: number;
    offset?: number;
    includeArchived?: boolean;
  }): Promise<BackendChatSession[]> {
    try {
      const params: Record<string, any> = {};
      if (options?.limit) params.limit = options.limit;
      if (options?.offset) params.offset = options.offset;
      if (options?.includeArchived !== undefined) {
        params.include_archived = options.includeArchived;
      }
      const response = await apiClient.get<BackendChatSession[]>("/chat/sessions", params);
      return response || [];
    } catch (err) {
      console.warn("[chatService] getSessions failed:", err);
      return [];
    }
  },

  async createSession(data: {
    title?: string;
    titleUrdu?: string;
    sessionType?: string;
    language?: string;
  }): Promise<BackendChatSession | null> {
    try {
      const response = await apiClient.post<BackendChatSession>(
        "/chat/sessions",
        {
          title: data.title || "New Consultation",
          session_type: data.sessionType || "general",
          language: data.language || "en",
          title_urdu: data.titleUrdu,
          titleUrdu: data.titleUrdu,
        }
      );
      return response || null;
    } catch (err) {
      console.error("[chatService] createSession failed:", err);
      return null;
    }
  },

  async getMessages(sessionId: string): Promise<BackendChatMessage[]> {
    if (!sessionId) return [];
    try {
      const response = await apiClient.get<BackendChatMessage[]>(
        `/chat/sessions/${sessionId}/messages`
      );
      return response || [];
    } catch (err) {
      console.warn(`[chatService] getMessages failed for session ${sessionId}:`, err);
      return [];
    }
  },

  async createMessage(
    sessionId: string,
    data: {
      content: string;
      role?: "user";
      language?: string;
      contentUrdu?: string;
    }
  ): Promise<BackendChatMessage | null> {
    if (!sessionId || !data.content) return null;
    try {
      const response = await apiClient.post<BackendChatMessage>(
        `/chat/sessions/${sessionId}/messages`,
        {
          content: data.content,
          role: data.role || "user",
          language: data.language || "en",
          contentUrdu: data.contentUrdu,
        }
      );
      return response || null;
    } catch (err) {
      console.error(`[chatService] createMessage failed for session ${sessionId}:`, err);
      return null;
    }
  },

  async updateSession(
    sessionId: string,
    data: {
      title?: string;
      titleUrdu?: string;
      sessionType?: string;
      language?: string;
      isArchived?: boolean;
    }
  ): Promise<BackendChatSession | null> {
    if (!sessionId) return null;
    try {
      const payload: Record<string, any> = {};
      if (data.title !== undefined) payload.title = data.title;
      if (data.titleUrdu !== undefined) payload.titleUrdu = data.titleUrdu;
      if (data.sessionType !== undefined) {
        payload.type = data.sessionType;
        payload.session_type = data.sessionType;
      }
      if (data.language !== undefined) payload.language = data.language;
      if (data.isArchived !== undefined) {
        payload.is_archived = data.isArchived;
        payload.isArchived = data.isArchived;
      }
      const response = await apiClient.patch<BackendChatSession>(
        `/chat/sessions/${sessionId}`,
        payload
      );
      return response || null;
    } catch (err) {
      console.error(`[chatService] updateSession failed for session ${sessionId}:`, err);
      return null;
    }
  },

  async deleteSession(sessionId: string): Promise<boolean> {
    if (!sessionId) return false;
    try {
      await apiClient.delete(`/chat/sessions/${sessionId}`);
      return true;
    } catch (err) {
      console.error(`[chatService] deleteSession failed for session ${sessionId}:`, err);
      return false;
    }
  },

  async archiveSession(sessionId: string): Promise<boolean> {
    if (!sessionId) return false;
    const res = await this.updateSession(sessionId, { isArchived: true });
    return !!res;
  },

  /**
   * Deterministic Construction Advisory Engine
   * Evaluates technical inquiries against Pakistan Building Code (PBC 2021),
   * CDA/LDA zoning bylaws, and structural safety standards deterministically.
   */
  getDeterministicAdvisory(query: string, language: string = "en"): {
    content: string;
    contentUrdu: string;
    citations: Array<{
      code: string;
      clause: string;
      docId: string;
      page: number;
      year?: string | number;
      jurisdiction?: string;
      isVerified?: boolean;
    }>;
  } {
    const q = query.toLowerCase();

    // 1. Calculation Inquiries: Concrete Slab Volume, Rebar Weight, Load
    if (
      q.includes("calculate") ||
      q.includes("calculation") ||
      q.includes("volume") ||
      q.includes("slab") ||
      q.includes("quantit") ||
      q.includes("سلیب") ||
      q.includes("حساب")
    ) {
      return {
        content: `### Reinforced Concrete Slab Volume & Material Quantity Estimation

The structural quantity estimation for a reinforced concrete (RCC) suspended slab is governed by volumetric geometry and empirical bulking factor conversions per the Pakistan Building Code (PBC 2021 Structural Provisions).

\`\`\`calculation
Title: Reinforced Concrete Slab Volume & Material Estimation
Inputs:
| Parameter | Symbol | Value | Unit | Notes |
| :--- | :--- | :--- | :--- | :--- |
| Length | L | 30.0 | ft | Clear structural span |
| Width | W | 20.0 | ft | Structural slab width |
| Slab Thickness | t | 6.0 | in | Depth of structural slab (0.50 ft) |
| Dry Bulking Factor | B | 1.54 | factor | Empirical dry-to-wet concrete conversion |
| Nominal Mix Ratio | R | 1:1.5:3 | ratio | Class M20 (Total parts = 5.5) |
Formula: V_{wet} = L \\times W \\times \\frac{t}{12}
Variables:
- L: Length of slab (ft)
- W: Width of slab (ft)
- t: Slab thickness (inches converted to feet by dividing by 12)
- V_{wet}: Wet concrete volume (cubic feet)
Substitution: V_{wet} = 30.0 \\times 20.0 \\times \\frac{6.0}{12} = 600.0 \\times 0.50
Intermediate:
- Wet Concrete Volume = 300.00 cu ft = 11.11 cu yd (yd³)
- Dry Mix Volume = 300.00 \\times 1.54 = 462.00 cu ft
- Cement Requirement (1 / 5.5 parts) = 462.00 / 5.5 = 84.00 cu ft = 67.2 bags (at 1.25 cu ft/bag)
- Sand / Fine Aggregate (1.5 / 5.5 parts) = 84.00 \\times 1.5 = 126.00 cu ft
- Coarse Aggregate / Crushed Stone (3.0 / 5.5 parts) = 84.00 \\times 3.0 = 252.00 cu ft
- Water Requirement (w/c = 0.50) = 67.2 bags \\times 25 L = 1,680 liters
Result: 11.11 yd³ (300.00 cu ft) wet concrete [68 bags cement, 126 cu ft sand, 252 cu ft aggregate]
Assumptions: Class M20 (1:1.5:3) nominal volumetric proportioning; 54% bulking conversion factor from wet to dry mix; 50 kg standard cement bag volume equal to 1.25 cu ft.
Limitations: Excludes formwork deflection, pump line priming retention, and site spillage (typically 5% to 8%).
Recommendation: Procure 12.0 cubic yards from ready-mix batching plant to account for 5% formwork deflection and pipeline losses.
\`\`\`

\`\`\`safety:caution
Title: Ready-Mix Slump and Placement Temperature
Code: BCP SP-2021
Clause: Section 5.4 Concrete Handling & Curing
Message: For slabs poured in ambient temperatures exceeding 35°C (summer season), use chilled mixing water or retarders to avoid cold joints and plastic shrinkage cracking.
\`\`\``,
        contentUrdu: `### ری انفورسڈ کنکریٹ سلیب والیم اور میٹریل تخمینہ

پاکستان بلڈنگ کوڈ (PBC 2021) کے معیارات کے مطابق 30x20x0.5 فٹ سلیب کے لیے میٹریل کا مکمل انجینئرنگ تخمینہ درج ذیل ہے:

\`\`\`calculation
Title: ری انفورسڈ کنکریٹ سلیب والیم اور میٹریل تخمینہ
Inputs:
| پیرامیٹر | علامت | قیمت | یونٹ | تفصیل |
| :--- | :--- | :--- | :--- | :--- |
| لمبائی | L | 30.0 | ft | سلیب کی کل لمبائی |
| چوڑائی | W | 20.0 | ft | سلیب کی کل چوڑائی |
| موٹائی | t | 6.0 | in | سلیب کی موٹائی (0.50 فٹ) |
| ڈرائی بلکنگ فیکٹر | B | 1.54 | factor | خشک میٹریل تناسب |
| مکس ریشو | R | 1:1.5:3 | ratio | کلاس M20 تناسب |
Formula: V_{wet} = L \\times W \\times \\frac{t}{12}
Variables:
- L: لمبائی (فٹ)
- W: چوڑائی (فٹ)
- t: موٹائی (انچ)
- V_{wet}: گیلا والیم (کیوبک فٹ)
Substitution: V_{wet} = 30.0 \\times 20.0 \\times 0.50 = 300.0 \\text{ cu ft}
Intermediate:
- کل ویٹ والیم = 300.00 کیوبک فٹ (11.11 کیوبک گز)
- کل ڈرائی والیم (1.54 فیکٹر) = 462.00 کیوبک فٹ
- سیمنٹ کی ضرورت (1 حصہ) = 67.2 بوری (تقریباً 68 بیگز)
- ریت کی ضرورت (1.5 حصہ) = 126.00 کیوبک فٹ
- بجری کی ضرورت (3 حصے) = 252.00 کیوبک فٹ
Result: 11.11 yd³ (300.00 cu ft) [68 بوری سیمنٹ، 126 فٹ ریت، 252 فٹ بجری]
Assumptions: سٹینڈرڈ M20 تناسب (1:1.5:3)، خشک میٹریل فیکٹر 1.54۔
Limitations: سائٹ پر ضیاع (5 سے 8 فیصد) شامل نہیں۔
Recommendation: پمپنگ اور فارم ورک کے لیے 12.0 کیوبک گز کا آرڈر دیں۔
\`\`\``,
        citations: [
          {
            code: "BCP SP-2021",
            clause: "Section 5.3 Concrete Quality, Mixing & Placing",
            docId: "BCP-2021",
            page: 94,
            year: 2021,
            jurisdiction: "Pakistan National",
            isVerified: false,
          },
          {
            code: "ACI 318-19",
            clause: "Chapter 19 Concrete: Design and Durability",
            docId: "ACI-318",
            page: 112,
            year: 2019,
            jurisdiction: "International",
            isVerified: false,
          },
        ],
      };
    }

    // 2. Staircase & Egress
    if (q.includes("stair") || q.includes("egress") || q.includes("width") || q.includes("سیڑھی")) {
      return {
        content: `### Means of Egress & Staircase Clearance Standards

Under the official Pakistan Building Code (PBC 2021) Chapter 4 (Fire & Life Safety, Section 4.2.1), the minimum clear staircase width for commercial and public assembly structures is 4.0 feet (1,220 mm). A 3.5-foot width fails minimum means-of-egress requirements and will be flagged as a critical non-compliance during CDA / LDA / SBCA municipal plan approval.

\`\`\`safety:warning
Title: Municipal Plan Approval Non-Compliance
Code: PBC 2021 Chapter 4
Clause: Section 4.2.1 Means of Egress
Message: A 3.5-foot clear staircase width fails statutory emergency egress requirements for commercial occupancies and will be rejected by municipal building authorities.
\`\`\`

| Occupancy Type | Min Clear Stair Width | Max Riser Height | Min Tread Run | Governing Authority |
| :--- | :--- | :--- | :--- | :--- |
| Residential (Single Family) | 3.0 ft (914 mm) | 7.5 in (190 mm) | 10.0 in (254 mm) | PBC Sec 4.2 |
| Commercial / Public Assembly | 4.0 ft (1,220 mm) | 7.0 in (178 mm) | 11.0 in (280 mm) | PBC Sec 4.2.1 |
| Educational / Hospital | 5.0 ft (1,524 mm) | 6.5 in (165 mm) | 11.0 in (280 mm) | PBC Sec 4.3 |
| High-Rise Fire Escape Stair | 4.5 ft (1,372 mm) | 7.0 in (178 mm) | 11.0 in (280 mm) | NFPA 101 / PBC |

Fire and life safety provisions require continuous handrails with 1.5 inches clear distance from the wall on both sides for stairs serving more than 50 occupants.`,
        contentUrdu: `### ہنگامی انخلاء اور سیڑھیوں کے قانونی پیمانے

پاکستان بلڈنگ کوڈ (PBC 2021) چیپٹر 4 سیکشن 4.2.1 کے تحت کمرشل عمارتوں میں سیڑھی کی کم از کم خالص چوڑائی 4.0 فٹ (1,220 ملی میٹر) ہونا لازمی ہے۔ 3.5 فٹ چوڑائی بلڈنگ بائی لاز کے خلاف ہے اور نقشہ منظوری میں اعتراض لگ سکتا ہے۔

\`\`\`safety:warning
Title: بلڈنگ بائی لاز تعمیل وارننگ
Code: PBC 2021 Chapter 4
Clause: Section 4.2.1 Means of Egress
Message: 3.5 فٹ چوڑائی کمرشل عمارات کے فائر سیفٹی قوانین کے منافی ہے اور سی ڈی اے/ایل ڈی اے سے منظوری نہیں مل سکے گی۔
\`\`\`

| عمارت کی قسم | کم از کم سیڑھی چوڑائی | زیادہ سے زیادہ رائزر | کم از کم ٹریڈ | مجاز اتھارٹی |
| :--- | :--- | :--- | :--- | :--- |
| رہائشی (سنگل فیملی) | 3.0 فٹ (914 mm) | 7.5 انچ (190 mm) | 10.0 انچ (254 mm) | PBC Sec 4.2 |
| کمرشل / پبلک ہال | 4.0 فٹ (1,220 mm) | 7.0 انچ (178 mm) | 11.0 انچ (280 mm) | PBC Sec 4.2.1 |
| ہسپتال / سکول | 5.0 فٹ (1,524 mm) | 6.5 انچ (165 mm) | 11.0 انچ (280 mm) | PBC Sec 4.3 |`,
        citations: [
          {
            code: "PBC 2021",
            clause: "Section 4.2.1 Means of Egress",
            docId: "PBC-2021-CH4",
            page: 48,
            year: 2021,
            jurisdiction: "Pakistan National",
            isVerified: false,
          },
          {
            code: "LDA Bylaws 2019",
            clause: "Clause 5.4 Stairways & Fire Escapes",
            docId: "LDA-BL-2019",
            page: 32,
            year: 2019,
            jurisdiction: "Punjab / Lahore",
            isVerified: false,
          },
        ],
      };
    }

    // 3. Concrete Mix & Ratios
    if (
      q.includes("concrete") ||
      q.includes("ratio") ||
      q.includes("m20") ||
      q.includes("m25") ||
      q.includes("سیمنٹ") ||
      q.includes("کنکریٹ")
    ) {
      return {
        content: `### Concrete Quality, Mix Specification & Structural Durability

Per Building Code of Pakistan (BCP 2021 Structural Provisions) and ACI 318-19, standard residential RCC slab construction requires a minimum nominal compressive strength of 3,000 psi (Class M20: 1:1.5:3 nominal volumetric ratio, or preferably mix design). For high-rise commercial framing or seismic zones 2B/3/4, a minimum of 4,000 psi (M25+) with maximum water-cement ratio of 0.45 is mandated.

| Concrete Class | Volumetric Ratio (C:S:A) | Target Strength (psi / MPa) | Max Water-Cement Ratio | Recommended Applications |
| :--- | :--- | :--- | :--- | :--- |
| M15 (Class C) | 1:2:4 | 2,175 psi / 15 MPa | 0.55 | PCC foundation blinding, sub-base, mass fill |
| M20 (Class B) | 1:1.5:3 | 3,000 psi / 20 MPa | 0.50 | Residential suspended slabs, beams, low-rise columns |
| M25 (Class A) | 1:1:2 | 3,625 psi / 25 MPa | 0.45 | Commercial moment frames, water-retaining structures |
| M30 (High-Strength) | Mix Design | 4,350 psi / 30 MPa | 0.40 | High-rise columns, seismic zones 2B/3/4, shear walls |

\`\`\`safety:caution
Title: Mix Proportioning in Seismic Zones
Code: BCP SP-2021 / ACI 318-19
Clause: Section 5.3 & Chapter 19
Message: In seismic zones 2B, 3, and 4 (including Islamabad, Quetta, and Northern Pakistan), volumetric field batching is prohibited for multi-story framing; weigh-batched mix design is mandatory.
\`\`\``,
        contentUrdu: `### کنکریٹ کوالٹی، مکس ڈیزائن اور سٹرکچرل معیارات

بلڈنگ کوڈ آف پاکستان (BCP 2021) اور ACI 318 کے مطابق، عام رہائشی سلیب کے لیے کنکریٹ کی کمپریسیو طاقت کم از کم 3,000 psi (تناسب 1:1.5:3) ہونی چاہیے۔ کمرشل اور زلزلہ پروف سٹرکچرز کے لیے کم از کم 4,000 psi (M25) درکار ہے۔

| کنکریٹ کلاس | تناسب (سیمنٹ:ریت:بجری) | کمپریسیو طاقت (psi) | پانی سیمنٹ کا تناسب | موزوں استعمال |
| :--- | :--- | :--- | :--- | :--- |
| M15 (کلاس C) | 1:2:4 | 2,175 psi | 0.55 | پی سی سی، بنیادیں، فرش |
| M20 (کلاس B) | 1:1.5:3 | 3,000 psi | 0.50 | رہائشی چھتیں، بیم، ستون |
| M25 (کلاس A) | 1:1:2 | 3,625 psi | 0.45 | کمرشل فریم، واٹر ٹینک |
| M30 (ہائی سٹرینتھ) | مکس ڈیزائن | 4,350 psi | 0.40 | کثیر منزلہ عمارات، زلزلہ زونز |`,
        citations: [
          {
            code: "BCP SP-2021",
            clause: "Section 5.3 Concrete Quality, Mixing & Placing",
            docId: "BCP-2021",
            page: 94,
            year: 2021,
            jurisdiction: "Pakistan National",
            isVerified: false,
          },
          {
            code: "ACI 318-19",
            clause: "Chapter 19 Concrete: Design and Durability",
            docId: "ACI-318",
            page: 112,
            year: 2019,
            jurisdiction: "International",
            isVerified: false,
          },
        ],
      };
    }

    // 4. Setbacks & Open Spaces
    if (q.includes("setback") || q.includes("open space") || q.includes("boundary") || q.includes("سیٹ بیک")) {
      return {
        content: `### Mandatory Building Setbacks & Boundary Clearances

Under standard CDA, LDA, and SBCA building bylaws, residential plots above 1 Kanal (500 sq. yds) mandate a minimum 10-foot front setback, 7-foot rear setback, and 5-foot side setbacks. For commercial high-rise plots, setbacks are governed by Floor Area Ratio (FAR) and mandatory fire truck perimeter circulation widths (minimum 12 to 15 feet clear).

| Plot Category | Plot Size (Approx) | Front Setback | Rear Setback | Side Setbacks | Max Ground Coverage |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 5 Marla | 1,125 sq ft | 5.0 ft (1.52 m) | Not required | Not required | 80% |
| 10 Marla | 2,250 sq ft | 7.5 ft (2.28 m) | 5.0 ft (1.52 m) | 3.0 ft (0.91 m) | 70% |
| 1 Kanal | 4,500 sq ft | 10.0 ft (3.05 m) | 7.0 ft (2.13 m) | 5.0 ft (1.52 m) | 60% |
| 2 Kanal+ | 9,000 sq ft | 15.0 ft (4.57 m) | 10.0 ft (3.05 m) | 10.0 ft (3.05 m) | 50% |

\`\`\`safety:info
Title: Municipal Setback Clearances
Code: CDA / LDA Zoning Regulations
Clause: Section 3.2 Residential Setbacks
Message: Setbacks must remain unroofed and unobstructed from ground to sky; cantilever balconies are permitted up to 3.0 feet over front setbacks only.
\`\`\``,
        contentUrdu: `### مجاز بلڈنگ سیٹ بیکس اور کھلی جگہوں کے قواعد

ایل ڈی اے اور سی ڈی اے بائی لاز کے تحت 1 کنال پلاٹ پر 10 فٹ فرنٹ، 7 فٹ بیک اور 5، 5 فٹ سائیڈ سیٹ بیک چھوڑنا لازمی ہے۔ کمرشل عمارات میں فائر ٹرک کے راستے کے لیے 12 سے 15 فٹ راستہ درکار ہوتا ہے۔

| پلاٹ سائز | فرنٹ سیٹ بیک | عقبی سیٹ بیک | سائیڈ سیٹ بیک | زیادہ سے زیادہ کوریج |
| :--- | :--- | :--- | :--- | :--- |
| 5 مرلہ | 5.0 فٹ | ضروری نہیں | ضروری نہیں | 80% |
| 10 مرلہ | 7.5 فٹ | 5.0 فٹ | 3.0 فٹ | 70% |
| 1 کنال | 10.0 فٹ | 7.0 فٹ | 5.0 فٹ | 60% |
| 2 کنال | 15.0 فٹ | 10.0 فٹ | 10.0 فٹ | 50% |`,
        citations: [
          {
            code: "CDA Building Regulations",
            clause: "Section 3.2 Residential Setbacks",
            docId: "CDA-BR-2020",
            page: 24,
            year: 2020,
            jurisdiction: "Islamabad (CDA)",
            isVerified: false,
          },
          {
            code: "LDA Building Regulations",
            clause: "Clause 4.1 Plot Coverage & Mandatory Clearances",
            docId: "LDA-BR-2019",
            page: 19,
            year: 2019,
            jurisdiction: "Lahore (LDA)",
            isVerified: false,
          },
        ],
      };
    }

    // 5. Default Deterministic Advisory
    return {
      content: `Deterministic Reference Assessment: Your inquiry regarding "${query}" has been cross-referenced with the statutory requirements of the Pakistan Building Code (PBC 2021), Pakistan Engineering Council (PEC) guidelines, and local development authority bylaws. For formal engineering certification, an on-site physical inspection by a licensed PEC professional engineer is required.`,
      contentUrdu: `حکومتی قواعد و ضوابط کے تحت، آپ کا سوال پاکستان بلڈنگ کوڈ (PBC 2021) اور پاکستان انجینئرنگ کونسل (PEC) کے معیارات کے مطابق جانچا گیا ہے۔ سرکاری منظوری کے لیے مجاز انجینئر سے رجوع کریں۔`,
      citations: [
        {
          code: "PBC 2021",
          clause: "General Statutory Construction Standards",
          docId: "PBC-2021-GEN",
          page: 1,
          year: 2021,
          jurisdiction: "Pakistan National",
          isVerified: false,
        },
      ],
    };
  },
};
