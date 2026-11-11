"use client";

import React, { useState } from "react";
import { Copy, Check, Code as CodeIcon, Terminal } from "lucide-react";
import { FormulaBlock } from "./FormulaBlock";
import { MessageTable, parseMarkdownTable } from "./MessageTable";
import { CalculationBlock, CalculationData } from "./CalculationBlock";
import { SafetyNotice, SafetySeverity } from "./SafetyNotice";
import { CitationList, CitationItem } from "./CitationList";
import { cn } from "@/lib/utils";

interface MessageContentRendererProps {
  content: string;
  citations?: CitationItem[];
  language?: "en" | "ur";
  className?: string;
}

/**
 * Parses inline formatting: bold, italic, inline code, inline formulas ($...$)
 */
function renderInlineFormatting(text: string, keyPrefix: string): React.ReactNode[] {
  const elements: React.ReactNode[] = [];
  let remaining = text;
  let idx = 0;

  while (remaining.length > 0) {
    // 1. Inline formula: $...$ (ensure not double $$)
    const mathMatch = remaining.match(/^\$([^$]+)\$/);
    if (mathMatch && !remaining.startsWith("$$")) {
      elements.push(
        <FormulaBlock
          key={`${keyPrefix}-math-${idx++}`}
          formula={mathMatch[1]}
          inline={true}
        />
      );
      remaining = remaining.slice(mathMatch[0].length);
      continue;
    }

    // 2. Bold text: **...** or __...__
    const boldMatch = remaining.match(/^(\*\*|__)(.*?)\1/);
    if (boldMatch) {
      elements.push(
        <strong key={`${keyPrefix}-b-${idx++}`} className="font-bold text-slate-900 dark:text-slate-100">
          {renderInlineFormatting(boldMatch[2], `${keyPrefix}-bin-${idx}`)}
        </strong>
      );
      remaining = remaining.slice(boldMatch[0].length);
      continue;
    }

    // 3. Italic text: *...* or _..._
    const italicMatch = remaining.match(/^(\*|_)(.*?)\1/);
    if (italicMatch && italicMatch[2].length > 0) {
      elements.push(
        <em key={`${keyPrefix}-it-${idx++}`} className="italic text-slate-800 dark:text-slate-200">
          {renderInlineFormatting(italicMatch[2], `${keyPrefix}-itin-${idx}`)}
        </em>
      );
      remaining = remaining.slice(italicMatch[0].length);
      continue;
    }

    // 4. Inline code: `...`
    const codeMatch = remaining.match(/^`([^`]+)`/);
    if (codeMatch) {
      elements.push(
        <code
          key={`${keyPrefix}-code-${idx++}`}
          className="px-1.5 py-0.5 rounded bg-slate-100 dark:bg-navy-950 font-mono text-[11px] text-orange-600 dark:text-orange-400 border border-slate-200 dark:border-slate-800"
        >
          {codeMatch[1]}
        </code>
      );
      remaining = remaining.slice(codeMatch[0].length);
      continue;
    }

    // 5. Normal text run up to the next special character
    const textMatch = remaining.match(/^[^$*_`]+/);
    if (textMatch) {
      elements.push(<span key={`${keyPrefix}-txt-${idx++}`}>{textMatch[0]}</span>);
      remaining = remaining.slice(textMatch[0].length);
      continue;
    }

    // Fallback: single character
    elements.push(<span key={`${keyPrefix}-char-${idx++}`}>{remaining[0]}</span>);
    remaining = remaining.slice(1);
  }

  return elements;
}

/**
 * Parse structured text calculation block into CalculationData
 */
function parseCalculationContent(raw: string): CalculationData {
  const trimmed = raw.trim();

  // Try JSON first if block starts with {
  if (trimmed.startsWith("{")) {
    try {
      const parsed = JSON.parse(trimmed);
      return {
        title: parsed.title || "Engineering Calculation",
        inputs: parsed.inputs || [],
        formula: parsed.formula || "",
        formulaCaption: parsed.formulaCaption,
        variables: parsed.variables || [],
        substitution: parsed.substitution || "",
        intermediateSteps: parsed.intermediateSteps || [],
        finalResult: parsed.finalResult || { value: "", unit: "" },
        assumptions: parsed.assumptions || [],
        limitations: parsed.limitations || [],
        recommendation: parsed.recommendation,
      };
    } catch {
      // Fall through to text parser
    }
  }

  // Parse structured key-value lines
  const lines = trimmed.split("\n");
  const data: CalculationData = {
    title: "Engineering Calculation",
    inputs: [],
    formula: "",
    variables: [],
    substitution: "",
    intermediateSteps: [],
    finalResult: { value: "", unit: "" },
    assumptions: [],
    limitations: [],
  };

  let currentSection = "";
  let tableMarkdown = "";

  for (const line of lines) {
    const l = line.trim();
    if (!l) continue;

    if (/^Title:\s*/i.test(l)) {
      data.title = l.replace(/^Title:\s*/i, "").trim();
      currentSection = "title";
      continue;
    }

    if (/^Inputs:\s*/i.test(l)) {
      currentSection = "inputs";
      tableMarkdown = "";
      continue;
    }

    if (/^Formula:\s*/i.test(l)) {
      data.formula = l.replace(/^Formula:\s*/i, "").trim();
      currentSection = "formula";
      continue;
    }

    if (/^Variables:\s*/i.test(l)) {
      const rest = l.replace(/^Variables:\s*/i, "").trim();
      if (rest) {
        const parts = rest.split(":");
        data.variables.push({
          symbol: parts[0]?.trim() || "",
          name: parts[1]?.trim() || "",
        });
      }
      currentSection = "variables";
      continue;
    }

    if (/^Substitution:\s*/i.test(l)) {
      data.substitution = l.replace(/^Substitution:\s*/i, "").trim();
      currentSection = "substitution";
      continue;
    }

    if (/^Intermediate:\s*/i.test(l) || /^Intermediate Steps:\s*/i.test(l)) {
      const rest = l.replace(/^(Intermediate Steps|Intermediate):\s*/i, "").trim();
      if (rest) {
        data.intermediateSteps.push(rest);
      }
      currentSection = "intermediate";
      continue;
    }

    if (/^Result:\s*/i.test(l) || /^Final Result:\s*/i.test(l)) {
      const resText = l.replace(/^(Final )?Result:\s*/i, "").trim();
      // Try to parse: "300 cu ft (11.11 yd³)" or "11.11 yd³"
      const match = resText.match(/^([0-9.,]+)\s*([a-zA-Z³²/%^]+)?(?:\s*\[(.*?)\]|\s*\((.*?)\))?$/);
      if (match) {
        data.finalResult = {
          value: match[1],
          unit: match[2] || "Units",
          highlightText: match[3] || match[4] || undefined,
        };
      } else {
        data.finalResult = { value: resText, unit: "" };
      }
      currentSection = "result";
      continue;
    }

    if (/^Assumptions:\s*/i.test(l)) {
      const rest = l.replace(/^Assumptions:\s*/i, "").trim();
      if (rest) {
        const items = rest.split(";").map((s) => s.trim()).filter(Boolean);
        data.assumptions.push(...items);
      }
      currentSection = "assumptions";
      continue;
    }

    if (/^Limitations:\s*/i.test(l)) {
      const rest = l.replace(/^Limitations:\s*/i, "").trim();
      if (rest) {
        const items = rest.split(";").map((s) => s.trim()).filter(Boolean);
        data.limitations.push(...items);
      }
      currentSection = "limitations";
      continue;
    }

    if (/^Recommendation:\s*/i.test(l) || /^Note:\s*/i.test(l)) {
      data.recommendation = l.replace(/^(Recommendation|Note):\s*/i, "").trim();
      currentSection = "recommendation";
      continue;
    }

    // Content lines according to current section
    if (currentSection === "inputs") {
      if (l.startsWith("|")) {
        tableMarkdown += l + "\n";
        const parsedTbl = parseMarkdownTable(tableMarkdown);
        if (parsedTbl.rows.length > 0) {
          data.inputs = parsedTbl.rows.map((row) => ({
            name: row[0] || "",
            symbol: row[1] || "",
            value: row[2] || "",
            unit: row[3] || "",
            notes: row[4] || "",
          }));
        }
      } else if (l.startsWith("-") || l.startsWith("*")) {
        const item = l.replace(/^[-*]\s*/, "");
        const parts = item.split(":");
        data.inputs.push({
          name: parts[0]?.trim() || "Parameter",
          symbol: "",
          value: parts[1]?.trim() || "",
          unit: "",
        });
      }
    } else if (currentSection === "variables") {
      if (l.startsWith("-") || l.startsWith("*")) {
        const item = l.replace(/^[-*]\s*/, "");
        const parts = item.split(":");
        data.variables.push({
          symbol: parts[0]?.trim() || "",
          name: parts[1]?.trim() || "",
        });
      }
    } else if (currentSection === "intermediate") {
      if (l.startsWith("-") || l.startsWith("*") || /^\d+\./.test(l)) {
        data.intermediateSteps.push(l.replace(/^[-*\d.]+\s*/, ""));
      } else {
        data.intermediateSteps.push(l);
      }
    } else if (currentSection === "assumptions") {
      if (l.startsWith("-") || l.startsWith("*")) {
        data.assumptions.push(l.replace(/^[-*]\s*/, ""));
      } else {
        data.assumptions.push(l);
      }
    } else if (currentSection === "limitations") {
      if (l.startsWith("-") || l.startsWith("*")) {
        data.limitations.push(l.replace(/^[-*]\s*/, ""));
      } else {
        data.limitations.push(l);
      }
    }
  }

  // Fallbacks if some fields missing
  if (data.inputs.length === 0) {
    data.inputs = [{ name: "Standard Design Spec", symbol: "D", value: "Standard", unit: "-" }];
  }
  if (!data.formula) {
    data.formula = "Q = f(A, B, C)";
  }
  if (!data.substitution) {
    data.substitution = "Direct engineering evaluation";
  }
  if (data.assumptions.length === 0) {
    data.assumptions.push("Pakistan Building Code (PBC 2021) standard factors applied.");
  }
  if (data.limitations.length === 0) {
    data.limitations.push("Subject to site structural inspection and soil conditions.");
  }

  return data;
}

/**
 * Parse structured safety block into SafetyNoticeProps
 */
function parseSafetyContent(raw: string, defaultLevel: SafetySeverity = "warning"): {
  level: SafetySeverity;
  title?: string;
  message: string;
  codeReference?: string;
  clause?: string;
} {
  const lines = raw.trim().split("\n");
  let level = defaultLevel;
  let title = "";
  let message = "";
  let codeReference = "";
  let clause = "";

  for (const line of lines) {
    const l = line.trim();
    if (!l) continue;

    if (/^Level:\s*/i.test(l)) {
      const lvl = l.replace(/^Level:\s*/i, "").trim().toLowerCase();
      if (lvl === "critical" || lvl === "warning" || lvl === "caution" || lvl === "info") {
        level = lvl;
      }
      continue;
    }

    if (/^Title:\s*/i.test(l)) {
      title = l.replace(/^Title:\s*/i, "").trim();
      continue;
    }

    if (/^Code:\s*/i.test(l) || /^Reference:\s*/i.test(l)) {
      codeReference = l.replace(/^(Code|Reference):\s*/i, "").trim();
      continue;
    }

    if (/^Clause:\s*/i.test(l)) {
      clause = l.replace(/^Clause:\s*/i, "").trim();
      continue;
    }

    if (/^Message:\s*/i.test(l)) {
      message = l.replace(/^Message:\s*/i, "").trim();
      continue;
    }

    // Accumulate into message if not a header
    message += (message ? " " : "") + l;
  }

  return { level, title, message, codeReference, clause };
}

/**
 * Standard Code Block with syntax highlight container & copy action
 */
function CodeBlock({ code, language }: { code: string; language?: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      data-testid="message-code-block"
      className="my-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-slate-900 text-slate-100 overflow-hidden shadow-2xs"
    >
      <div className="flex items-center justify-between px-3 py-1.5 bg-slate-950/70 border-b border-slate-800 text-[11px] text-slate-400">
        <div className="flex items-center gap-1.5 font-mono">
          <Terminal className="w-3.5 h-3.5 text-orange-400" />
          <span>{language || "text"}</span>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded hover:bg-slate-800 text-slate-300 transition-colors"
          title="Copy code"
          aria-label="Copy code block"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-400" />
              <span className="text-emerald-400">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="p-3 text-xs font-mono overflow-x-auto leading-relaxed">
        <code>{code}</code>
      </pre>
    </div>
  );
}

export function MessageContentRenderer({
  content,
  citations,
  language = "en",
  className,
}: MessageContentRendererProps) {
  // Support both explicit language context and automatic script detection for bilingual support
  const hasUrduCharacters = /[\u0600-\u06FF]/.test(content);
  const isUrdu = language === "ur" || hasUrduCharacters;

  // Pre-split content into blocks: fenced blocks (```...```), tables (|...|), math ($$...$$), and paragraphs
  const blocks: React.ReactNode[] = [];
  const lines = content.split("\n");
  let i = 0;
  let blockKey = 0;

  while (i < lines.length) {
    const line = lines[i];
    const trimmed = line.trim();

    // 1. Fenced Code / Calculation / Safety / Math Blocks
    if (trimmed.startsWith("```")) {
      const fenceTag = trimmed.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // Skip closing ```
      const blockBody = codeLines.join("\n");

      // Check fence type
      if (fenceTag === "calculation") {
        const calcData = parseCalculationContent(blockBody);
        blocks.push(
          <CalculationBlock
            key={`calc-${blockKey++}`}
            data={calcData}
            language={language}
          />
        );
        continue;
      }

      if (fenceTag.startsWith("safety")) {
        const severityPart = fenceTag.split(":")[1]?.toLowerCase() as SafetySeverity;
        const validSeverity: SafetySeverity =
          severityPart === "critical" || severityPart === "caution" || severityPart === "info"
            ? severityPart
            : "warning";
        const safetyData = parseSafetyContent(blockBody, validSeverity);
        blocks.push(
          <SafetyNotice
            key={`safe-${blockKey++}`}
            level={safetyData.level}
            title={safetyData.title}
            message={safetyData.message}
            codeReference={safetyData.codeReference}
            clause={safetyData.clause}
            language={language}
          />
        );
        continue;
      }

      if (fenceTag === "math" || fenceTag === "formula") {
        blocks.push(
          <FormulaBlock
            key={`math-${blockKey++}`}
            formula={blockBody}
            inline={false}
          />
        );
        continue;
      }

      // Default: Code block
      blocks.push(
        <CodeBlock
          key={`code-${blockKey++}`}
          code={blockBody}
          language={fenceTag || "text"}
        />
      );
      continue;
    }

    // 2. Standalone Math Block: $$ ... $$
    if (trimmed.startsWith("$$")) {
      const mathLines: string[] = [];
      if (trimmed.endsWith("$$") && trimmed.length > 2) {
        // Single-line block math
        const formula = trimmed.slice(2, -2).trim();
        blocks.push(
          <FormulaBlock
            key={`math-${blockKey++}`}
            formula={formula}
            inline={false}
          />
        );
        i++;
        continue;
      } else {
        i++;
        while (i < lines.length && !lines[i].trim().endsWith("$$")) {
          mathLines.push(lines[i]);
          i++;
        }
        if (i < lines.length) {
          mathLines.push(lines[i].trim().slice(0, -2));
          i++;
        }
        blocks.push(
          <FormulaBlock
            key={`math-${blockKey++}`}
            formula={mathLines.join("\n")}
            inline={false}
          />
        );
        continue;
      }
    }

    // 3. GitHub Alert Callouts: > [!WARNING], > [!CRITICAL], > [!NOTE], > [!CAUTION]
    if (trimmed.startsWith("> [!")) {
      const alertTypeMatch = trimmed.match(/^>\s*\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION|CRITICAL)\]/i);
      const alertType = alertTypeMatch ? alertTypeMatch[1].toUpperCase() : "WARNING";
      const calloutLines: string[] = [];
      i++;
      while (i < lines.length && lines[i].trim().startsWith(">")) {
        calloutLines.push(lines[i].trim().replace(/^>\s*/, ""));
        i++;
      }
      let severity: SafetySeverity = "warning";
      if (alertType === "CRITICAL") severity = "critical";
      else if (alertType === "CAUTION") severity = "caution";
      else if (alertType === "NOTE" || alertType === "TIP") severity = "info";

      blocks.push(
        <SafetyNotice
          key={`alert-${blockKey++}`}
          level={severity}
          title={alertType === "CRITICAL" ? "Critical Engineering Alert" : `${alertType} Advisory`}
          message={calloutLines.join(" ")}
          language={language}
        />
      );
      continue;
    }

    // 4. Markdown Tables: starts with | and contains |
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith("|") && lines[i].trim().endsWith("|")) {
        tableLines.push(lines[i].trim());
        i++;
      }
      blocks.push(
        <MessageTable
          key={`tbl-${blockKey++}`}
          rawMarkdown={tableLines.join("\n")}
        />
      );
      continue;
    }

    // 5. Headings: #, ##, ###, ####
    if (trimmed.startsWith("#")) {
      const hMatch = trimmed.match(/^(#{1,4})\s+(.+)$/);
      if (hMatch) {
        const level = hMatch[1].length;
        const text = hMatch[2];
        const headingClass =
          level === 1
            ? "text-base font-bold text-slate-900 dark:text-slate-100 my-2 pt-1 border-b border-slate-200 dark:border-slate-800 pb-1"
            : level === 2
            ? "text-sm font-bold text-slate-900 dark:text-slate-100 my-2"
            : "text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 my-1.5";

        blocks.push(
          <div key={`h-${blockKey++}`} className={headingClass}>
            {renderInlineFormatting(text, `h-${blockKey}`)}
          </div>
        );
        i++;
        continue;
      }
    }

    // 6. Lists: bullet points (- or *) or numbered (1., 2.)
    if (/^[-*]\s+/.test(trimmed) || /^\d+\.\s+/.test(trimmed)) {
      const isNumbered = /^\d+\.\s+/.test(trimmed);
      const listItems: string[] = [];
      while (
        i < lines.length &&
        ((isNumbered && /^\d+\.\s+/.test(lines[i].trim())) ||
          (!isNumbered && /^[-*]\s+/.test(lines[i].trim())))
      ) {
        listItems.push(lines[i].trim().replace(/^([-*]|\d+\.)\s+/, ""));
        i++;
      }

      if (isNumbered) {
        blocks.push(
          <ol
            key={`list-${blockKey++}`}
            className="my-2 list-decimal list-inside space-y-1 text-xs text-slate-700 dark:text-slate-300 leading-relaxed"
          >
            {listItems.map((item, idx) => (
              <li key={idx}>{renderInlineFormatting(item, `ol-${blockKey}-${idx}`)}</li>
            ))}
          </ol>
        );
      } else {
        blocks.push(
          <ul
            key={`list-${blockKey++}`}
            className="my-2 list-disc list-inside space-y-1 text-xs text-slate-700 dark:text-slate-300 leading-relaxed"
          >
            {listItems.map((item, idx) => (
              <li key={idx}>{renderInlineFormatting(item, `ul-${blockKey}-${idx}`)}</li>
            ))}
          </ul>
        );
      }
      continue;
    }

    // 7. Regular paragraph / text line
    if (trimmed.length > 0) {
      blocks.push(
        <p
          key={`p-${blockKey++}`}
          className="my-1.5 text-xs text-slate-800 dark:text-slate-200 leading-relaxed font-sans"
        >
          {renderInlineFormatting(trimmed, `p-${blockKey}`)}
        </p>
      );
    }

    i++;
  }

  return (
    <div
      data-testid="message-content-renderer"
      className={cn("space-y-1 text-xs leading-relaxed", className)}
      dir={isUrdu ? "rtl" : "ltr"}
    >
      {blocks}

      {/* Statutory Citations Section */}
      {citations && citations.length > 0 && (
        <CitationList citations={citations} language={language} />
      )}
    </div>
  );
}
