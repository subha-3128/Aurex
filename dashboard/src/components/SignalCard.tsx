import { 
  Radio, 
  TrendingUp, 
  TrendingDown, 
  Minus 
} from 'lucide-react';

interface Props {
  status: Record<string, any> | null;
}

export default function SignalCard({ status }: Props) {
  if (!status) {
    return (
      <div className="pro-card">
        <div className="pro-card-header">
          <div className="pro-card-title">
            <Radio size={15} className="pro-card-title-icon" />
            <span>Market Signal</span>
          </div>
        </div>
        <div style={{ padding: 20, color: 'var(--text-muted)', textAlign: 'center' }}>
          Awaiting telemetry...
        </div>
      </div>
    );
  }

  const signal = status.signal ?? 'HOLD';
  const regime = status.regime ?? 'LOW_VOL';
  const price = status.latest_price ?? status.price ?? 0;
  const cycles = status.cycle_count ?? 0;
  const running = status.auto_running ?? false;

  const isRegimeBull = regime.includes('BULL');
  const isRegimeBear = regime.includes('BEAR');

  return (
    <div className="pro-card">
      <div className="pro-card-header">
        <div className="pro-card-title">
          <Radio size={15} className="pro-card-title-icon" />
          <span>Autonomous Consensus Telemetry</span>
        </div>
        <span className={`status-pill ${running ? 'status-pill--active' : 'status-pill--degraded'}`}>
          <span className="radar-dot" />
          {running ? 'AUTONOMOUS 24/7' : 'PAUSED'}
        </span>
      </div>

      <div className="pro-card-body">
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {/* Regime */}
          <div className="agent-stat-tile" style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: '9px 12px' }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Market Regime
            </span>
            <span className={`pill-regime ${isRegimeBull ? 'pill-regime--bull' : isRegimeBear ? 'pill-regime--bear' : ''}`}>
              {regime}
            </span>
          </div>

          {/* Consensus Signal */}
          <div className="agent-stat-tile" style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: '9px 12px' }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Consensus Stance
            </span>
            <span className={`decision-action-badge ${
              signal === 'BUY' ? 'decision-action-badge--buy' :
              signal === 'SELL' ? 'decision-action-badge--sell' : 'decision-action-badge--hold'
            }`}>
              {signal === 'BUY' && <TrendingUp size={11} />}
              {signal === 'SELL' && <TrendingDown size={11} />}
              {signal === 'HOLD' && <Minus size={11} />}
              {signal}
            </span>
          </div>

          {/* Live BTC Price */}
          <div className="agent-stat-tile" style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: '9px 12px' }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              BTC Spot Price
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, fontSize: 17, color: 'var(--text-primary)' }}>
              ${price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </span>
          </div>

          {/* Cycles Counter */}
          <div className="agent-stat-tile" style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', padding: '9px 12px' }}>
            <span style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              Total Cycles Run
            </span>
            <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: 13, color: 'var(--text-secondary)' }}>
              #{cycles}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
