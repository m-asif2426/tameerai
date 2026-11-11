"use client";

import React, { useState } from "react";
import { Copy, Check, Table as TableIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export interface MessageTableProps {
  headers?: string[];
  rows?: string[][];
  rawMarkdown?: string;
  caption?: string;
  className?: string;
  alignments?: Array<"left" | "center" | "right">;
}

/**
 * Parses a standard markdown table text into structured headers, rows, and alignments
 */
export function parseMarkdownTable(markdown: string): {
  headers: string[];
  rows: string[][];
  alignments: Array<"left" | "center" | "right">;
} {
  const lines = markdown
    .trim()
    .split("\n")
    .map((l) => l.trim())
    .filter((l) => l.startsWith("|") && l.endsWith("|"));

  if (lines.length < 2) {
    return { headers: [], rows: [], alignments: [] };
  }

  // Header line
  const parseRow = (line: string) =>
    line
      .slice(1, -1)
      .split("|")
      .map((c) => c.trim());

  const headers = parseRow(lines[0]);
  let startRowIdx = 1;
  let delimiterCols: string[] = [];

  if (lines.length > 1 && lines[1].includes("-")) {
    delimiterCols = parseRow(lines[1]);
    startRowIdx = 2;
  }

  const alignments: Array<"left" | "center" | "right"> = delimiterCols.map((col) => {
    const left = col.startsWith(":");
    const right = col.endsWith(":");
    if (left && right) return "center";
    if (right) return "right";
    return "left";
  });

  const rows: string[][] = [];
  for (let i = startRowIdx; i < lines.length; i++) {
    const cols = parseRow(lines[i]);
    if (cols.length > 0) {
      rows.push(cols);
    }
  }

  return { headers, rows, alignments };
}

export function MessageTable({
  headers: initialHeaders,
  rows: initialRows,
  rawMarkdown,
  caption,
  className,
  alignments: initialAlignments,
}: MessageTableProps) {
  const [copied, setCopied] = useState(false);

  // If rawMarkdown is provided, parse it
  let headers = initialHeaders || [];
  let rows = initialRows || [];
  let alignments = initialAlignments || [];

  if (rawMarkdown && headers.length === 0) {
    const parsed = parseMarkdownTable(rawMarkdown);
    headers = parsed.headers;
    rows = parsed.rows;
    alignments = parsed.alignments;
  }

  if (headers.length === 0 && rows.length === 0) {
    return null;
  }

  // Determine column alignment if not provided by markdown delimiter
  const computedAlignments = headers.map((header, colIdx) => {
    if (alignments[colIdx]) return alignments[colIdx];
    // Check if majority of values in this column are numeric
    let numericCount = 0;
    for (const row of rows) {
      const val = row[colIdx];
      if (val && /^[$€£₨]?\s*-?[0-9,]+(\.[0-9]+)?\s*[%a-zA-Z/²³^]*$/.test(val.trim())) {
        numericCount++;
      }
    }
    if (rows.length > 0 && numericCount / rows.length >= 0.7) {
      return "right";
    }
    return "left";
  });

  const handleCopyTable = () => {
    // Generate TSV for clean Excel / Sheets pasting
    const lines = [headers.join("\t")];
    for (const r of rows) {
      lines.push(r.join("\t"));
    }
    navigator.clipboard.writeText(lines.join("\n"));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div
      data-testid="message-table-container"
      className={cn(
        "my-3 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-navy-950 shadow-2xs overflow-hidden",
        className
      )}
    >
      <div className="flex items-center justify-between px-3 py-2 bg-slate-50 dark:bg-navy-900 border-b border-slate-200/80 dark:border-slate-800 text-[11px] text-slate-500 dark:text-slate-400 font-medium">
        <div className="flex items-center gap-1.5 font-semibold text-slate-700 dark:text-slate-300">
          <TableIcon className="w-3.5 h-3.5 text-orange-500" />
          <span>{caption || "Engineering Data Specification"}</span>
        </div>
        <button
          type="button"
          onClick={handleCopyTable}
          className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-md hover:bg-slate-200/60 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-300 transition-colors"
          title="Copy table to clipboard"
          aria-label="Copy table data"
        >
          {copied ? (
            <>
              <Check className="w-3 h-3 text-emerald-500" />
              <span className="text-emerald-600 dark:text-emerald-400 font-medium">Copied</span>
            </>
          ) : (
            <>
              <Copy className="w-3 h-3" />
              <span>Copy Data</span>
            </>
          )}
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left border-collapse" role="table">
          <thead>
            <tr className="border-b border-slate-200 dark:border-slate-800 bg-slate-100/50 dark:bg-navy-900/60">
              {headers.map((h, i) => (
                <th
                  key={i}
                  scope="col"
                  className={cn(
                    "px-3.5 py-2.5 font-bold tracking-tight text-[11px] text-slate-700 dark:text-slate-200 uppercase",
                    computedAlignments[i] === "right" && "text-right",
                    computedAlignments[i] === "center" && "text-center",
                    computedAlignments[i] === "left" && "text-left"
                  )}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {rows.map((row, rIdx) => (
              <tr
                key={rIdx}
                className={cn(
                  "transition-colors hover:bg-orange-500/5 dark:hover:bg-orange-500/5",
                  rIdx % 2 === 1 ? "bg-slate-50/40 dark:bg-navy-900/30" : "bg-transparent"
                )}
              >
                {row.map((cell, cIdx) => (
                  <td
                    key={cIdx}
                    className={cn(
                      "px-3.5 py-2 text-slate-700 dark:text-slate-300 text-xs font-mono sm:font-sans",
                      computedAlignments[cIdx] === "right" && "text-right font-mono",
                      computedAlignments[cIdx] === "center" && "text-center",
                      computedAlignments[cIdx] === "left" && "text-left"
                    )}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
