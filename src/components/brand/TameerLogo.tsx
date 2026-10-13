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
 * TameerAI Modern SVG Icon Mark
 * Represents:
 * 1. Isometric architectural high-rise beam structure (Construction / Engineering)
 * 2. Blueprint technical gridlines (Precision & Architecture)
 * 3. Interconnected neural network nodes (Artificial Intelligence)
 * 4. Grounded foundation & safety shield archetype (Trust & Safety)
 */
export function TameerIcon({
  size = 36,
  className = "",
  glow = true,
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
      aria-label="TameerAI Mark"
    >
      <defs>
        {/* Gradients */}
        <linearGradient id="tameer-orange-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FB923C" />
          <stop offset="100%" stopColor="#EA580C" />
        </linearGradient>

        <linearGradient id="tameer-green-grad" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#15803D" />
          <stop offset="50%" stopColor="#22C55E" />
          <stop offset="100%" stopColor="#4ADE80" />
        </linearGradient>

        <linearGradient id="tameer-navy-grad" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#1E293B" />
          <stop offset="100%" stopColor="#0F172A" />
        </linearGradient>

        <filter id="neural-glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="2.5" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {/* Blueprint Grid Lines (Subtle Precision Backdrop) */}
      <path
        d="M20 20 H80 M20 40 H80 M20 60 H80 M20 80 H80"
        stroke="#94A3B8"
        strokeOpacity="0.18"
        strokeWidth="0.8"
        strokeDasharray="2 2"
      />
      <path
        d="M25 15 V85 M50 15 V85 M75 15 V85"
        stroke="#94A3B8"
        strokeOpacity="0.18"
        strokeWidth="0.8"
        strokeDasharray="2 2"
      />

      {/* Structural Foundation Beam (Base) */}
      <rect
        x="14"
        y="83"
        width="72"
        height="4.5"
        rx="2.25"
        fill="url(#tameer-orange-grad)"
      />

      {/* AI Neural Constellation Behind Beams */}
      <g opacity="0.9" filter={glow ? "url(#neural-glow)" : undefined}>
        {/* Network Synapse Lines */}
        <path
          d="M32 64 L50 48 L68 64 M50 26 L50 48 M32 64 L50 74 L68 64 M24 48 L32 64 M76 48 L68 64 M32 38 L50 26 L68 38"
          stroke="url(#tameer-green-grad)"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeOpacity="0.85"
        />

        {/* Neural Nodes */}
        <circle cx="50" cy="26" r="3.2" fill="#4ADE80" />
        <circle cx="50" cy="48" r="3.6" fill="#22C55E" />
        <circle cx="50" cy="74" r="2.8" fill="#4ADE80" />
        <circle cx="32" cy="64" r="3" fill="#22C55E" />
        <circle cx="68" cy="64" r="3" fill="#22C55E" />
        <circle cx="24" cy="48" r="2.4" fill="#4ADE80" />
        <circle cx="76" cy="48" r="2.4" fill="#4ADE80" />
        <circle cx="32" cy="38" r="2.2" fill="#86EFAC" />
        <circle cx="68" cy="38" r="2.2" fill="#86EFAC" />
      </g>

      {/* Architectural High-Rise Cantilever Beams (Construction Structure) */}
      {/* Central Spire Arch */}
      <path
        d="M50 16 L65 28 V83 H57 V33 L50 27 L43 33 V83 H35 V28 L50 16 Z"
        fill="url(#tameer-orange-grad)"
      />

      {/* Left Tower Pillar */}
      <path
        d="M26 40 L35 34 V83 H26 V40 Z"
        fill="url(#tameer-orange-grad)"
        fillOpacity="0.95"
      />

      {/* Right Tower Pillar */}
      <path
        d="M74 40 L65 34 V83 H74 V40 Z"
        fill="url(#tameer-orange-grad)"
        fillOpacity="0.95"
      />

      {/* Safety Keystone Diamond (Apex of Precision) */}
      <polygon
        points="50,11 54,16 50,21 46,16"
        fill="#22C55E"
      />
    </svg>
  );
}

/**
 * TameerAI Micro Favicon (Optimized for 16x16, 32x32, 48x48)
 * Bold, high-contrast, instantly recognizable at tiny scales.
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

      {/* Outer Glow Grid */}
      <rect x="8" y="8" width="48" height="48" rx="8" stroke="#334155" strokeWidth="1" strokeDasharray="3 3" />

      {/* Simplified Structural Tower (Orange) */}
      <path
        d="M32 12 L46 23 V52 H38 V30 L32 25 L26 30 V52 H18 V23 L32 12 Z"
        fill="#F97316"
      />

      {/* Green AI Core Node */}
      <circle cx="32" cy="38" r="4.5" fill="#22C55E" />
      <path d="M32 26 V33 M24 45 L29 40 M40 45 L35 40" stroke="#4ADE80" strokeWidth="2" strokeLinecap="round" />

      {/* Foundation Base */}
      <rect x="14" y="52" width="36" height="3" rx="1.5" fill="#F97316" />
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
