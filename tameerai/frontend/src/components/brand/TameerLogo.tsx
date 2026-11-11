import React from "react";

interface TameerLogoProps {
  variant?: "full" | "icon" | "favicon";
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
  theme?: "auto" | "light" | "dark";
  showTagline?: boolean;
}

const sizeMap = {
  xs: { icon: 20, text: "text-sm", tagline: "text-[9px]" },
  sm: { icon: 28, text: "text-base", tagline: "text-[10px]" },
  md: { icon: 36, text: "text-xl", tagline: "text-xs" },
  lg: { icon: 48, text: "text-2xl", tagline: "text-sm" },
  xl: { icon: 64, text: "text-3xl", tagline: "text-base" },
};

/**
 * TameerAI Geometric Architectural Mark
 * Engineered vector geometry representing:
 * 1. Heavy structural foundation I-beam (Physical Construction)
 * 2. Precision twin load-bearing columns (Structural Stability)
 * 3. 45° engineering truss cross-bracing (Lateral Load Resistance)
 * 4. Architectural keystone apex (Statutory Safety & Compliance)
 */
export function TameerIcon({
  size = 36,
  className = "",
}: {
  size?: number;
  className?: string;
  glow?: boolean;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="TameerAI Architectural Mark"
    >
      <defs>
        <linearGradient id="tameer-beam-orange" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FB923C" />
          <stop offset="100%" stopColor="#EA580C" />
        </linearGradient>
        <linearGradient id="tameer-steel-emerald" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#22C55E" />
          <stop offset="100%" stopColor="#15803D" />
        </linearGradient>
      </defs>

      {/* Blueprint Drafting Grid (Subtle Technical Gridlines) */}
      <path
        d="M18 20 H82 M18 40 H82 M18 60 H82 M18 80 H82"
        stroke="#94A3B8"
        strokeOpacity="0.22"
        strokeWidth="0.75"
        strokeDasharray="2 3"
      />
      <path
        d="M24 16 V84 M50 16 V84 M76 16 V84"
        stroke="#94A3B8"
        strokeOpacity="0.22"
        strokeWidth="0.75"
        strokeDasharray="2 3"
      />

      {/* Heavy Structural Foundation Beam (Base) */}
      <rect
        x="12"
        y="80"
        width="76"
        height="6"
        rx="2"
        fill="url(#tameer-beam-orange)"
      />

      {/* Structural Steel Cross-Bracing (Lateral Truss Geometry) */}
      <path
        d="M28 44 L72 76 M72 44 L28 76"
        stroke="url(#tameer-steel-emerald)"
        strokeWidth="3.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Load-Bearing Structural Columns (Twin Towers) */}
      <rect
        x="20"
        y="36"
        width="11"
        height="44"
        rx="2"
        fill="url(#tameer-beam-orange)"
      />
      <rect
        x="69"
        y="36"
        width="11"
        height="44"
        rx="2"
        fill="url(#tameer-beam-orange)"
      />

      {/* Central Architectural Spire & Cantilever Truss */}
      <path
        d="M50 16 L63 28 V80 H55 V33 L50 27 L45 33 V80 H37 V28 L50 16 Z"
        fill="#EA580C"
      />

      {/* Keystone Apex Diamond (Engineering Precision & Statutory Compliance) */}
      <polygon
        points="50,8 57,16 50,24 43,16"
        fill="#16A34A"
      />
      <circle cx="50" cy="16" r="2" fill="#FFFFFF" />
    </svg>
  );
}

/**
 * TameerAI Micro Favicon (Optimized for 16x16, 32x32, 48x48)
 */
export function TameerFavicon({ size = 32 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="TameerAI Favicon"
    >
      <rect width="64" height="64" rx="14" fill="#0F172A" />
      {/* Structural Tower */}
      <path
        d="M32 10 L46 22 V50 H38 V28 L32 23 L26 28 V50 H18 V22 L32 10 Z"
        fill="#F97316"
      />
      {/* Cross-Brace */}
      <path d="M22 32 L42 46 M42 32 L22 46" stroke="#22C55E" strokeWidth="2.5" strokeLinecap="round" />
      {/* Foundation Base */}
      <rect x="12" y="50" width="40" height="4" rx="2" fill="#EA580C" />
      {/* Apex Keystone */}
      <polygon points="32,6 36,11 32,16 28,11" fill="#16A34A" />
    </svg>
  );
}

/**
 * Main TameerAI Master Logo Component
 */
export default function TameerLogo({
  variant = "full",
  size = "md",
  className = "",
  theme = "auto",
  showTagline = false,
}: TameerLogoProps) {
  const currentSize = sizeMap[size];

  if (variant === "favicon") {
    return <TameerFavicon size={currentSize.icon} />;
  }

  if (variant === "icon") {
    return (
      <div className={`inline-flex items-center justify-center ${className}`}>
        <TameerIcon size={currentSize.icon} />
      </div>
    );
  }

  const textColor =
    theme === "dark"
      ? "text-white"
      : theme === "light"
      ? "text-slate-900"
      : "text-slate-900 dark:text-white";

  const taglineColor =
    theme === "dark"
      ? "text-slate-400"
      : theme === "light"
      ? "text-slate-500"
      : "text-slate-500 dark:text-slate-400";

  return (
    <div className={`inline-flex items-center gap-2.5 ${className}`}>
      {/* Icon Mark */}
      <div className="flex-shrink-0 transition-transform duration-200 hover:scale-105">
        <TameerIcon size={currentSize.icon} />
      </div>

      {/* Wordmark */}
      <div className="flex flex-col leading-none">
        <div className="flex items-center">
          <span className={`font-bold tracking-tight ${currentSize.text} ${textColor}`}>
            Tameer
          </span>
          <span className={`font-black tracking-tight ${currentSize.text} text-orange-500 ml-[1px]`}>
            AI
          </span>
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-500 ml-1.5 self-center" />
        </div>

        {showTagline && (
          <span
            className={`font-medium tracking-[0.18em] uppercase ${currentSize.tagline} ${taglineColor} mt-1`}
          >
            Construction Intelligence
          </span>
        )}
      </div>
    </div>
  );
}
