import { UCORE_BASE } from "@/api/base";

export interface RepairStep {
  kind: string;
  id: string;
  details: string;
  action: string;
}

export interface CapabilityPreflightResult {
  capability: string;
  ready: boolean;
  repair_required: boolean;
  status?: number;
  requirements_source?: string;
  repair: RepairStep[];
  error?: string;
}

export interface CapabilityReadinessSnapshot {
  ready: boolean;
  count: number;
  requirements_source?: string;
  capabilities: CapabilityPreflightResult[];
}

export interface RepairCardModel {
  title: string;
  detail: string;
  actionLabel: string;
  key: string;
}

export async function getCapabilityPreflight(
  capability: string,
  timeoutMs = 8000,
): Promise<CapabilityPreflightResult> {
  const res = await fetch(
    `${UCORE_BASE}/api/capabilities/${encodeURIComponent(capability)}/preflight`,
    { signal: AbortSignal.timeout(timeoutMs) },
  );

  let data: CapabilityPreflightResult | null = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }

  if (!data) {
    throw new Error(`Preflight returned invalid payload (HTTP ${res.status})`);
  }

  return data;
}

export async function ensureCapabilityReady(
  capability: string,
  timeoutMs = 8000,
): Promise<CapabilityPreflightResult> {
  const result = await getCapabilityPreflight(capability, timeoutMs);
  if (result.ready) return result;

  const reason = result.error || `Capability '${capability}' is not ready`;
  const e = new Error(reason) as Error & {
    preflight?: CapabilityPreflightResult;
  };
  e.preflight = result;
  throw e;
}

export function toRepairCards(
  result: CapabilityPreflightResult,
): RepairCardModel[] {
  return (result.repair || []).map((step) => ({
    key: `${step.kind}:${step.id}`,
    title: `${step.kind}: ${step.id}`,
    detail: step.details,
    actionLabel: step.action,
  }));
}

export async function getCapabilitiesReadiness(
  capabilities: string[] = [],
  timeoutMs = 10000,
): Promise<CapabilityReadinessSnapshot> {
  const params = new URLSearchParams();
  if (capabilities.length > 0) {
    params.set("capabilities", capabilities.join(","));
  }

  const qs = params.toString();
  const url = `${UCORE_BASE}/api/capabilities/readiness${qs ? `?${qs}` : ""}`;
  const res = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
  const data = await res.json();

  if (!data || !Array.isArray(data.capabilities)) {
    throw new Error(`Invalid readiness response (HTTP ${res.status})`);
  }

  return data as CapabilityReadinessSnapshot;
}
