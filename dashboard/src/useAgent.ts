// Central data hook — polls all API endpoints for the multi-agent system
import { useState, useEffect, useCallback, useRef } from 'react';
import type { SystemStatus, AgentState, AgentTrade, BrokerStatus, MarketResearch } from './types';
import { api } from './api';

const POLL_MS = 8_000;

export function useAgent() {
  const [status,       setStatus]       = useState<SystemStatus | null>(null);
  const [agents,       setAgents]       = useState<AgentState[]>([]);
  const [trades,       setTrades]       = useState<AgentTrade[]>([]);
  const [research,     setResearch]     = useState<MarketResearch | null>(null);
  const [brokerStatus, setBrokerStatus] = useState<BrokerStatus | null>(null);
  const [loading,      setLoading]      = useState(true);
  const [refreshing,   setRefreshing]   = useState(false);
  const [error,        setError]        = useState<string | null>(null);
  const [lastUpdated,  setLastUpdated]  = useState<Date | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchAll = useCallback(async (manual = false) => {
    if (manual) setRefreshing(true);
    try {
      const [sRes, aRes, tRes, rRes, bRes] = await Promise.all([
        api.status().catch(() => null),
        api.agents().catch(() => []),
        api.trades().catch(() => []),
        api.research().catch(() => null),
        api.brokerStatus().catch(() => null),
      ]);
      if (sRes) setStatus(sRes);
      setAgents(aRes as AgentState[]);
      setTrades(tRes as AgentTrade[]);
      if (rRes) setResearch(rRes as MarketResearch);
      if (bRes) setBrokerStatus(bRes as BrokerStatus);
      setError(null);
      setLastUpdated(new Date());
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'API error';
      setError(msg + ' — is the backend running on :8000?');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  const emergencyStop = useCallback(async () => {
    await api.emergencyStop();
    fetchAll(true);
  }, [fetchAll]);

  const clearStop = useCallback(async () => {
    await api.clearStop();
    fetchAll(true);
  }, [fetchAll]);

  const toggleAuto = useCallback(async () => {
    await api.toggleAuto();
    fetchAll(true);
  }, [fetchAll]);

  useEffect(() => {
    fetchAll();
    timerRef.current = setInterval(() => fetchAll(), POLL_MS);
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [fetchAll]);

  return {
    status,
    agents,
    trades,
    research,
    brokerStatus,
    loading,
    refreshing,
    error,
    lastUpdated,
    fetchAll,
    emergencyStop,
    clearStop,
    toggleAuto,
  };
}
