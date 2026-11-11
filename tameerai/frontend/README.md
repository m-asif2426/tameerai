# 🏗️ TameerAI (تعمیر اے آئی)

> **Pakistan's AI Construction Compliance, FIDIC Contract Analyzer & Cost Intelligence Platform**  
> *پاکستان کی پہلی مصنوعی ذہانت پر مبنی عمارت سازی، قانونی معاہدات اور لاگت انٹیلی جنس سسٹم*

![TameerAI Platform](https://img.shields.io/badge/Next.js-14.2-black?style=for-the-badge&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?style=for-the-badge&logo=typescript)
![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4-38B2AC?style=for-the-badge&logo=tailwind-css)
![Standards](https://img.shields.io/badge/Standard-PBC_2021_%7C_FIDIC-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-Proprietary-red?style=for-the-badge)

---

## 📌 Overview (تعارف)

**TameerAI** is an enterprise-grade AI software designed for Pakistani civil engineers, architectural firms, and construction contractors (*Thekedars*). Grounded in the statutory regulations of the **Pakistan Building Code (PBC 2021)**, **Lahore Development Authority (LDA 2020)** by-laws, and **FIDIC Red Book / Subcontract** standards, TameerAI eliminates municipal plan rejections, detects catastrophic legal contract clauses, and hedges against volatile commodity price fluctuations (Grade-60 Rebar, OPC Cement, Red Bricks).

---

## 🌟 Key Capabilities (بنیادی خصوصیات)

- **🏛️ Pakistan Building Code (PBC 2021) Compliance Engine:** Automatic architectural and CAD plan auditing with percentage compliance score (e.g. 92%), highlighting passed items, warnings, and violations (e.g. Staircase egress width 3.5 ft vs. 4.0 ft required under PBC Section 4.2.1).
- **⚖️ FIDIC Contract & Legal Risk Analyzer:** In-depth clause-by-clause audit scoring contracts (e.g. 8/10 Risk Score), detecting uncapped liquidated damages, prolonged 90-day payment cycles, and unilateral termination liabilities with side-by-side synchronized PDF viewer.
- **📈 Real-Time Cost Intelligence & Inflation Radar:** Dynamic project budget tracking (PKR 120M vs. PKR 128.45M), material price trends (Steel, Cement, Bricks) in Lahore and Karachi, and Recharts interactive comparison graphs.
- **🤖 Construction AI Assistant (ChatGPT & Perplexity Style):** 3-pane interface with chat history, instant code violation warning cards, quick prompts, live material rates, and source document citations.
- **📁 Autodesk-Inspired Project Workspaces:** Complete multi-tab project control center (`/dashboard/projects/[id]`) with 7 modules: *Overview, AI Chat, Documents, Compliance, Contract, Cost, and Reports*.
- **📑 Executive Consulting Reports Management:** Client-ready engineering dossiers styled after international consulting firms (Arup, Turner & Townsend), featuring formal letterheads, PEC engineering sign-offs, PBC 2021 stamps, interactive PDF modal previews, and PDF export.
- **⚙️ Full SaaS Settings Portal:** Dedicated configuration for Profile (Aslam Bhai / PEC registration), Instant Bilingual Switcher (English / Urdu RTL), Light & Dark Themes, 2-Factor Authentication (2FA), Active Devices, and AI Audit Strictness Parameters.

---

## 📂 Complete Source Directory Structure (`src/`)

```text
src/
├── app/                                       # Next.js 14 App Router
│   ├── favicon.ico                            # TameerAI Brand Favicon
│   ├── globals.css                            # Global styles, variables & Tailwind directives
│   ├── layout.tsx                             # Root layout (Theme & Language providers)
│   ├── page.tsx                               # Public landing page (Hero, Features, Rates)
│   │
│   ├── login/                                 # Authentication: Login
│   │   └── page.tsx                           # Split-screen AI SaaS login page
│   │
│   ├── signup/                                # Authentication: Register
│   │   └── page.tsx                           # Split-screen account registration page
│   │
│   └── dashboard/                             # SaaS Application Portal
│       ├── layout.tsx                         # SaaS layout shell (Collapsible Sidebar & Topbar)
│       ├── page.tsx                           # Main Dashboard (Welcome, Quick Actions, Stats)
│       │
│       ├── ai-assistant/                      # AI Interaction Console
│       │   └── page.tsx                       # 3-Pane ChatGPT/Perplexity AI Assistant
│       │
│       ├── audit/                             # Audit Setup Wizard
│       │   └── page.tsx                       # 3-Step New Construction Audit Wizard
│       │
│       ├── compliance/                        # Building Code Inspector
│       │   └── page.tsx                       # PBC 2021 Compliance check with CAD blueprint viewer
│       │
│       ├── contracts/                         # Legal Agreement Analyzer
│       │   └── page.tsx                       # FIDIC Contract analyzer with 8/10 risk radar & PDF viewer
│       │
│       ├── costs/                             # Financial Intelligence
│       │   └── page.tsx                       # Project budget comparison & material price trends
│       │
│       ├── projects/                          # Project Management
│       │   ├── page.tsx                       # Project cards list (Filter, Search, Create modal)
│       │   └── [id]/                          # Project Workspace
│       │       └── page.tsx                   # 7-Tab Autodesk-style project workspace
│       │
│       ├── reports/                           # Executive Technical Dossiers
│       │   └── page.tsx                       # Reports Management (Compliance, Contract, Cost)
│       │
│       └── settings/                          # SaaS Configuration
│           └── page.tsx                       # Settings (Profile, Language, Theme, 2FA, AI rules)
│
├── components/                                # Reusable UI Components
│   ├── auth/
│   │   └── AuthSplitScreen.tsx                # Reusable split-screen layout for Auth pages
│   │
│   ├── brand/
│   │   └── TameerLogo.tsx                     # Official TameerAI SVG logo & brand icon
│   │
│   └── landing/                               # Landing Page Section Components
│       ├── FeaturesSection.tsx                # Enterprise feature showcase grid
│       ├── Footer.tsx                         # Regulatory links, contact info & copyright
│       ├── HeroSection.tsx                    # Value proposition, live CTAs & badges
│       ├── HowItWorksSection.tsx              # 3-Step workflow illustration
│       ├── MaterialRatesSection.tsx           # Daily Pakistani commodity price ticker
│       ├── Navbar.tsx                         # Navigation bar with Language & Theme toggles
│       ├── ProblemSection.tsx                 # Cost of non-compliance in Pakistan
│       └── StorySection.tsx                   # Case study component
│
├── contexts/
│   └── LanguageContext.tsx                    # English & Urdu bilingual state with RTL flipping
│
└── lib/
    └── utils.ts                               # Class merging helper (clsx + tailwind-merge)
```

---

## 🗺️ Application Routes Map (روٹس اور صفحات)

| Route | Purpose | Key Features |
|---|---|---|
| `/` | **Public Landing Page** | Enterprise Hero, live commodity rates, regulatory badges, how it works. |
| `/login` | **Sign In** | Split-screen layout, AI image showcase, Google Auth, language & theme switcher. |
| `/signup` | **Create Account** | Split-screen registration with PEC credentials and firm details. |
| `/dashboard` | **Main Hub** | "Welcome back Aslam Bhai", 4 KPI metrics, quick actions, active project cards. |
| `/dashboard/projects` | **Projects Directory** | Search, sort, filters, risk indicators, "+ Create New Project" modal. |
| `/dashboard/projects/PRJ-001` | **Project Workspace** | 7 Tabs: Overview, AI Chat, Documents, Compliance, Contract, Cost, Reports. |
| `/dashboard/ai-assistant` | **AI Assistant** | 3-Section layout, Staircase width PBC 2021 warning card, PDF groundings. |
| `/dashboard/audit` | **New Audit Wizard** | 3-Step workflow: Project Info → File Upload → Analysis Selection → Live Simulation. |
| `/dashboard/compliance` | **Code Compliance** | 92% Compliance score, Passed/Warnings/Violations, CAD blueprint viewer. |
| `/dashboard/contracts` | **FIDIC Contract Analyzer** | 8/10 Risk score, 3 Risk cards (Delay, Payment, Termination), synchronized PDF viewer. |
| `/dashboard/costs` | **Cost Intelligence** | Budget comparison (PKR 120M vs 128.45M), Steel/Cement/Brick cards, Recharts. |
| `/dashboard/reports` | **Reports Management** | Compliance, Contract, and Cost reports with Preview modal & Download PDF. |
| `/dashboard/settings` | **Settings Portal** | Profile, Language (EN/UR), Theme (Light/Dark), Notifications, 2FA, AI Rules. |

---

## 🛠️ Technology Stack

- **Framework:** [Next.js 14](https://nextjs.org/) (App Router, Server & Client Components)
- **Language:** [TypeScript](https://www.typescriptlang.org/) (Strict type-checking)
- **Styling:** [Tailwind CSS 3.4](https://tailwindcss.com/) + CSS variables
- **Icons:** [Lucide React](https://lucide.dev/)
- **Charts:** [Recharts 3.10](https://recharts.org/)
- **Theming:** [next-themes](https://github.com/pacocoursey/next-themes) (Seamless Light / Dark Mode)
- **UI Primitives:** Radix UI components (Dialog, Tabs, Avatar, Progress, Tooltip, Switch)
- **State & Localization:** Custom `LanguageContext` supporting English and Urdu with automatic RTL document direction switching.

---

## 💻 Getting Started (پروجیکٹ چلانے کا طریقہ)

### 1. Prerequisites
- Node.js (v18.17.0 or higher recommended)
- npm or yarn

### 2. Installation
```bash
# Clone or navigate to the project directory
cd "d:\new idea project\tameerai-landing"

# Install dependencies
npm install
```

### 3. Run Development Server
```bash
# Run Next.js on Port 3001
npm run dev -- -p 3001
```

### 4. Open in Browser
Open your browser and navigate to:
```text
http://localhost:3001
```

Or open directly from Windows PowerShell / Terminal:
```powershell
start http://localhost:3001
```

---

## 🔮 Future Roadmap (آئندہ کے اقدامات)

- [ ] **Real LLM Integration:** Connect Google Gemini 1.5 Pro API for live document chat, CAD drawing recognition, and automated contract redaction.
- [ ] **Cloud Backend & Database:** Integrate Supabase or Firebase for user authentication, persistent project databases, and encrypted PDF storage.
- [ ] **Server-side PDF Generation:** Integrate `@react-pdf/renderer` or Puppeteer for pixel-perfect official engineering dossiers with QR-code cryptographic verification.
- [ ] **Live Market Webhooks:** Connect Karachi and Lahore local steel mills and cement distributors for automated 24-hour rate updates.

---

### 🏛️ Developed with precision for Pakistan's Construction Industry
**TameerAI Engineering Intelligence** — Empowering builders, securing contracts, and ensuring compliance.
