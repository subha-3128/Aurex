import { useState } from 'react';
import { 
  Clock, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  Filter,
  Radio
} from 'lucide-react';

interface Props {
  trades: Record<string, any>[];
}

function formatTimestamp(ts: number): string {
  return new Date(ts).toLocaleString(undefined, {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}

const AGENT_COLORS: Record<string, string> = {
  agent_quant: '#00B8D9',
  agent_sentiment: '#8B8B93',
  agent_foundation: '#00C896',
  agent_master: '#FFB020',
};

export default function TradesTable({ trades }: Props) {
  const [selectedAgent, setSelectedAgent] = useState<string>('ALL');

  const filteredTrades = selectedAgent === 'ALL'
    ? trades
    : trades.filter(t => (t.agent_id === selectedAgent || t.agent_name?.toLowerCase().includes(selectedAgent.toLowerCase())));

  return (
    <div className="pro-card col-span-full">
      <div className="pro-card-header">
        <div className="pro-card-title">
          <Clock size={15} className="pro-card-title-icon" />
          <span>Autonomous Trade Execution Ledger</span>
          <span className="brand-version" style={{ marginLeft: 8 }}>{trades.length} EXECUTIONS</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--text-muted)' }}>
          <Filter size={11} />
          <span>Real-Time Audit Trail</span>
        </div>
      </div>

      <div className="pro-card-body">
        {/* Filter Pills */}
        <div className="table-filter-bar">
          <button 
            className={`filter-pill-btn ${selectedAgent === 'ALL' ? 'filter-pill-btn--active' : ''}`}
            onClick={() => setSelectedAgent('ALL')}
          >
            All Models ({trades.length})
          </button>
          <button 
            className={`filter-pill-btn ${selectedAgent === 'agent_quant' ? 'filter-pill-btn--active' : ''}`}
            onClick={() => setSelectedAgent('agent_quant')}
            style={selectedAgent === 'agent_quant' ? { borderColor: 'var(--accent-ai)', color: 'var(--accent-ai)' } : {}}
          >
            Quant Analyst
          </button>
          <button 
            className={`filter-pill-btn ${selectedAgent === 'agent_sentiment' ? 'filter-pill-btn--active' : ''}`}
            onClick={() => setSelectedAgent('agent_sentiment')}
            style={selectedAgent === 'agent_sentiment' ? { borderColor: 'var(--color-hold)', color: 'var(--color-hold)' } : {}}
          >
            Sentiment Analyst
          </button>
          <button 
            className={`filter-pill-btn ${selectedAgent === 'agent_foundation' ? 'filter-pill-btn--active' : ''}`}
            onClick={() => setSelectedAgent('agent_foundation')}
            style={selectedAgent === 'agent_foundation' ? { borderColor: 'var(--color-profit)', color: 'var(--color-profit)' } : {}}
          >
            Foundation AI
          </button>
          <button 
            className={`filter-pill-btn ${selectedAgent === 'agent_master' ? 'filter-pill-btn--active' : ''}`}
            onClick={() => setSelectedAgent('agent_master')}
            style={selectedAgent === 'agent_master' ? { borderColor: 'var(--color-warning)', color: 'var(--color-warning)' } : {}}
          >
            Master Brain
          </button>
        </div>

        {/* Table Container */}
        {filteredTrades.length === 0 ? (
          <div style={{ 
            padding: '36px 20px', 
            textAlign: 'center', 
            borderRadius: 'var(--radius-sm)', 
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            color: 'var(--text-muted)'
          }}>
            <Radio size={24} style={{ opacity: 0.35, marginBottom: 8 }} />
            <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)' }}>
              No Trade Executions Recorded Yet
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4, maxWidth: 420, margin: '4px auto 0' }}>
              Models are monitoring market regime, orderbook depth, and sentiment. Trades will execute when confidence crosses the hurdle and Risk Shield permits.
            </div>
          </div>
        ) : (
          <div className="table-container-pro">
            <table className="table-pro">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Model</th>
                  <th>Action</th>
                  <th>Execution Price</th>
                  <th>Size</th>
                  <th>Net PnL</th>
                  <th>Reward Impact</th>
                  <th>Confidence</th>
                  <th>Market Regime</th>
                </tr>
              </thead>
              <tbody>
                {filteredTrades.map((t, idx) => {
                  const action = t.action ?? t.signal ?? 'HOLD';
                  const pnl = t.net_pnl ?? 0;
                  const rewardDelta = t.reward_delta ?? 0;
                  const agentColor = AGENT_COLORS[t.agent_id] || 'var(--accent-ai)';

                  return (
                    <tr key={t.id ?? idx}>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: 'var(--text-muted)' }}>
                        {formatTimestamp(t.timestamp)}
                      </td>
                      <td>
                        <span style={{ 
                          display: 'inline-flex', 
                          alignItems: 'center', 
                          gap: 6,
                          fontSize: 11, 
                          fontWeight: 600,
                          color: agentColor 
                        }}>
                          <span style={{ width: 5, height: 5, borderRadius: '50%', background: agentColor }} />
                          {t.agent_name ?? t.agent_id ?? 'AI Node'}
                        </span>
                      </td>
                      <td>
                        <span className={`decision-action-badge ${
                          action === 'BUY' ? 'decision-action-badge--buy' :
                          action === 'SELL' ? 'decision-action-badge--sell' : 'decision-action-badge--hold'
                        }`} style={{ fontSize: 10, padding: '1px 6px' }}>
                          {action === 'BUY' && <TrendingUp size={10} />}
                          {action === 'SELL' && <TrendingDown size={10} />}
                          {action === 'HOLD' && <Minus size={10} />}
                          {action}
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: 'var(--text-primary)' }}>
                        ${(t.exit_price || t.entry_price || t.price || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
                        ${(t.position_size || 0).toFixed(2)}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: pnl >= 0 ? 'var(--color-profit)' : 'var(--color-loss)' }}>
                        {pnl !== 0 ? `${pnl >= 0 ? '+' : ''}$${pnl.toFixed(4)}` : '—'}
                      </td>
                      <td>
                        <span style={{ 
                          fontFamily: 'var(--font-mono)', 
                          fontWeight: 600,
                          fontSize: 11,
                          color: rewardDelta >= 0 ? 'var(--color-profit)' : 'var(--color-loss)'
                        }}>
                          {rewardDelta >= 0 ? '+' : ''}{rewardDelta.toFixed(1)} pts
                        </span>
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)' }}>
                        {t.confidence ? `${(t.confidence * 100).toFixed(0)}%` : '—'}
                      </td>
                      <td>
                        <span className="pill-regime" style={{ fontSize: 9, padding: '1px 5px' }}>
                          {t.regime ?? 'LOW_VOL'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
