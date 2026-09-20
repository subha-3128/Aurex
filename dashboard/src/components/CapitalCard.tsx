import type { BrokerStatus } from '../types';
import { 
  Shield, 
  Lock, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle,
  Wallet,
  DollarSign
} from 'lucide-react';

interface StatusLike {
  capital?:      number;
  equity?:       number;
  total_equity?: number;
  trade_count?:  number;
  regime?:       string;
  auto_running?: boolean;
  daily_pnl?:    number;
}

interface Props {
  status:       StatusLike | null;
  brokerStatus: BrokerStatus | null;
}

export default function CapitalCard({ status, brokerStatus }: Props) {
  const equity     = status?.total_equity ?? status?.equity ?? status?.capital ?? 50.0;
  const isLive     = !brokerStatus?.sandbox;
  const freeUsdt   = brokerStatus?.free_usdt ?? 0;
  const freeBtc    = brokerStatus?.free_btc ?? 0;
  const connected  = brokerStatus?.success ?? false;
  const maxCap     = brokerStatus?.max_allocated_capital ?? 50.0;
  const minNotional = brokerStatus?.min_notional ?? 10.0;

  return (
    <div className="pro-card">
      <div className="pro-card-header">
        <div className="pro-card-title">
          <Shield size={15} className="pro-card-title-icon" />
          <span>Capital & Risk Shield Diagnostics</span>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          {connected ? (
            <span className="status-pill status-pill--active">
              <CheckCircle2 size={10} />
              Binance Live
            </span>
          ) : (
            <span className="status-pill status-pill--dead">
              <XCircle size={10} />
              Disconnected
            </span>
          )}
          {isLive ? (
            <span className="live-badge-pro live-badge-pro--real" style={{ fontSize: 9, padding: '2px 7px' }}>
              REAL MONEY
            </span>
          ) : (
            <span className="live-badge-pro live-badge-pro--test" style={{ fontSize: 9, padding: '2px 7px' }}>
              TESTNET
            </span>
          )}
        </div>
      </div>

      <div className="pro-card-body">
        {/* Balance Matrix */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginBottom: 14 }}>
          <div className="agent-stat-tile" style={{ padding: '10px 12px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <Wallet size={10} /> Portfolio Equity
            </label>
            <span style={{ fontSize: 18, color: 'var(--text-primary)', fontWeight: 700 }}>
              ${equity.toFixed(2)}
            </span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Reference Base</span>
          </div>

          <div className="agent-stat-tile" style={{ padding: '10px 12px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <DollarSign size={10} /> Binance Free USDT
            </label>
            <span style={{ fontSize: 18, color: freeUsdt > 0 ? 'var(--color-profit)' : 'var(--text-secondary)', fontWeight: 700 }}>
              ${freeUsdt.toFixed(2)}
            </span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Available Wallet</span>
          </div>

          <div className="agent-stat-tile" style={{ padding: '10px 12px' }}>
            <label>Binance Free BTC</label>
            <span style={{ fontSize: 16, color: 'var(--text-primary)', fontWeight: 700 }}>
              {freeBtc.toFixed(6)}
            </span>
            <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Spot Balance</span>
          </div>
        </div>

        {/* 4-Agent Capital Allocation Pool Bar */}
        <div style={{ background: 'var(--bg-elevated)', borderRadius: 'var(--radius-sm)', padding: '10px 12px', border: '1px solid var(--border)', marginBottom: 14 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 5 }}>
            <span style={{ color: 'var(--text-muted)' }}>Active Capital Pool ($50.00 Limit)</span>
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)', fontWeight: 600 }}>
              $12.50 / agent (4 Models)
            </span>
          </div>
          <div style={{ display: 'flex', height: 6, borderRadius: 3, overflow: 'hidden', gap: 2 }}>
            <div style={{ flex: 1, background: 'var(--accent-ai)', borderRadius: '3px 0 0 3px' }} title="Quant ($12.50)" />
            <div style={{ flex: 1, background: 'var(--color-hold)' }} title="Sentiment ($12.50)" />
            <div style={{ flex: 1, background: 'var(--color-profit)' }} title="Foundation ($12.50)" />
            <div style={{ flex: 1, background: 'var(--color-warning)', borderRadius: '0 3px 3px 0' }} title="Master ($12.50)" />
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 9, color: 'var(--text-muted)', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: 'var(--accent-ai)' }}>QUANT</span>
            <span style={{ color: 'var(--color-hold)' }}>SENTIMENT</span>
            <span style={{ color: 'var(--color-profit)' }}>FOUNDATION</span>
            <span style={{ color: 'var(--color-warning)' }}>MASTER</span>
          </div>
        </div>

        {/* Deterministic Risk Shield Diagnostics */}
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: 8 }}>
            <Lock size={11} color="var(--color-profit)" />
            <span>Deterministic Risk Shield Enforcements</span>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 6 }}>
            <div className="agent-stat-tile">
              <label>Min Notional Gate</label>
              <span style={{ color: 'var(--color-profit)' }}>${minNotional.toFixed(2)} USD</span>
            </div>
            <div className="agent-stat-tile">
              <label>Max Capital Cap</label>
              <span>${maxCap.toFixed(2)} USD</span>
            </div>
            <div className="agent-stat-tile">
              <label>Daily Drawdown Breaker</label>
              <span style={{ color: 'var(--color-warning)' }}>4.0% Max Loss</span>
            </div>
            <div className="agent-stat-tile">
              <label>Taker Fee / Slippage</label>
              <span>0.10% / 0.05%</span>
            </div>
          </div>
        </div>

        {/* Funding Notice if 0 USDT */}
        {freeUsdt === 0 && (
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 8, 
            marginTop: 12, 
            padding: '8px 12px', 
            borderRadius: 'var(--radius-sm)', 
            background: 'var(--color-warning-subtle)',
            border: '1px solid var(--color-warning-border)',
            fontSize: 11,
            color: 'var(--color-warning)'
          }}>
            <AlertTriangle size={14} style={{ flexShrink: 0 }} />
            <span>
              Your Binance Spot wallet currently has $0.00 USDT. Transfer USDT to your Spot account to allow active agents to execute orders up to your $50 cap.
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
