import React, { useMemo, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ReferenceLine,
  Legend,
} from "recharts";

/**
 * Equity Curve Experiment Dashboard
 * - Single strategy mode by default
 * - Optional Comparison Mode (Strategy A vs Strategy B)
 * - Adjustable probabilities and payoffs with live charts & risk metrics
 *
 * Notes:
 * - Keeps the spirit of the uploaded artifact, but fixes missing state/variables and adds
 *   robust stats (drawdowns, time underwater, simple risk-of-ruin, VaR 5%).
 */

// ----------------------- Types -----------------------
interface Params {
  E0: number; // initial equity
  f: number; // risk per trade fraction
  M: number; // reward multiple
  W: number; // win rate fraction
  B: number; // breakeven rate fraction
  sL: number; // loss severity bias (0 => all max loss, 1 => all half loss)
  w4: number; // half gain weight (pre-normalized)
  w5: number; // max gain weight (pre-normalized)
  w6: number; // extended gain weight (pre-normalized)
  numTrades: number; // number of trades per path
  numPaths: number; // number of paths
}

interface Derived {
  L: number; // loss rate = 1 - W - B
  probabilities: { p1: number; p2: number; p3: number; p4: number; p5: number; p6: number };
  deltas: { delta1: number; delta2: number; delta3: number; delta4: number; delta5: number; delta6: number };
  expectedDelta: number;
  expectedGeometric: number;
  winWeightSum: number;
  w4_norm: number;
  w5_norm: number;
  w6_norm: number;
}

interface RiskPerPath {
  finalEquity: number;
  totalReturn: number; // %
  maxDrawdownPct: number; // %
  timeUnderwaterPct: number; // % of points below prior peak
  hitHalfRuin: boolean; // ever below 50% of E0
}

interface Stats {
  meanFinalEquity: number;
  minFinalEquity: number;
  maxFinalEquity: number;
  meanReturn: number; // %
  meanMaxDrawdown: number; // %
  p95MaxDrawdown: number; // %
  meanTimeUnderwater: number; // %
  riskOfRuinPercent: number; // % of paths hitting 50% E0
  var5Percent: number; // per-trade VaR (as a fraction, e.g., -0.02 => -2%)
}

// ----------------------- Helpers -----------------------
function clamp(n: number, lo: number, hi: number) {
  return Math.max(lo, Math.min(hi, n));
}

function quantile(sorted: number[], q: number) {
  if (sorted.length === 0) return 0;
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (sorted[base + 1] !== undefined) {
    return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
  } else {
    return sorted[base];
  }
}

function computeDerived(params: Params): Derived {
  const L_raw = 1 - params.W - params.B;
  const L = Math.max(0, L_raw); // prevent negatives; UI will warn if W+B>1

  const winWeightSum = params.w4 + params.w5 + params.w6;
  const w4_norm = winWeightSum > 0 ? params.w4 / winWeightSum : 1;
  const w5_norm = winWeightSum > 0 ? params.w5 / winWeightSum : 0;
  const w6_norm = winWeightSum > 0 ? params.w6 / winWeightSum : 0;

  const probabilities = {
    p1: clamp((1 - params.sL) * L, 0, 1), // Max loss
    p2: clamp(params.sL * L, 0, 1), // Half loss
    p3: clamp(params.B, 0, 1), // Breakeven
    p4: clamp(w4_norm * params.W, 0, 1), // Half gain
    p5: clamp(w5_norm * params.W, 0, 1), // Max gain
    p6: clamp(w6_norm * params.W, 0, 1), // Extended gain
  };

  // Normalize tiny drift that may arise from clamps
  const sumP = Object.values(probabilities).reduce((a, b) => a + b, 0) || 1;
  (Object.keys(probabilities) as (keyof typeof probabilities)[]).forEach((k) => {
    probabilities[k] = probabilities[k] / sumP;
  });

  const deltas = {
    delta1: -params.f, // Max Loss
    delta2: -0.5 * params.f, // Half Loss
    delta3: 0, // Breakeven
    delta4: 0.5 * params.M * params.f, // Half Gain
    delta5: 1.0 * params.M * params.f, // Max Gain
    delta6: 1.5 * params.M * params.f, // Extended Gain
  };

  const expectedDelta =
    probabilities.p1 * deltas.delta1 +
    probabilities.p2 * deltas.delta2 +
    probabilities.p3 * deltas.delta3 +
    probabilities.p4 * deltas.delta4 +
    probabilities.p5 * deltas.delta5 +
    probabilities.p6 * deltas.delta6;

  const expectedGeometric =
    probabilities.p1 * Math.log(1 + deltas.delta1) +
    probabilities.p2 * Math.log(1 + deltas.delta2) +
    probabilities.p3 * Math.log(1 + deltas.delta3) +
    probabilities.p4 * Math.log(1 + deltas.delta4) +
    probabilities.p5 * Math.log(1 + deltas.delta5) +
    probabilities.p6 * Math.log(1 + deltas.delta6);

  return {
    L,
    probabilities,
    deltas,
    expectedDelta,
    expectedGeometric,
    winWeightSum,
    w4_norm,
    w5_norm,
    w6_norm,
  };
}

function generateOutcome(rand: number, probabilities: Derived["probabilities"]) {
  const cumulative = [
    probabilities.p1,
    probabilities.p1 + probabilities.p2,
    probabilities.p1 + probabilities.p2 + probabilities.p3,
    probabilities.p1 + probabilities.p2 + probabilities.p3 + probabilities.p4,
    probabilities.p1 + probabilities.p2 + probabilities.p3 + probabilities.p4 + probabilities.p5,
    1.0,
  ];
  for (let i = 0; i < cumulative.length; i++) {
    if (rand <= cumulative[i]) return i + 1; // 1..6
  }
  return 6;
}

function simulatePaths(params: Params, derived: Derived) {
  const paths: Array<Array<{ trade: number; equity: number }>> = [];
  const riskPerPath: RiskPerPath[] = [];
  const { deltas, probabilities } = derived;

  for (let p = 0; p < params.numPaths; p++) {
    const series: Array<{ trade: number; equity: number }> = [];
    let equity = params.E0;
    series.push({ trade: 0, equity });

    let peak = equity;
    let maxDD = 0; // as fraction
    let timeUnderwater = 0; // count of points below peak
    let hitHalfRuin = false;

    for (let t = 1; t <= params.numTrades; t++) {
      const r = Math.random();
      const outcome = generateOutcome(r, probabilities);

      let delta = 0;
      if (outcome === 1) delta = deltas.delta1;
      else if (outcome === 2) delta = deltas.delta2;
      else if (outcome === 3) delta = deltas.delta3;
      else if (outcome === 4) delta = deltas.delta4;
      else if (outcome === 5) delta = deltas.delta5;
      else delta = deltas.delta6;

      equity = equity * (1 + delta);
      series.push({ trade: t, equity });

      // drawdown tracking
      if (equity > peak) peak = equity;
      const dd = peak > 0 ? (peak - equity) / peak : 0;
      if (dd > maxDD) maxDD = dd;
      if (equity < peak) timeUnderwater += 1;
      if (equity <= 0.5 * params.E0) hitHalfRuin = true;
    }

    const finalEquity = series[series.length - 1].equity;
    const totalReturn = ((finalEquity / params.E0) - 1) * 100;
    const timeUnderwaterPct = (timeUnderwater / series.length) * 100;

    riskPerPath.push({
      finalEquity,
      totalReturn,
      maxDrawdownPct: maxDD * 100,
      timeUnderwaterPct,
      hitHalfRuin,
    });

    paths.push(series);
  }

  // Build chart dataset: trade index → each path equity
  const chartData: Array<Record<string, number>> = [];
  for (let t = 0; t <= params.numTrades; t++) {
    const row: Record<string, number> = { trade: t };
    for (let p = 0; p < params.numPaths; p++) {
      row[`path${p + 1}`] = paths[p][t].equity;
    }
    chartData.push(row);
  }

  return { paths, chartData, riskPerPath };
}

function summarizeStats(params: Params, derived: Derived, riskPerPath: RiskPerPath[]): Stats {
  const finals = riskPerPath.map((r) => r.finalEquity);
  const meanFinal = finals.reduce((a, b) => a + b, 0) / finals.length;
  const minFinal = Math.min(...finals);
  const maxFinal = Math.max(...finals);
  const meanReturn = ((meanFinal / params.E0) - 1) * 100;

  const mdds = riskPerPath.map((r) => r.maxDrawdownPct).sort((a, b) => a - b);
  const tuw = riskPerPath.map((r) => r.timeUnderwaterPct);
  const meanMDD = mdds.reduce((a, b) => a + b, 0) / mdds.length;
  const p95MDD = quantile(mdds, 0.95);
  const meanTUW = tuw.reduce((a, b) => a + b, 0) / tuw.length;
  const riskOfRuin = (riskPerPath.filter((r) => r.hitHalfRuin).length / riskPerPath.length) * 100;

  // VaR 5% from discrete per-trade deltas
  const outcomes: Array<{ d: number; p: number }> = [
    { d: derived.deltas.delta1, p: derived.probabilities.p1 },
    { d: derived.deltas.delta2, p: derived.probabilities.p2 },
    { d: derived.deltas.delta3, p: derived.probabilities.p3 },
    { d: derived.deltas.delta4, p: derived.probabilities.p4 },
    { d: derived.deltas.delta5, p: derived.probabilities.p5 },
    { d: derived.deltas.delta6, p: derived.probabilities.p6 },
  ];
  const expanded: number[] = [];
  // Expand into 10,000 samples for simple quantile (deterministic enough for UI)
  outcomes.forEach(({ d, p }) => {
    const n = Math.round(p * 10000);
    for (let i = 0; i < n; i++) expanded.push(d);
  });
  expanded.sort((a, b) => a - b);
  const var5 = expanded.length ? quantile(expanded, 0.05) : 0;

  return {
    meanFinalEquity: meanFinal,
    minFinalEquity: minFinal,
    maxFinalEquity: maxFinal,
    meanReturn,
    meanMaxDrawdown: meanMDD,
    p95MaxDrawdown: p95MDD,
    meanTimeUnderwater: meanTUW,
    riskOfRuinPercent: riskOfRuin,
    var5Percent: var5,
  };
}

// ----------------------- UI Components -----------------------
const MetricCard: React.FC<{ title: string; value: string; valueB?: string | null; colorScheme: "blue" | "green" | "purple" | "yellow" }> = ({ title, value, valueB, colorScheme }) => {
  const colors: Record<string, string> = {
    blue: "bg-blue-100 text-blue-800 text-blue-600",
    green: "bg-green-100 text-green-800 text-green-600",
    purple: "bg-purple-100 text-purple-800 text-purple-600",
    yellow: "bg-yellow-100 text-yellow-800 text-yellow-600",
  };
  const [bg, headerColor, textColor] = colors[colorScheme].split(" ");
  return (
    <div className={`${bg} p-4 rounded-lg text-center`}>
      <div className={`text-2xl font-bold ${headerColor}`}>{value}</div>
      {valueB && <div className="text-lg font-semibold text-orange-700 mt-1">{valueB}</div>}
      <div className={`text-sm ${textColor}`}>{title}</div>
    </div>
  );
};

const RiskMetricsPanel: React.FC<{ title: string; stats: Stats; colorScheme: "red" | "orange" }> = ({ title, stats, colorScheme }) => {
  const colors = {
    red: { bg: "bg-red-50", header: "text-red-900", text: "text-red-700" },
    orange: { bg: "bg-orange-50", header: "text-orange-900", text: "text-orange-700" },
  } as const;
  const color = colors[colorScheme];
  return (
    <div className={`${color.bg} p-4 rounded-lg`}>
      <h4 className={`font-semibold ${color.header} mb-3`}>{title}</h4>
      <div className="space-y-2 text-sm">
        <div className={`flex justify-between ${color.text}`}>
          <span>Mean Max Drawdown:</span>
          <span className="font-medium">{stats.meanMaxDrawdown.toFixed(1)}%</span>
        </div>
        <div className={`flex justify-between ${color.text}`}>
          <span>95th Percentile DD:</span>
          <span className="font-medium">{stats.p95MaxDrawdown.toFixed(1)}%</span>
        </div>
        <div className={`flex justify-between ${color.text}`}>
          <span>Mean Time Underwater:</span>
          <span className="font-medium">{stats.meanTimeUnderwater.toFixed(1)}%</span>
        </div>
        <div className={`flex justify-between ${color.text}`}>
          <span>Risk of Ruin (50%):</span>
          <span className="font-medium">{stats.riskOfRuinPercent.toFixed(1)}%</span>
        </div>
        <div className={`flex justify-between ${color.text}`}>
          <span>5% VaR (per trade):</span>
          <span className="font-medium">{(stats.var5Percent * 100).toFixed(2)}%</span>
        </div>
      </div>
    </div>
  );
};

const ComparisonPanel: React.FC<{ statsA: Stats; statsB: Stats }> = ({ statsA, statsB }) => {
  const betterA = (a: number, b: number, lowerIsBetter = false) => {
    const better = lowerIsBetter ? a < b : a > b;
    return better ? "text-green-600" : "text-red-600";
  };
  return (
    <div className="bg-gray-50 p-4 rounded-lg">
      <h4 className="font-semibold text-gray-900 mb-3">Strategy Comparison</h4>
      <div className="space-y-2 text-sm">
        <div className="text-gray-700">
          <div className="font-medium mb-1">Returns:</div>
          <div className={`${betterA(statsA.meanReturn, statsB.meanReturn)} text-xs`}>
            A: {statsA.meanReturn.toFixed(1)}% vs B: {statsB.meanReturn.toFixed(1)}%
          </div>
        </div>
        <div className="text-gray-700">
          <div className="font-medium mb-1">Max Drawdown:</div>
          <div className={`${betterA(statsA.meanMaxDrawdown, statsB.meanMaxDrawdown, true)} text-xs`}>
            A: {statsA.meanMaxDrawdown.toFixed(1)}% vs B: {statsB.meanMaxDrawdown.toFixed(1)}%
          </div>
        </div>
        <div className="text-gray-700">
          <div className="font-medium mb-1">Risk of Ruin:</div>
          <div className={`${betterA(statsA.riskOfRuinPercent, statsB.riskOfRuinPercent, true)} text-xs`}>
            A: {statsA.riskOfRuinPercent.toFixed(1)}% vs B: {statsB.riskOfRuinPercent.toFixed(1)}%
          </div>
        </div>
        <div className="text-gray-700">
          <div className="font-medium mb-1">Time Underwater:</div>
          <div className={`${betterA(statsA.meanTimeUnderwater, statsB.meanTimeUnderwater, true)} text-xs`}>
            A: {statsA.meanTimeUnderwater.toFixed(1)}% vs B: {statsB.meanTimeUnderwater.toFixed(1)}%
          </div>
        </div>
        <div className="mt-3 p-2 bg-white rounded text-xs">
          <div className="font-medium text-gray-900">Risk-Adjusted Winner:</div>
          <div className="text-gray-600 mt-1">
            {statsA.meanReturn / Math.max(1e-9, statsA.meanMaxDrawdown) >
            statsB.meanReturn / Math.max(1e-9, statsB.meanMaxDrawdown)
              ? "Strategy A (better return/risk ratio)"
              : "Strategy B (better return/risk ratio)"}
          </div>
        </div>
      </div>
    </div>
  );
};

const ParameterControls: React.FC<{
  params: Params;
  derived: Derived;
  updateParam: (key: keyof Params, value: number) => void;
  colorScheme: "blue" | "orange";
}> = ({ params, derived, updateParam, colorScheme }) => {
  const colors = {
    blue: { bg: "bg-blue-50", text: "text-blue-700", header: "text-blue-900" },
    orange: { bg: "bg-orange-50", text: "text-orange-700", header: "text-orange-900" },
  } as const;
  const color = colors[colorScheme];

  const warnInvalid = params.W + params.B > 1;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Core Strategy Parameters */}
      <div className={`${color.bg} p-4 rounded-lg`}>
        <h4 className={`font-semibold ${color.header} mb-3`}>Core Strategy</h4>
        <div className="space-y-3">
          <div>
            <label className={`block text-sm font-medium ${color.text}`}>Risk per Trade (%)</label>
            <input
              type="range"
              min={0.1}
              max={5}
              step={0.1}
              value={params.f * 100}
              onChange={(e) => updateParam("f", parseFloat(e.target.value) / 100)}
              className="w-full"
            />
            <span className={`text-sm ${color.text}`}>{(params.f * 100).toFixed(1)}%</span>
          </div>
          <div>
            <label className={`block text-sm font-medium ${color.text}`}>Reward Multiple</label>
            <input
              type="range"
              min={1}
              max={10}
              step={0.5}
              value={params.M}
              onChange={(e) => updateParam("M", parseFloat(e.target.value))}
              className="w-full"
            />
            <span className={`text-sm ${color.text}`}>{params.M}:1</span>
          </div>
          <div>
            <label className={`block text-sm font-medium ${color.text}`}>Win Rate (%)</label>
            <input
              type="range"
              min={10}
              max={90}
              step={5}
              value={params.W * 100}
              onChange={(e) => updateParam("W", parseFloat(e.target.value) / 100)}
              className="w-full"
            />
            <span className={`text-sm ${color.text}`}>{(params.W * 100).toFixed(0)}%</span>
          </div>
          <div>
            <label className={`block text-sm font-medium ${color.text}`}>Breakeven Rate (%)</label>
            <input
              type="range"
              min={0}
              max={20}
              step={1}
              value={params.B * 100}
              onChange={(e) => updateParam("B", parseFloat(e.target.value) / 100)}
              className="w-full"
            />
            <span className={`text-sm ${color.text}`}>{(params.B * 100).toFixed(0)}%</span>
          </div>
          {warnInvalid && (
            <div className="text-xs text-red-600 mt-1">
              Warning: Win% + Breakeven% exceeds 100%. Loss probability forced to 0.
            </div>
          )}
        </div>
      </div>

      {/* Loss Distribution */}
      <div className="bg-red-50 p-4 rounded-lg">
        <h4 className="font-semibold text-red-900 mb-3">Loss Distribution</h4>
        <div>
          <label className="block text-sm font-medium text-red-700">Loss Severity Bias</label>
          <input
            type="range"
            min={0}
            max={1}
            step={0.1}
            value={params.sL}
            onChange={(e) => updateParam("sL", parseFloat(e.target.value))}
            className="w-full"
          />
          <div className="text-xs text-red-600 mt-1">
            <div>Max Loss: {((1 - params.sL) * 100).toFixed(0)}%</div>
            <div>Half Loss: {(params.sL * 100).toFixed(0)}%</div>
          </div>
        </div>
        <div className="mt-3 text-xs text-red-600">
          <div>Loss Rate: {(derived.L * 100).toFixed(1)}%</div>
        </div>
      </div>

      {/* Win Distribution */}
      <div className="bg-green-50 p-4 rounded-lg">
        <h4 className="font-semibold text-green-900 mb-3">Win Distribution</h4>
        <div className="space-y-2">
          <div>
            <label className="block text-sm font-medium text-green-700">Half Gain Weight</label>
            <input
              type="range"
              min={0.1}
              max={1}
              step={0.1}
              value={params.w4}
              onChange={(e) => updateParam("w4", parseFloat(e.target.value))}
              className="w-full"
            />
            <span className="text-xs text-green-600">{(derived.w4_norm * 100).toFixed(0)}%</span>
          </div>
          <div>
            <label className="block text-sm font-medium text-green-700">Max Gain Weight</label>
            <input
              type="range"
              min={0.1}
              max={1}
              step={0.1}
              value={params.w5}
              onChange={(e) => updateParam("w5", parseFloat(e.target.value))}
              className="w-full"
            />
            <span className="text-xs text-green-600">{(derived.w5_norm * 100).toFixed(0)}%</span>
          </div>
          <div>
            <label className="block text-sm font-medium text-green-700">Extended Gain Weight</label>
            <input
              type="range"
              min={0.05}
              max={0.5}
              step={0.05}
              value={params.w6}
              onChange={(e) => updateParam("w6", parseFloat(e.target.value))}
              className="w-full"
            />
            <span className="text-xs text-green-600">{(derived.w6_norm * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      {/* Simulation Settings */}
      <div className="bg-gray-50 p-4 rounded-lg">
        <h4 className="font-semibold text-gray-900 mb-3">Simulation</h4>
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700">Number of Trades</label>
            <input
              type="number"
              min={100}
              max={5000}
              step={100}
              value={params.numTrades}
              onChange={(e) => updateParam("numTrades", parseInt(e.target.value || "0", 10))}
              className="w-full px-2 py-1 border rounded text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Number of Paths</label>
            <input
              type="number"
              min={1}
              max={20}
              value={params.numPaths}
              onChange={(e) => updateParam("numPaths", parseInt(e.target.value || "0", 10))}
              className="w-full px-2 py-1 border rounded text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Initial Equity</label>
            <input
              type="number"
              min={1000}
              max={1000000}
              step={1000}
              value={params.E0}
              onChange={(e) => updateParam("E0", parseInt(e.target.value || "0", 10))}
              className="w-full px-2 py-1 border rounded text-sm"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

// ----------------------- Main Component -----------------------
const EquityCurveDashboard: React.FC = () => {
  // Strategy A
  const [paramsA, setParamsA] = useState<Params>({
    E0: 10000,
    f: 0.01,
    M: 4,
    W: 0.45,
    B: 0.05,
    sL: 0.3,
    w4: 0.5,
    w5: 0.4,
    w6: 0.1,
    numTrades: 1000,
    numPaths: 10,
  });
  // Strategy B (for comparison)
  const [paramsB, setParamsB] = useState<Params>({
    ...paramsA,
    f: 0.008,
    W: 0.5,
    B: 0.03,
  });

  const [comparisonMode, setComparisonMode] = useState(false);

  const derivedA = useMemo(() => computeDerived(paramsA), [paramsA]);
  const derivedB = useMemo(() => computeDerived(paramsB), [paramsB]);

  const simA = useMemo(() => simulatePaths(paramsA, derivedA), [paramsA, derivedA]);
  const statsA = useMemo(() => summarizeStats(paramsA, derivedA, simA.riskPerPath), [paramsA, derivedA, simA]);

  const simB = useMemo(() => (comparisonMode ? simulatePaths(paramsB, derivedB) : null), [comparisonMode, paramsB, derivedB]);
  const statsB = useMemo(() => (comparisonMode && simB ? summarizeStats(paramsB, derivedB, simB.riskPerPath) : null), [comparisonMode, simB, paramsB, derivedB]);

  // Merge chart data for comparison display
  const combinedChartData = useMemo(() => {
    if (!comparisonMode || !simB) return simA.chartData; // single mode
    const maxLen = Math.max(simA.chartData.length, simB.chartData.length);
    const merged: Array<Record<string, number>> = [];
    for (let i = 0; i < maxLen; i++) {
      const row: Record<string, number> = { trade: i } as any;
      const aRow = simA.chartData[i] || simA.chartData[simA.chartData.length - 1];
      const bRow = simB.chartData[i] || simB.chartData[simB.chartData.length - 1];
      // copy A paths with A prefix when comparing
      for (let p = 0; p < paramsA.numPaths; p++) {
        row[`pathA${p + 1}`] = aRow[`path${p + 1}`];
      }
      for (let p = 0; p < paramsB.numPaths; p++) {
        row[`pathB${p + 1}`] = bRow[`path${p + 1}`];
      }
      merged.push(row);
    }
    return merged;
  }, [comparisonMode, simA, simB, paramsA.numPaths, paramsB?.numPaths]);

  const probabilityDataA = useMemo(
    () => [
      { name: "Max Loss", value: derivedA.probabilities.p1, color: "#dc2626" },
      { name: "Half Loss", value: derivedA.probabilities.p2, color: "#f97316" },
      { name: "Breakeven", value: derivedA.probabilities.p3, color: "#6b7280" },
      { name: "Half Gain", value: derivedA.probabilities.p4, color: "#22c55e" },
      { name: "Max Gain", value: derivedA.probabilities.p5, color: "#16a34a" },
      { name: "Extended Gain", value: derivedA.probabilities.p6, color: "#15803d" },
    ],
    [derivedA]
  );

  const probabilityDataB = useMemo(
    () =>
      comparisonMode && derivedB
        ? [
            { name: "Max Loss", value: derivedB.probabilities.p1, color: "#dc2626" },
            { name: "Half Loss", value: derivedB.probabilities.p2, color: "#f97316" },
            { name: "Breakeven", value: derivedB.probabilities.p3, color: "#6b7280" },
            { name: "Half Gain", value: derivedB.probabilities.p4, color: "#22c55e" },
            { name: "Max Gain", value: derivedB.probabilities.p5, color: "#16a34a" },
            { name: "Extended Gain", value: derivedB.probabilities.p6, color: "#15803d" },
          ]
        : null,
    [comparisonMode, derivedB]
  );

  const updateParamA = (key: keyof Params, value: number) => setParamsA((p) => ({ ...p, [key]: value }));
  const updateParamB = (key: keyof Params, value: number) => setParamsB((p) => ({ ...p, [key]: value }));

  return (
    <div className="w-full max-w-7xl mx-auto p-6 bg-white">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Equity Curve Experiment Dashboard</h1>
        <p className="text-gray-600 mb-4">Interactive exploration of how trading parameters affect equity curves</p>
        <div className="flex items-center gap-4">
          <label className="flex items-center cursor-pointer">
            <input type="checkbox" checked={!!comparisonMode} onChange={(e) => setComparisonMode(e.target.checked)} className="mr-2" />
            <span className="font-medium">Comparison Mode</span>
          </label>
          {comparisonMode && <span className="text-sm text-gray-500">Compare two different parameter sets side by side</span>}
        </div>
      </div>

      {/* Controls Panel */}
      <div className="space-y-6 mb-8">
        <div className="border rounded-lg p-4">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">{comparisonMode ? "Strategy A" : "Strategy Parameters"}</h2>
          <ParameterControls params={paramsA} derived={derivedA} updateParam={updateParamA} colorScheme="blue" />
        </div>
        {comparisonMode && (
          <div className="border rounded-lg p-4 bg-orange-50">
            <h2 className="text-xl font-semibold text-orange-900 mb-4">Strategy B</h2>
            <ParameterControls params={paramsB} derived={derivedB} updateParam={updateParamB} colorScheme="orange" />
          </div>
        )}
      </div>

      {/* Key Metrics Bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricCard title="Expected Δ per Trade" value={`${(derivedA.expectedDelta * 100).toFixed(3)}%`} valueB={comparisonMode && derivedB ? `${(derivedB.expectedDelta * 100).toFixed(3)}%` : null} colorScheme="blue" />
        <MetricCard title="Geometric Growth" value={`${(derivedA.expectedGeometric * 100).toFixed(3)}%`} valueB={comparisonMode && derivedB ? `${(derivedB.expectedGeometric * 100).toFixed(3)}%` : null} colorScheme="green" />
        <MetricCard title="Mean Final Equity" value={`${Math.round(statsA.meanFinalEquity).toLocaleString()}`} valueB={comparisonMode && statsB ? `${Math.round(statsB.meanFinalEquity).toLocaleString()}` : null} colorScheme="purple" />
        <MetricCard title="Total Return" value={`${statsA.meanReturn.toFixed(1)}%`} valueB={comparisonMode && statsB ? `${statsB.meanReturn.toFixed(1)}%` : null} colorScheme="yellow" />
      </div>

      {/* Risk Metrics Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <RiskMetricsPanel title={comparisonMode ? "Risk Metrics - Strategy A" : "Risk Metrics"} stats={statsA} colorScheme="red" />
        {comparisonMode && statsB && <RiskMetricsPanel title="Risk Metrics - Strategy B" stats={statsB} colorScheme="orange" />}
        {comparisonMode && statsB && <ComparisonPanel statsA={statsA} statsB={statsB} />}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Equity Curves */}
        <div className="lg:col-span-2 bg-white p-4 rounded-lg border">
          <h3 className="font-semibold text-gray-900 mb-4">Equity Curves</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={combinedChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="trade" />
                <YAxis />
                <Tooltip formatter={(value: any, name: any) => [`${Math.round(Number(value)).toLocaleString()}`, name]} />
                <ReferenceLine y={paramsA.E0} stroke="#666" strokeDasharray="2 2" />
                {/* Strategy A */}
                {!comparisonMode &&
                  Array.from({ length: paramsA.numPaths }, (_, i) => (
                    <Line key={`a${i}`} type="monotone" dataKey={`path${i + 1}`} stroke="#3b82f6" strokeWidth={1.5} dot={false} />
                  ))}
                {comparisonMode &&
                  Array.from({ length: paramsA.numPaths }, (_, i) => (
                    <Line key={`aa${i}`} type="monotone" dataKey={`pathA${i + 1}`} stroke="#3b82f6" strokeWidth={1.5} dot={false} opacity={0.8} />
                  ))}
                {comparisonMode &&
                  Array.from({ length: paramsB.numPaths }, (_, i) => (
                    <Line key={`bb${i}`} type="monotone" dataKey={`pathB${i + 1}`} stroke="#f97316" strokeWidth={1.5} dot={false} opacity={0.8} />
                  ))}
                {comparisonMode && <Legend />}
              </LineChart>
            </ResponsiveContainer>
          </div>
          {comparisonMode && (
            <div className="flex justify-center gap-4 mt-2 text-sm">
              <span className="flex items-center gap-1">
                <div className="w-3 h-3 bg-blue-500 rounded" /> Strategy A
              </span>
              <span className="flex items-center gap-1">
                <div className="w-3 h-3 bg-orange-500 rounded" /> Strategy B
              </span>
            </div>
          )}
        </div>

        {/* Probability Distribution (A) */}
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="font-semibold text-gray-900 mb-4">{comparisonMode ? "Strategy A - Outcome Probabilities" : "Outcome Probabilities"}</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={probabilityDataA} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, value }) => `${name}: ${(Number(value) * 100).toFixed(1)}%`}>
                  {probabilityDataA.map((entry, idx) => (
                    <Cell key={`cell-a-${idx}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value: any) => `${(Number(value) * 100).toFixed(2)}%`} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Strategy B Probability + Final Equity Comparison */}
      {comparisonMode && probabilityDataB && statsB && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="bg-white p-4 rounded-lg border">
            <h3 className="font-semibold text-gray-900 mb-4">Strategy B - Outcome Probabilities</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={probabilityDataB} cx="50%" cy="50%" outerRadius={70} dataKey="value" label={({ name, value }) => `${name}: ${(Number(value) * 100).toFixed(1)}%`}>
                    {probabilityDataB.map((entry, idx) => (
                      <Cell key={`cell-b-${idx}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value: any) => `${(Number(value) * 100).toFixed(2)}%`} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="lg:col-span-2 bg-white p-4 rounded-lg border">
            <h3 className="font-semibold text-gray-900 mb-4">Final Equity Distribution Comparison</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={[
                    { metric: "Mean Final Equity", StrategyA: Math.round(statsA.meanFinalEquity), StrategyB: Math.round(statsB.meanFinalEquity) },
                    { metric: "Min Final Equity", StrategyA: Math.round(statsA.minFinalEquity), StrategyB: Math.round(statsB.minFinalEquity) },
                    { metric: "Max Final Equity", StrategyA: Math.round(statsA.maxFinalEquity), StrategyB: Math.round(statsB.maxFinalEquity) },
                  ]}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="metric" />
                  <YAxis />
                  <Tooltip formatter={(value: any) => `${Number(value).toLocaleString()}`} />
                  <Bar dataKey="StrategyA" fill="#3b82f6" />
                  <Bar dataKey="StrategyB" fill="#f97316" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      )}

      {/* Final Equity Distribution (single strategy mode) */}
      {!comparisonMode && (
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="font-semibold text-gray-900 mb-4">Final Equity Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={simA.riskPerPath.map((rm, i) => ({ path: `Path ${i + 1}`, equity: Math.round(rm.finalEquity), ret: rm.totalReturn }))}
              >
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="path" />
                <YAxis />
                <Tooltip formatter={(value: any, name: any) => [name === "equity" ? `${Number(value).toLocaleString()}` : `${Number(value).toFixed(1)}%`, name === "equity" ? "Final Equity" : "Return"]} />
                <Bar dataKey="equity" fill="#3b82f6" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

export default EquityCurveDashboard;
