import type { MarketResearch } from '../types';
import { 
  Globe, 
  Layers, 
  ExternalLink,
  Flame,
  Radio
} from 'lucide-react';

interface ResearchCardProps {
  research: MarketResearch | null;
}

/* ── Custom SVG Semicircular Radial Gauge ─────────────────────────────────── */
function FearGreedSpeedometer({ 
  score, 
  label,
  sentiment
}: { 
  score: number; 
  label: string;
  sentiment?: number;
}) {
  const clampedScore = Math.max(0, Math.min(100, score));

  // Determine semantic color according to dark palette tokens
  const getColor = (s: number) => {
    if (s <= 25) return '#FF4D5A'; // Extreme Fear / Loss
    if (s <= 45) return '#FFB020'; // Fear / Warning
    if (s <= 55) return '#8B8B93'; // Neutral / Hold
    return '#00C896';             // Greed / Profit
  };

  const activeColor = getColor(clampedScore);

  // SVG Geometry: Center (85, 82), Radius 58
  // Semicircle arc length = π * 58 ≈ 182.21
  const arcLength = 182.21;
  const strokeOffset = arcLength * (1 - clampedScore / 100);

  // Calculate orbital marker coordinates along the perimeter curve (never cuts through text)
  const rad = (clampedScore / 100) * Math.PI;
  const markerX = 85 - 58 * Math.cos(rad);
  const markerY = 82 - 58 * Math.sin(rad);

  // Contrarian interpretation telemetry (feeds into agent consensus logic)
  const effectiveSentiment = sentiment ?? (clampedScore > 55 ? -0.3 : clampedScore < 45 ? 0.3 : 0.0);
  const sentimentColor = effectiveSentiment > 0 
    ? 'var(--color-profit)' 
    : effectiveSentiment < 0 
    ? 'var(--color-loss)' 
    : 'var(--color-hold)';
    
  const stanceText = effectiveSentiment >= 0.8 ? 'Contrarian Strong Buy'
    : effectiveSentiment > 0 ? 'Contrarian Buy Lean'
    : effectiveSentiment <= -0.8 ? 'Contrarian Strong Sell'
    : effectiveSentiment < 0 ? 'Contrarian Sell Lean'
    : 'Neutral Consensus';

  return (
    <div className="fng-card-inner">
      {/* Top Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
          <Flame size={13} color="var(--color-warning)" />
          <span>Fear & Greed Index</span>
        </div>
        <span style={{ fontSize: 10, fontFamily: 'var(--font-mono)', color: activeColor, fontWeight: 600 }}>
          {clampedScore}/100
        </span>
      </div>

      {/* SVG Radial Arc (No colliding needle) */}
      <div className="fng-gauge-wrapper">
        <svg width="170" height="96" viewBox="0 0 170 96">
          <defs>
            <linearGradient id="fngTrackGradient" x1="0%" y1="100%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#FF4D5A" />
              <stop offset="35%" stopColor="#FFB020" />
              <stop offset="50%" stopColor="#8B8B93" />
              <stop offset="100%" stopColor="#00C896" />
            </linearGradient>
          </defs>

          {/* Background Reference Track */}
          <path
            d="M 27 82 A 58 58 0 0 1 143 82"
            fill="none"
            stroke="var(--border)"
            strokeWidth="7"
            strokeLinecap="round"
          />

          {/* Active Value Progress Arc */}
          <path
            d="M 27 82 A 58 58 0 0 1 143 82"
            fill="none"
            stroke={activeColor}
            strokeWidth="7"
            strokeLinecap="round"
            strokeDasharray={arcLength}
            strokeDashoffset={strokeOffset}
            style={{ transition: 'stroke-dashoffset 0.6s cubic-bezier(0.16, 1, 0.3, 1)' }}
          />

          {/* Orbital Marker Pip on Perimeter */}
          <circle cx={markerX} cy={markerY} r={7} fill={activeColor} opacity={0.25} />
          <circle cx={markerX} cy={markerY} r={4} fill="var(--bg-card)" stroke={activeColor} strokeWidth="2.5" />

          {/* Centered Clean Score Display */}
          <text 
            x="85" 
            y="62" 
            textAnchor="middle" 
            fill="var(--text-primary)" 
            fontSize="32" 
            fontWeight="800" 
            fontFamily="var(--font-mono)"
            letterSpacing="-0.02em"
          >
            {clampedScore}
          </text>

          {/* Centered Semantic Label */}
          <text 
            x="85" 
            y="78" 
            textAnchor="middle" 
            fill={activeColor} 
            fontSize="10" 
            fontWeight="700" 
            letterSpacing="0.08em" 
            fontFamily="var(--font-sans)"
          >
            {label.toUpperCase()}
          </text>

          {/* Range Endpoints */}
          <text x="27" y="94" textAnchor="middle" fill="var(--text-muted)" fontSize="9" fontFamily="var(--font-mono)">
            0
          </text>
          <text x="85" y="94" textAnchor="middle" fill="var(--text-muted)" fontSize="8" fontFamily="var(--font-sans)" letterSpacing="0.04em">
            50
          </text>
          <text x="143" y="94" textAnchor="middle" fill="var(--text-muted)" fontSize="9" fontFamily="var(--font-mono)">
            100
          </text>
        </svg>
      </div>

      {/* Contrarian Intelligence Telemetry Box */}
      <div className="fng-telemetry-box">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 3 }}>
          <span style={{ color: 'var(--text-muted)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Contrarian Signal</span>
          <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: 11, color: sentimentColor }}>
            {effectiveSentiment >= 0 ? '+' : ''}{effectiveSentiment.toFixed(2)}
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ color: 'var(--text-muted)', fontSize: 10 }}>Agent Interpretation</span>
          <span style={{ color: sentimentColor, fontWeight: 500, fontSize: 10 }}>
            {stanceText}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function ResearchCard({ research }: ResearchCardProps) {
  if (!research) {
    return (
      <div className="pro-card col-span-full">
        <div className="pro-card-header">
          <div className="pro-card-title">
            <Globe size={15} className="pro-card-title-icon" />
            <span>Market Intelligence</span>
          </div>
        </div>
        <div style={{ padding: 36, textAlign: 'center', color: 'var(--text-muted)' }}>
          <Radio size={20} className="spin" style={{ marginBottom: 10, opacity: 0.5 }} />
          <div>Synthesizing live market intelligence...</div>
        </div>
      </div>
    );
  }

  const fg = research.fear_greed || {};
  const cg = research.coingecko || {};
  const ob = research.orderbook || {};
  const news = research.news || {};

  const totalDepth = (ob.bid_volume || 0) + (ob.ask_volume || 0);
  const bidPct = totalDepth > 0 ? Math.round(((ob.bid_volume || 0) / totalDepth) * 100) : 50;
  const askPct = 100 - bidPct;

  const bestBid = ob.best_bid ?? 0;
  const bestAsk = ob.best_ask ?? 0;
  const spread = (bestAsk > 0 && bestBid > 0) ? Math.max(0, bestAsk - bestBid) : 0;
  const spreadPct = ob.spread_pct ?? 0;

  const momentum = cg.momentum ?? 0;
  const isMomBull = momentum >= 0;

  const headlines: string[] = news.headlines || [];
  const bullCount = news.bullish_count || 0;
  const bearCount = news.bearish_count || 0;
  const newsSentiment = news.news_sentiment ?? 0;

  return (
    <div className="pro-card col-span-full">
      <div className="pro-card-header">
        <div className="pro-card-title">
          <Globe size={15} className="pro-card-title-icon" />
          <span>Real-Time Internet Market Intelligence</span>
          <span className="brand-version" style={{ marginLeft: 8 }}>MULTI-SOURCE</span>
        </div>
        <span style={{ fontSize: 11, color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
          Synced {research.timestamp ? new Date(research.timestamp * 1000).toLocaleTimeString() : '—'}
        </span>
      </div>

      <div className="pro-card-body">
        {/* Top Intelligence Grid: Fear & Greed + Orderbook Depth */}
        <div className="research-grid-top">
          {/* 1. Fear & Greed Meter */}
          <FearGreedSpeedometer 
            score={fg.score ?? 50} 
            label={fg.label ?? 'Neutral'} 
            sentiment={fg.sentiment}
          />

          {/* 2. Binance Live Orderbook Depth Visualizer */}
          <div className="orderbook-panel">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                <Layers size={13} color="var(--accent-ai)" />
                <span>Binance Orderbook Liquidity Depth (Top 20)</span>
              </div>
              <span style={{ 
                fontSize: 11, 
                fontFamily: 'var(--font-mono)', 
                color: (ob.imbalance ?? 0) >= 0 ? 'var(--color-profit)' : 'var(--color-loss)', 
                fontWeight: 600 
              }}>
                Imbalance: {(ob.imbalance ?? 0) >= 0 ? '+' : ''}{(ob.imbalance || 0).toFixed(4)}
              </span>
            </div>

            {/* Split Depth Bar */}
            <div className="orderbook-split-bar">
              <div 
                className="orderbook-bid-side"
                style={{ width: `${bidPct}%` }}
              >
                {bidPct >= 15 && `BIDS ${bidPct}%`}
              </div>
              <div 
                className="orderbook-ask-side"
                style={{ width: `${askPct}%` }}
              >
                {askPct >= 15 && `ASKS ${askPct}%`}
              </div>
            </div>

            {/* Depth Volume Stats */}
            <div className="orderbook-stats-row">
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Bid Wall: </span>
                <strong style={{ color: 'var(--color-profit)', fontFamily: 'var(--font-mono)' }}>
                  {(ob.bid_volume || 0).toFixed(4)} BTC
                </strong>
                {bestBid > 0 && (
                  <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 6 }}>
                    (${bestBid.toLocaleString()})
                  </span>
                )}
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Ask Wall: </span>
                <strong style={{ color: 'var(--color-loss)', fontFamily: 'var(--font-mono)' }}>
                  {(ob.ask_volume || 0).toFixed(4)} BTC
                </strong>
                {bestAsk > 0 && (
                  <span style={{ fontSize: 10, color: 'var(--text-muted)', marginLeft: 6 }}>
                    (${bestAsk.toLocaleString()})
                  </span>
                )}
              </div>
            </div>

            {/* Micro Metrics Row: 4 Clean Stat Tiles */}
            <div className="orderbook-micro-grid">
              <div className="agent-stat-tile">
                <label>Best Spread</label>
                <span>${spread.toFixed(2)} ({spreadPct.toFixed(3)}%)</span>
              </div>
              <div className="agent-stat-tile">
                <label>CoinGecko 24h Chg</label>
                <span style={{ color: (cg.change_24h_pct ?? 0) >= 0 ? 'var(--color-profit)' : 'var(--color-loss)' }}>
                  {(cg.change_24h_pct ?? 0) >= 0 ? '+' : ''}{(cg.change_24h_pct ?? 0).toFixed(2)}%
                </span>
              </div>
              <div className="agent-stat-tile">
                <label>CoinGecko 24h Vol</label>
                <span>${((cg.volume_24h || 0) / 1e9).toFixed(2)}B</span>
              </div>
              <div className="agent-stat-tile">
                <label>CoinGecko Momentum</label>
                <span style={{ color: isMomBull ? 'var(--color-profit)' : 'var(--color-loss)' }}>
                  {isMomBull ? '+' : ''}{(momentum * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Section: Live Crypto News Terminal */}
        <div style={{ marginTop: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              <Globe size={13} color="var(--accent-ai)" />
              <span>Breaking Headlines & NLP Sentiment</span>
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 11 }}>
              <span style={{ color: 'var(--color-profit)', fontWeight: 600 }}>{bullCount} Bullish</span>
              <span style={{ color: 'var(--text-muted)' }}>·</span>
              <span style={{ color: 'var(--color-loss)', fontWeight: 600 }}>{bearCount} Bearish</span>
              <span style={{ color: 'var(--text-muted)' }}>·</span>
              <span style={{ 
                fontFamily: 'var(--font-mono)', 
                fontWeight: 600, 
                color: newsSentiment > 0 ? 'var(--color-profit)' : newsSentiment < 0 ? 'var(--color-loss)' : 'var(--text-muted)'
              }}>
                Net: {newsSentiment > 0 ? '+' : ''}{(newsSentiment * 100).toFixed(0)}%
              </span>
            </div>
          </div>

          <div className="news-terminal">
            {headlines.length === 0 ? (
              <div style={{ padding: 16, textAlign: 'center', color: 'var(--text-muted)', fontSize: 12 }}>
                Awaiting next live news ingestion cycle...
              </div>
            ) : (
              headlines.map((headline, idx) => {
                const lower = headline.toLowerCase();
                const isBull = ['surge', 'bull', 'rally', 'high', 'gain', 'up', 'rise', 'buy', 'breakout', 'record', 'pump', 'ath', 'jump', 'soar'].some(w => lower.includes(w));
                const isBear = ['crash', 'bear', 'drop', 'low', 'loss', 'down', 'fall', 'sell', 'dump', 'fear', 'decline', 'slump', 'tank'].some(w => lower.includes(w));

                return (
                  <a
                    key={idx}
                    href={`https://news.google.com/search?q=${encodeURIComponent(headline)}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="news-item-row"
                  >
                    <span className="news-headline-text">{headline}</span>
                    <span className={`news-tag ${
                      isBull ? 'news-tag--bullish' : isBear ? 'news-tag--bearish' : 'news-tag--neutral'
                    }`}>
                      {isBull ? 'BULLISH' : isBear ? 'BEARISH' : 'NEUTRAL'}
                    </span>
                    <ExternalLink size={12} className="news-link-icon" />
                  </a>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
