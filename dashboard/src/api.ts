import type { AgentState, SystemStatus, BrokerStatus, MarketResearch, AgentTrade } from './types';

const BASE = 'http://localhost:8000';

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST' });
  if (!res.ok) throw new Error(`${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  status:       () => get<SystemStatus>('/status'),
  agents:       () => get<AgentState[]>('/agents'),
  agentTrades:  (id: string) => get<AgentTrade[]>(`/agents/${id}/trades`),
  trades:       () => get<AgentTrade[]>('/trades'),
  research:     () => get<MarketResearch>('/research'),
  brokerStatus: () => get<BrokerStatus>('/broker/status'),
  cycle:        () => get<Record<string, unknown>>('/cycle'),

  emergencyStop: () => post<{ stopped: boolean }>('/emergency-stop'),
  clearStop:     () => post<{ cleared: boolean }>('/clear-stop'),
  toggleAuto:    () => post<{ auto_running: boolean }>('/auto-toggle'),
};
