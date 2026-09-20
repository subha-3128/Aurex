// Cumulative PnL curve built from agent trade history
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { TrendingUp, Activity } from 'lucide-react';

interface Props {
  trades: Record<string, any>[];
  initialCapital?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const v = payload[0].value as number;
  return (
    <div style={{
      background: 'var(--bg-card)', 
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-sm)', 
      padding: '8px 12px', 
      fontSize: 12,
    }}>
      <div style={{ color: 'var(--text-muted)', fontSize: 10, marginBottom: 3, fontFamily: 'var(--font-mono)' }}>{label}</div>
      <div style={{ color: v >= 0 ? 'var(--color-profit)' : 'var(--color-loss)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
        {v >= 0 ? '+' : ''}${v.toFixed(4)} Cumulative PnL
      </div>
    </div>
  );
};

export function EquityChart({ trades, initialCapital: _ic = 50 }: Props) {
  const closedTrades = [...trades]
    .filter(t => t.action === 'SELL' && t.net_pnl != null)
    .sort((a, b) => a.timestamp - b.timestamp);

  let cumPnl = 0;
  const data = closedTrades.map(t => {
    cumPnl += (t.net_pnl ?? 0);
    return {
      time: new Date(t.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }),
      pnl: Math.round(cumPnl * 10000) / 10000,
    };
  });

  const latest = cumPnl;
  const isProfit = latest >= 0;
  const strokeColor = isProfit ? '#00C896' : '#FF4D5A';

  if (!data.length) {
    return (
      <div className="pro-card">
        <div className="pro-card-header">
          <div className="pro-card-title">
            <TrendingUp size={15} className="pro-card-title-icon" />
            <span>Cumulative Performance PnL Curve</span>
          </div>
        </div>
        <div style={{ height: 210, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
          <Activity size={22} style={{ opacity: 0.35, marginBottom: 8 }} />
          <span>No closed trades recorded yet. PnL trajectory will populate on first SELL execution.</span>
        </div>
      </div>
    );
  }

  return (
    <div className="pro-card">
      <div className="pro-card-header">
        <div className="pro-card-title">
          <TrendingUp size={15} className="pro-card-title-icon" />
          <span>Cumulative Performance PnL Curve</span>
        </div>
        <div style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: isProfit ? 'var(--color-profit)' : 'var(--color-loss)', fontSize: 15 }}>
          {isProfit ? '+' : ''}${latest.toFixed(4)} USD
        </div>
      </div>
      <div style={{ padding: '14px 18px 16px' }}>
        <ResponsiveContainer width="100%" height={210}>
          <AreaChart data={data} margin={{ top: 6, right: 6, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="pnlGradientPro" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor={strokeColor} stopOpacity={0.15} />
                <stop offset="95%" stopColor={strokeColor} stopOpacity={0.00} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="2 4" stroke="var(--border)" vertical={false} />
            <XAxis dataKey="time" tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickLine={false} axisLine={false} interval="preserveStartEnd" />
            <YAxis tick={{ fill: 'var(--text-muted)', fontSize: 10 }} tickLine={false} axisLine={false} tickFormatter={(v: number) => `$${v.toFixed(2)}`} domain={['auto', 'auto']} />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0} stroke="var(--border)" strokeDasharray="3 3" />
            <Area type="monotone" dataKey="pnl" stroke={strokeColor} strokeWidth={1.75} fill="url(#pnlGradientPro)" dot={false} activeDot={{ r: 4, fill: strokeColor, strokeWidth: 0 }} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default EquityChart;
