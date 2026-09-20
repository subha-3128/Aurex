import { useState } from 'react';
import type { AgentState } from '../types';
import { 
  Activity, 
  Globe, 
  Zap, 
  Shield, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  ChevronDown, 
  ChevronUp, 
  AlertTriangle,
  Radio,
  Cpu
} from 'lucide-react';

interface AgentsCardProps {
  agents: AgentState[];
  onSelectAgent?: (agentId: string) => void;
}

interface AgentConfig {
  accentColor: string;
  avatarBg: string;
  icon: React.ReactNode;
  subtitle: string;
  focusMetrics: string[];
}

const AGENT_CONFIGS: Record<string, AgentConfig> = {
  agent_quant: {
    accentColor: '#00B8D9',
    avatarBg: 'rgba(0, 184, 217, 0.10)',
    icon: <Activity size={16} color="#00B8D9" />,
    subtitle: 'Quantitative & Orderbook Depth',
    focusMetrics: ['RSI-14', 'EMA 9/21', 'MACD', 'Depth Imbalance'],
  },
  agent_sentiment: {
    accentColor: '#8B8B93',
    avatarBg: 'rgba(139, 139, 147, 0.10)',
    icon: <Globe size={16} color="#8B8B93" />,
    subtitle: 'Social Sentiment & Macro News',
    focusMetrics: ['Fear & Greed', 'CoinGecko Momentum', 'News NLP'],
  },
  agent_foundation: {
    accentColor: '#00C896',
    avatarBg: 'rgba(0, 200, 150, 0.10)',
    icon: <Zap size={16} color="#00C896" />,
    subtitle: 'Chronos-Bolt + XGBoost Gating',
    focusMetrics: ['Zero-Shot Forecast', 'Triple Barrier', 'Meta-Labeler'],
  },
  agent_master: {
    accentColor: '#FFB020',
    avatarBg: 'rgba(255, 176, 32, 0.10)',
    icon: <Shield size={16} color="#FFB020" />,
    subtitle: 'Performance-Weighted Consensus',
    focusMetrics: ['Weighted Voting', 'Risk Allocation', 'Consensus Gate'],
  },
};

export default function AgentsCard({ agents }: AgentsCardProps) {
  const [expandedRationale, setExpandedRationale] = useState<Record<string, boolean>>({});

  const toggleRationale = (id: string) => {
    setExpandedRationale(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const activeCount = agents.filter(a => a.status === 'ACTIVE').length;
  const degradedCount = agents.filter(a => a.status === 'DEGRADED').length;
  const deadCount = agents.filter(a => a.status === 'DEAD').length;

  return (
    <div className="pro-card col-span-full">
      <div className="pro-card-header">
        <div className="pro-card-title">
          <Cpu size={15} className="pro-card-title-icon" />
          <span>Autonomous AI Agent Arena</span>
          <span className="brand-version" style={{ marginLeft: 8 }}>4 LIVE MODELS</span>
        </div>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <span className="status-pill status-pill--active">
            <span className="radar-dot" />
            {activeCount} Active
          </span>
          {degradedCount > 0 && (
            <span className="status-pill status-pill--degraded">
              <AlertTriangle size={10} />
              {degradedCount} Degraded
            </span>
          )}
          {deadCount > 0 && (
            <span className="status-pill status-pill--dead">
              {deadCount} Dead
            </span>
          )}
        </div>
      </div>

      <div className="pro-card-body">
        <div className="grid-arena">
          {agents.map(agent => {
            const config = AGENT_CONFIGS[agent.agent_id] || {
              accentColor: '#00B8D9',
              avatarBg: 'rgba(0, 184, 217, 0.10)',
              icon: <Radio size={16} />,
              subtitle: agent.description?.split('.')[0] || 'Autonomous Trading Node',
              focusMetrics: [],
            };

            const isDead = agent.status === 'DEAD';
            const isDegraded = agent.status === 'DEGRADED';
            const score = agent.reward_score ?? 0;
            const isPositive = score >= 0;

            const clampedScore = Math.max(-100, Math.min(100, score));
            const barWidthPct = (Math.abs(clampedScore) / 100) * 50;

            const action = agent.last_decision?.action ?? 'HOLD';
            const confidence = agent.last_decision?.confidence ?? agent.confidence_hurdle ?? 0.5;
            const rationale = agent.last_decision?.rationale;

            return (
              <div 
                key={agent.agent_id}
                className={`agent-node-card ${isDead ? 'agent-node-card--dead' : ''} ${isDegraded ? 'agent-node-card--degraded' : ''}`}
                style={{ borderLeft: `2px solid ${config.accentColor}` }}
              >
                {/* Header: Identity & Status */}
                <div className="agent-header-row">
                  <div className="agent-identity">
                    <div 
                      className="agent-avatar-badge" 
                      style={{ background: config.avatarBg, borderColor: 'var(--border)' }}
                    >
                      {config.icon}
                    </div>
                    <div className="agent-title-block">
                      <h3>
                        {agent.name}
                        {agent.has_position && (
                          <span style={{ 
                            fontSize: 9, 
                            fontWeight: 600, 
                            padding: '1px 5px', 
                            borderRadius: 3, 
                            background: 'var(--color-profit-subtle)', 
                            color: 'var(--color-profit)',
                            border: '1px solid var(--color-profit-border)'
                          }}>
                            IN POSITION
                          </span>
                        )}
                      </h3>
                      <p>{config.subtitle}</p>
                    </div>
                  </div>

                  {/* Status Pill */}
                  <div>
                    {agent.status === 'ACTIVE' && (
                      <span className="status-pill status-pill--active">
                        <span className="radar-dot" />
                        ACTIVE
                      </span>
                    )}
                    {agent.status === 'DEGRADED' && (
                      <span className="status-pill status-pill--degraded">
                        <AlertTriangle size={10} />
                        DEGRADED
                      </span>
                    )}
                    {agent.status === 'DEAD' && (
                      <span className="status-pill status-pill--dead">
                        DEAD
                      </span>
                    )}
                  </div>
                </div>

                {/* Decision Ribbon */}
                <div className="decision-ribbon">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span style={{ fontSize: 10, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                      Stance
                    </span>
                    <span className={`decision-action-badge ${
                      action === 'BUY' ? 'decision-action-badge--buy' :
                      action === 'SELL' ? 'decision-action-badge--sell' : 'decision-action-badge--hold'
                    }`}>
                      {action === 'BUY' && <TrendingUp size={11} />}
                      {action === 'SELL' && <TrendingDown size={11} />}
                      {action === 'HOLD' && <Minus size={11} />}
                      {action}
                    </span>
                  </div>

                  <div className="decision-confidence-box">
                    <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>Confidence</span>
                    <div className="confidence-bar-track">
                      <div 
                        className="confidence-bar-fill" 
                        style={{ 
                          width: `${Math.round(confidence * 100)}%`,
                          background: confidence >= agent.confidence_hurdle ? config.accentColor : 'var(--text-muted)'
                        }} 
                      />
                    </div>
                    <span className="confidence-val">
                      {(confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                {/* Reward & Punishment Ledger */}
                <div className="reward-ledger-box">
                  <div className="reward-ledger-header">
                    <span style={{ color: 'var(--text-muted)' }}>
                      Reward Score
                    </span>
                    <span 
                      className="reward-score-val"
                      style={{ color: isPositive ? 'var(--color-profit)' : 'var(--color-loss)' }}
                    >
                      {isPositive ? '+' : ''}{score.toFixed(1)} pts
                    </span>
                  </div>

                  <div className="reward-track-wrapper">
                    {/* Midpoint marker at 50% */}
                    <div className="reward-center-notch" />
                    
                    {/* Danger zone marker (-50 point line = 25% from left) */}
                    <div style={{ position: 'absolute', left: '25%', top: 0, bottom: 0, width: 1, background: 'var(--color-warning-border)' }} />
                    
                    {/* Bar */}
                    <div 
                      className="reward-fill-bar"
                      style={{
                        width: `${barWidthPct}%`,
                        left: isPositive ? '50%' : `${50 - barWidthPct}%`,
                        background: isPositive ? 'var(--color-profit)' : 'var(--color-loss)',
                      }}
                    />
                  </div>

                  <div className="reward-danger-zones">
                    <span style={{ color: 'var(--color-loss)' }}>-100 DEAD</span>
                    <span style={{ color: 'var(--color-warning)' }}>-50 DEGRADED</span>
                    <span style={{ color: 'var(--text-muted)' }}>0 BASE</span>
                    <span style={{ color: 'var(--color-profit)' }}>+100 ELITE</span>
                  </div>
                </div>

                {/* Financial Metrics Grid */}
                <div className="agent-stats-grid">
                  <div className="agent-stat-tile">
                    <label>Allocated</label>
                    <span>${agent.allocated_capital.toFixed(2)}</span>
                  </div>
                  <div className="agent-stat-tile">
                    <label>Available Cash</label>
                    <span style={{ color: agent.cash < 5 ? 'var(--color-loss)' : 'var(--text-primary)' }}>
                      ${agent.cash.toFixed(2)}
                    </span>
                  </div>
                  <div className="agent-stat-tile">
                    <label>Net PnL</label>
                    <span style={{ color: agent.total_pnl >= 0 ? 'var(--color-profit)' : 'var(--color-loss)' }}>
                      {agent.total_pnl >= 0 ? '+' : ''}${agent.total_pnl.toFixed(2)}
                    </span>
                  </div>
                </div>

                {/* Focus Strategy Tags */}
                <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                  {config.focusMetrics.map((m, i) => (
                    <span 
                      key={i} 
                      style={{ 
                        fontSize: 9, 
                        fontWeight: 500, 
                        color: 'var(--text-muted)', 
                        background: 'var(--bg-main)', 
                        border: '1px solid var(--border)',
                        padding: '1px 5px',
                        borderRadius: 3
                      }}
                    >
                      {m}
                    </span>
                  ))}
                  <span style={{ 
                    fontSize: 9, 
                    fontWeight: 600, 
                    color: config.accentColor, 
                    marginLeft: 'auto',
                    fontFamily: 'var(--font-mono)'
                  }}>
                    Hurdle: {(agent.confidence_hurdle * 100).toFixed(0)}%
                  </span>
                </div>

                {/* Collapsible Rationale Snippet */}
                {rationale && (
                  <div>
                    <div 
                      className="rationale-toggle"
                      onClick={() => toggleRationale(agent.agent_id)}
                    >
                      <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <Cpu size={12} color={config.accentColor} />
                        AI Decision Rationale
                      </span>
                      {expandedRationale[agent.agent_id] ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                    </div>
                    {expandedRationale[agent.agent_id] && (
                      <div className="rationale-content">
                        {rationale}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
