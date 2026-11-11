"use client";

import React from "react";
import { cn } from "@/lib/utils";

interface FormulaBlockProps {
  formula: string;
  inline?: boolean;
  className?: string;
  caption?: string;
}

/**
 * Greek letters dictionary for mathematical rendering
 */
const GREEK_MAP: Record<string, string> = {
  "\\alpha": "α",
  "\\beta": "β",
  "\\gamma": "γ",
  "\\delta": "δ",
  "\\Delta": "Δ",
  "\\epsilon": "ε",
  "\\zeta": "ζ",
  "\\eta": "η",
  "\\theta": "θ",
  "\\iota": "ι",
  "\\kappa": "κ",
  "\\lambda": "λ",
  "\\Lambda": "Λ",
  "\\mu": "μ",
  "\\nu": "ν",
  "\\xi": "ξ",
  "\\pi": "π",
  "\\rho": "ρ",
  "\\sigma": "σ",
  "\\Sigma": "Σ",
  "\\tau": "τ",
  "\\phi": "φ",
  "\\chi": "χ",
  "\\psi": "ψ",
  "\\omega": "ω",
  "\\Omega": "Ω",
};

/**
 * Common math operators dictionary
 */
const SYMBOL_MAP: Record<string, string> = {
  "\\times": " × ",
  "\\cdot": " · ",
  "\\pm": " ± ",
  "\\approx": " ≈ ",
  "\\le": " ≤ ",
  "\\ge": " ≥ ",
  "\\neq": " ≠ ",
  "\\infty": " ∞ ",
  "\\rightarrow": " → ",
  "\\leftarrow": " ← ",
  "\\partial": " ∂ ",
  "\\sum": " ∑ ",
  "\\int": " ∫ ",
};

/**
 * Cleanly renders sub-expressions (subscripts, superscripts, Greek, operators)
 */
function renderSubExpression(text: string, keyPrefix: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  let remaining = text;
  let idx = 0;

  while (remaining.length > 0) {
    // 1. Text blocks: \text{...}
    const textMatch = remaining.match(/^\\text\{([^}]+)\}/);
    if (textMatch) {
      nodes.push(
        <span key={`${keyPrefix}-txt-${idx++}`} className="font-sans not-italic text-xs font-normal">
          {textMatch[1]}
        </span>
      );
      remaining = remaining.slice(textMatch[0].length);
      continue;
    }

    // 2. Fractions: \frac{num}{den}
    const fracMatch = remaining.match(/^\\frac\{([^}]+)\}\{([^}]+)\}/);
    if (fracMatch) {
      nodes.push(
        <span
          key={`${keyPrefix}-frac-${idx++}`}
          className="inline-flex flex-col items-center align-middle mx-1 text-center"
        >
          <span className="border-b border-current px-1 text-[11px] leading-tight pb-0.5">
            {renderSubExpression(fracMatch[1], `${keyPrefix}-num-${idx}`)}
          </span>
          <span className="px-1 text-[11px] leading-tight pt-0.5">
            {renderSubExpression(fracMatch[2], `${keyPrefix}-den-${idx}`)}
          </span>
        </span>
      );
      remaining = remaining.slice(fracMatch[0].length);
      continue;
    }

    // 3. Square root: \sqrt{x} or \sqrt[n]{x}
    const sqrtMatch = remaining.match(/^\\sqrt(?:\[([^\]]+)\])?\{([^}]+)\}/);
    if (sqrtMatch) {
      nodes.push(
        <span key={`${keyPrefix}-sqrt-${idx++}`} className="inline-flex items-center align-middle mx-0.5">
          <span className="text-base font-serif leading-none mr-0.5">√</span>
          <span className="border-t border-current pt-0.5 px-0.5 text-xs">
            {renderSubExpression(sqrtMatch[2], `${keyPrefix}-sqrtin-${idx}`)}
          </span>
        </span>
      );
      remaining = remaining.slice(sqrtMatch[0].length);
      continue;
    }

    // 4. Superscripts: ^{...} or ^x
    const supMatch = remaining.match(/^\^(?:\{([^}]+)\}|([0-9a-zA-Z+-]+))/);
    if (supMatch) {
      const content = supMatch[1] || supMatch[2];
      nodes.push(
        <sup key={`${keyPrefix}-sup-${idx++}`} className="text-[10px] font-sans ml-0.5">
          {content}
        </sup>
      );
      remaining = remaining.slice(supMatch[0].length);
      continue;
    }

    // 5. Subscripts: _{...} or _x
    const subMatch = remaining.match(/^_(?:\{([^}]+)\}|([0-9a-zA-Z+-]+))/);
    if (subMatch) {
      const content = subMatch[1] || subMatch[2];
      nodes.push(
        <sub key={`${keyPrefix}-sub-${idx++}`} className="text-[10px] font-sans ml-0.5">
          {content}
        </sub>
      );
      remaining = remaining.slice(subMatch[0].length);
      continue;
    }

    // 6. Greek letters
    let matchedGreek = false;
    for (const [cmd, char] of Object.entries(GREEK_MAP)) {
      if (remaining.startsWith(cmd)) {
        nodes.push(
          <span key={`${keyPrefix}-grk-${idx++}`} className="font-serif italic mx-0.5">
            {char}
          </span>
        );
        remaining = remaining.slice(cmd.length);
        matchedGreek = true;
        break;
      }
    }
    if (matchedGreek) continue;

    // 7. Math symbols
    let matchedSymbol = false;
    for (const [cmd, sym] of Object.entries(SYMBOL_MAP)) {
      if (remaining.startsWith(cmd)) {
        nodes.push(
          <span key={`${keyPrefix}-sym-${idx++}`} className="font-sans font-medium mx-0.5">
            {sym}
          </span>
        );
        remaining = remaining.slice(cmd.length);
        matchedSymbol = true;
        break;
      }
    }
    if (matchedSymbol) continue;

    // 8. Plain character or alphanumeric token
    const tokenMatch = remaining.match(/^([a-zA-Z]+|[0-9.]+|[=+\-*/(),:]|\s+)/);
    if (tokenMatch) {
      const tok = tokenMatch[1];
      // Single letter identifiers are italicized in mathematical notation
      if (/^[a-zA-Z]$/.test(tok)) {
        nodes.push(
          <span key={`${keyPrefix}-var-${idx++}`} className="font-serif italic px-0.5">
            {tok}
          </span>
        );
      } else {
        nodes.push(
          <span key={`${keyPrefix}-tok-${idx++}`} className="font-mono text-xs">
            {tok}
          </span>
        );
      }
      remaining = remaining.slice(tok.length);
      continue;
    }

    // Fallback: single character
    nodes.push(<span key={`${keyPrefix}-chr-${idx++}`}>{remaining[0]}</span>);
    remaining = remaining.slice(1);
  }

  return nodes;
}

export function FormulaBlock({ formula, inline = false, className, caption }: FormulaBlockProps) {
  // Clean formula string (trim leading/trailing $ if any)
  const clean = formula.replace(/^\$\$?/, "").replace(/\$\$?$/, "").trim();
  const renderedContent = renderSubExpression(clean, "math");

  if (inline) {
    return (
      <span
        role="math"
        aria-label={clean}
        className={cn(
          "inline-flex items-center px-1.5 py-0.5 rounded bg-slate-100 dark:bg-navy-950 font-mono text-xs text-orange-600 dark:text-orange-400 border border-slate-200/60 dark:border-slate-800 mx-0.5",
          className
        )}
      >
        {renderedContent}
      </span>
    );
  }

  return (
    <figure
      data-testid="formula-block"
      role="math"
      aria-label={clean}
      className={cn(
        "my-3 overflow-x-auto rounded-xl bg-slate-50 dark:bg-navy-950 border border-slate-200 dark:border-slate-800 p-3 sm:p-4 text-center text-slate-900 dark:text-slate-100 shadow-2xs",
        className
      )}
    >
      <div className="flex items-center justify-center min-w-max py-1 text-sm sm:text-base font-serif">
        {renderedContent}
      </div>
      {caption && (
        <figcaption className="mt-2 text-[11px] text-slate-500 dark:text-slate-400 font-sans tracking-tight">
          {caption}
        </figcaption>
      )}
    </figure>
  );
}

