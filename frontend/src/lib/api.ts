/**
 * Typed fetch helpers for the tracker API.
 * All endpoints proxy through Vite's dev server; see vite.config.ts.
 */

export type RunStatus = 'running' | 'completed' | 'failed'

export interface RunSummary {
  run_id: string
  experiment: string
  name: string
  status: RunStatus
  started_at: string
  finished_at: string | null
  git_sha: string
  error: string
  params: Record<string, unknown>
  metrics: Record<string, number>
  tags: string[]
}

export interface RunDetail extends RunSummary {
  feature_importance: { feature: string; importance: number; rank: number }[]
  artifacts: { name: string; path: string; kind: string; size_bytes: number }[]
}

export interface Experiment {
  experiment_id: number
  name: string
  description: string
  created_at: string
  n_runs: number
}

interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(path)
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${path}`)
  return r.json() as Promise<T>
}

export async function listRuns(params?: {
  experiment?: string
  status?: RunStatus
}): Promise<RunSummary[]> {
  const qs = new URLSearchParams()
  if (params?.experiment) qs.set('experiment', params.experiment)
  if (params?.status) qs.set('status', params.status)
  const url = `/api/runs/${qs.toString() ? `?${qs}` : ''}`
  const page = await getJson<Paginated<RunSummary>>(url)
  return page.results
}

export async function getRun(runId: string): Promise<RunDetail> {
  return getJson<RunDetail>(`/api/runs/${runId}/`)
}

export async function listExperiments(): Promise<Experiment[]> {
  return getJson<Experiment[]>('/api/experiments/')
}

export interface PortfolioPoint {
  date: string
  strategy_return: number
  cum_return: number
}

export interface PortfolioSeries {
  run_id: string
  points: PortfolioPoint[]
}

export async function getPortfolioReturns(runId: string): Promise<PortfolioSeries> {
  return getJson<PortfolioSeries>(`/api/runs/${runId}/portfolio-returns/`)
}

export interface PermDistribution {
  run_id: string
  baseline_metric: number
  median_perm: number | null
  p_gte: number | null
  p_lte: number | null
  p_two_sided: number | null
  effect_size: number | null
  n_valid: number
  n_permutations: number
  metrics: number[]
}

export async function getPermMetrics(runId: string): Promise<PermDistribution | null> {
  try {
    return await getJson<PermDistribution>(`/api/runs/${runId}/perm-metrics/`)
  } catch (e) {
    if (String(e).includes('404')) return null
    throw e
  }
}

export interface FeatureAggRow {
  feature: string
  n_runs: number
  mean_importance: number | null
  median_importance: number | null
  std_importance: number | null
  mean_rank: number | null
  best_rank: number | null
  worst_rank: number | null
}

export async function getFeatureImportance(): Promise<{
  features: FeatureAggRow[]
  n_total_runs: number
}> {
  return getJson('/api/feature-importance/')
}

export interface DqRunSummary {
  run_id: string
  started_at: string
  finished_at: string | null
  summary: { total: number; pass: number; warn: number; fail: number; universe?: string }
}

export interface DqCheck {
  check_name: string
  status: 'pass' | 'warn' | 'fail'
  rows_checked: number
  rows_failed: number
  details: Record<string, unknown>
}

export interface DqRunDetail extends DqRunSummary {
  checks: DqCheck[]
}

export async function getDqRuns(): Promise<DqRunSummary[]> {
  return getJson<DqRunSummary[]>('/api/dq/runs/')
}

export async function getDqRunDetail(runId: string): Promise<DqRunDetail> {
  return getJson<DqRunDetail>(`/api/dq/runs/${runId}/`)
}

export interface IngestStatus {
  symbols: {
    known_in_dim: number
    ingested: number
    per_symbol: {
      symbol: string
      first_date: string | null
      last_date: string | null
      n_rows: number
      last_ingest: string | null
    }[]
  }
  prices_total_rows: number
  factors: {
    n_rows: number
    first_date: string | null
    last_date: string | null
    last_ingest: string | null
  }
}

export async function getIngestStatus(): Promise<IngestStatus> {
  return getJson<IngestStatus>('/api/ingest/status/')
}

export interface IngestHistoryRow {
  run_id: string
  job_name: string
  started_at: string
  finished_at: string | null
  duration_seconds: number | null
  status: 'running' | 'completed' | 'failed'
  rows_ingested: number
  summary: Record<string, unknown>
  error: string
}

export async function getSchedulerRuns(): Promise<IngestHistoryRow[]> {
  return getJson<IngestHistoryRow[]>('/api/scheduler/runs/')
}
