import { Sparkles } from "lucide-react";

export default function DashboardLoading() {
  return (
    <div className="w-full min-h-[60vh] flex flex-col items-center justify-center space-y-4 font-sans animate-in fade-in duration-300">
      <div className="relative flex items-center justify-center">
        {/* Outer glowing pulsing ring */}
        <div className="w-16 h-16 rounded-2xl bg-orange-500/10 dark:bg-orange-500/20 animate-pulse border border-orange-500/30" />
        {/* Inner spinner */}
        <div className="absolute w-8 h-8 border-2 border-orange-500 border-t-transparent rounded-full animate-spin" />
      </div>

      <div className="text-center space-y-1">
        <div className="flex items-center justify-center gap-1.5 text-xs font-bold text-orange-600 dark:text-orange-400">
          <Sparkles className="w-3.5 h-3.5" />
          <span>TameerAI Intelligence Engine</span>
        </div>
        <p className="text-[11px] text-slate-400">Loading workspace data...</p>
      </div>
    </div>
  );
}
