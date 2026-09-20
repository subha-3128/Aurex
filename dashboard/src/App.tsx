import { useState, useEffect, useRef } from 'react';
import { useAgent } from './useAgent';
import AgentsCard from './components/AgentsCard';
import ResearchCard from './components/ResearchCard';
import CapitalCard from './components/CapitalCard';
import SignalCard from './components/SignalCard';
import TradesTable from './components/TradesTable';
import EquityChart from './components/EquityChart';
import {
  Cpu,
  Layers,
  Globe,
  Shield,
  Clock,
  Play,
  Pause,
  Power,
  RefreshCw,
  Radio,
  AlertTriangle,
  Wallet
} from 'lucide-react';

type Tab = 'cockpit' | 'agents' | 'research' | 'capital' | 'trades';

export default function App() {
  const {
    status, agents, trades, research, brokerStatus,
    loading, refreshing, error, lastUpdated,
    fetchAll, emergencyStop, toggleAuto,
  } = useAgent();

  const [tab, setTab] = useState<Tab>('cockpit');

  // Track price ticks for color flash animation
  const [priceFlash, setPriceFlash] = useState<'up' | 'down' | null>(null);
  const prevPriceRef = useRef<number | null>(null);

  const latestPrice = status?.latest_price ?? 0;

  useEffect(() => {
    if (prevPriceRef.current !== null && latestPrice !== 0) {
      if (latestPrice > prevPriceRef.current) {
        setPriceFlash('up');
        const t = setTimeout(() => setPriceFlash(null), 1000);
        return () => clearTimeout(t);
      } else if (latestPrice < prevPriceRef.current) {
        setPriceFlash('down');
        const t = setTimeout(() => setPriceFlash(null), 1000);
        return () => clearTimeout(t);
      }
    }
    prevPriceRef.current = latestPrice;
  }, [latestPrice]);

  // Keyboard shortcuts (1-5 to switch tabs)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === '1') setTab('cockpit');
      if (e.key === '2') setTab('agents');
      if (e.key === '3') setTab('research');
      if (e.key === '4') setTab('capital');
      if (e.key === '5') setTab('trades');
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const isLive = !brokerStatus?.sandbox;
  const isRunning = status?.auto_running ?? false;
  const priceStr = latestPrice > 0
    ? `$${latestPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : '—';

  const totalPnL = agents.reduce((s, a) => s + (a.total_pnl || 0), 0);
  const activeCount = agents.filter(a => a.status === 'ACTIVE').length;

  const statusForCapital = status ? {
    ...status,
    capital:      status.total_equity,
    equity:       status.total_equity,
    total_equity: status.total_equity,
    trade_count:  agents.reduce((s, a) => s + (a.trade_count || 0), 0),
    daily_pnl:    totalPnL,
    regime:       status.regime,
    auto_running: status.auto_running,
  } : null;

  return (
    <div className="app">
      {/* ── Command Deck (Header) ────────────────────────────────────────── */}
      <header className="command-deck">
        {/* Brand Monogram */}
        <div className="brand-section">
          <div className="brand-logo-hex">
            <Cpu size={18} />
          </div>
          <div className="brand-info">
            <div className="brand-title">
              AEGIS // QUANTUM
              <span className="brand-version">PRO</span>
            </div>
            <div className="brand-subtitle">
              Autonomous Multi-Agent Spot Engine · Binance Live
            </div>
          </div>
        </div>

        {/* Telemetry Strip (Center) */}
        <div className="telemetry-strip">
          {/* Execution Mode */}
          {isLive ? (
            <span className="live-badge-pro live-badge-pro--real">
              <span className="radar-dot" />
              LIVE REAL MONEY
            </span>
          ) : (
            <span className="live-badge-pro live-badge-pro--test">
              TESTNET SIMULATION
            </span>
          )}

          <div className="telemetry-divider" />

          {/* BTC Price with tick flash */}
          <div className="ticker-box">
            <span className="ticker-pair">BTC/USDT</span>
            <span className={`ticker-price ${priceFlash === 'up' ? 'ticker-price--up' : priceFlash === 'down' ? 'ticker-price--down' : ''}`}>
              {priceStr}
            </span>
          </div>

          <div className="telemetry-divider" />

          {/* Regime Pill */}
          {status?.regime && (
            <span className={`pill-regime ${status.regime.includes('BULL') ? 'pill-regime--bull' : status.regime.includes('BEAR') ? 'pill-regime--bear' : ''}`}>
              {status.regime}
            </span>
          )}

          <div className="telemetry-divider" />

          {/* Active Agents & PnL */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 11, paddingRight: 2 }}>
            <span style={{ color: 'var(--text-muted)' }}>
              Models: <strong style={{ color: 'var(--text-primary)' }}>{activeCount}/4</strong>
            </span>
            <span style={{ 
              fontWeight: 600, 
              fontFamily: 'var(--font-mono)', 
              color: totalPnL >= 0 ? 'var(--color-profit)' : 'var(--color-loss)' 
            }}>
              {totalPnL >= 0 ? '+' : ''}${totalPnL.toFixed(2)}
            </span>
          </div>
        </div>

        {/* Control Deck (Right) */}
        <div className="deck-controls">
          <button
            id="btn-toggle-auto"
            className={`btn-deck ${isRunning ? 'btn-deck-toggle--running' : 'btn-deck-toggle--paused'}`}
            onClick={() => toggleAuto()}
            title={isRunning ? 'Pause 24/7 autonomous loop' : 'Start 24/7 autonomous loop'}
          >
            {isRunning ? <Pause size={12} /> : <Play size={12} />}
            <span>{isRunning ? 'Pause Engine' : 'Resume 24/7'}</span>
          </button>

          <button
            id="btn-emergency-stop"
            className="btn-deck btn-deck-danger"
            onClick={() => emergencyStop()}
            title="Immediate emergency kill switch — cancel orders and halt loop"
          >
            <Power size={12} />
            <span>Kill Switch</span>
          </button>

          <button
            id="btn-refresh"
            className={`btn-deck btn-deck-ghost ${refreshing ? 'spin' : ''}`}
            onClick={() => fetchAll(true)}
            title="Manual sync with agents and Binance"
          >
            <RefreshCw size={12} />
          </button>

          {lastUpdated && (
            <span className="deck-timestamp">
              {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </header>

      {/* ── Error Banner ─────────────────────────────────────────────────────── */}
      {error && (
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '9px 14px',
          marginBottom: 12,
          borderRadius: 'var(--radius-sm)',
          background: 'var(--color-loss-subtle)',
          border: '1px solid var(--color-loss-border)',
          color: 'var(--color-loss)',
          fontSize: 12
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <AlertTriangle size={14} />
            <span>{error}</span>
          </div>
          <button 
            className="btn-deck btn-deck-ghost" 
            style={{ padding: '2px 8px', fontSize: 11 }}
            onClick={() => fetchAll(true)}
          >
            Retry Connection
          </button>
        </div>
      )}

      {/* ── Pro Tab Navigation Bar ─────────────────────────────────────────── */}
      <nav className="pro-tab-bar">
        <div className="tab-group">
          {([
            { id: 'cockpit', label: 'Command Cockpit', icon: <Layers size={13} />, kbd: '1' },
            { id: 'agents',  label: 'AI Model Arena',  icon: <Cpu size={13} />,    kbd: '2', badge: `${activeCount}/4` },
            { id: 'research',label: 'Market Intel',     icon: <Globe size={13} />,  kbd: '3' },
            { id: 'capital', label: 'Capital & Risk',  icon: <Shield size={13} />, kbd: '4' },
            { id: 'trades',  label: 'Trade Ledger',    icon: <Clock size={13} />,  kbd: '5', badge: trades.length ? `${trades.length}` : undefined },
          ] as { id: Tab; label: string; icon: React.ReactNode; kbd: string; badge?: string }[]).map(t => (
            <button
              key={t.id}
              id={`tab-${t.id}`}
              className={`pro-tab-btn ${tab === t.id ? 'pro-tab-btn--active' : ''}`}
              onClick={() => setTab(t.id)}
            >
              {t.icon}
              <span>{t.label}</span>
              {t.badge && <span className="pro-tab-badge">{t.badge}</span>}
              <span className="pro-tab-kbd">{t.kbd}</span>
            </button>
          ))}
        </div>

        <div className="deck-meta-right">
          <div className="meta-stat-item">
            <Wallet size={12} />
            <span>Equity: <strong>${(status?.total_equity ?? 50).toFixed(2)}</strong></span>
          </div>
          <div className="meta-stat-item">
            <Radio size={12} />
            <span>Cycle: <strong>#{status?.cycle_count ?? 0}</strong></span>
          </div>
        </div>
      </nav>

      {/* ── Main Workspace ─────────────────────────────────────────────────── */}
      <main style={{ flex: 1 }}>
        {loading && (
          <div style={{ height: 320, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
            <div style={{
              width: 32, height: 32, borderRadius: '50%',
              border: '2px solid var(--border)',
              borderTopColor: 'var(--accent-ai)',
              animation: 'spin 0.8s linear infinite'
            }} />
            <span style={{ marginTop: 12, fontSize: 12, letterSpacing: '0.02em' }}>
              Synchronizing neural nodes and Binance stream...
            </span>
          </div>
        )}

        {/* ── 1. COCKPIT TAB (Master Overview) ─────────────────────────────── */}
        {tab === 'cockpit' && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {/* Top Row: AI Model Arena */}
            <AgentsCard agents={agents} />

            {/* Split Row: Intelligence & Risk Shield */}
            <div className="grid-cockpit">
              <ResearchCard research={research} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {statusForCapital && (
                  <CapitalCard status={statusForCapital as any} brokerStatus={brokerStatus} />
                )}
                <SignalCard status={statusForCapital as any} />
              </div>
            </div>

            {/* Bottom Row: Cumulative Performance & Recent Executions */}
            <div className="grid-2col">
              <EquityChart trades={trades as any} />
              <TradesTable trades={trades as any} />
            </div>
          </div>
        )}

        {/* ── 2. AI MODEL ARENA TAB ────────────────────────────────────────── */}
        {tab === 'agents' && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <AgentsCard agents={agents} />
            <div className="grid-2col">
              {statusForCapital && (
                <CapitalCard status={statusForCapital as any} brokerStatus={brokerStatus} />
              )}
              <SignalCard status={statusForCapital as any} />
            </div>
          </div>
        )}

        {/* ── 3. MARKET INTELLIGENCE TAB ──────────────────────────────────── */}
        {tab === 'research' && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <ResearchCard research={research} />
            <div className="grid-2col">
              <SignalCard status={statusForCapital as any} />
              {statusForCapital && (
                <CapitalCard status={statusForCapital as any} brokerStatus={brokerStatus} />
              )}
            </div>
          </div>
        )}

        {/* ── 4. CAPITAL & RISK TAB ───────────────────────────────────────── */}
        {tab === 'capital' && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {statusForCapital && (
              <CapitalCard status={statusForCapital as any} brokerStatus={brokerStatus} />
            )}
            <EquityChart trades={trades as any} />
          </div>
        )}

        {/* ── 5. TRADE LEDGER TAB ─────────────────────────────────────────── */}
        {tab === 'trades' && !loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <TradesTable trades={trades as any} />
            <EquityChart trades={trades as any} />
          </div>
        )}
      </main>

      {/* ── Footer ───────────────────────────────────────────────────────────── */}
      <footer className="terminal-footer">
        <div className="footer-tags">
          <span className="footer-pill">
            <span className="radar-dot" style={{ background: 'var(--color-profit)' }} />
            <span>AEGIS // QUANTUM SPOT ENGINE</span>
          </span>
          <span className="footer-pill">
            <span>Cycle #{status?.cycle_count ?? 0}</span>
          </span>
          <span className="footer-pill">
            <span>{isLive ? 'BINANCE LIVE (api.binance.com)' : 'TESTNET ENVIRONMENT'}</span>
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14, fontFamily: 'var(--font-mono)' }}>
          <span>PORTFOLIO: <strong>${(status?.total_equity ?? 50).toFixed(2)} USD</strong></span>
          <span>PRESS 1-5 TO SWITCH TABS</span>
        </div>
      </footer>
    </div>
  );
}
