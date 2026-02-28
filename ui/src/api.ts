/**
 * API client for MasterPi AI backend.
 *
 * All calls go through Vite proxy: /api → http://localhost:8000/api
 */

const BASE = "/api/v1";

// ---------- Types (mirror backend DTOs) ----------

export interface VideoInfo {
  title: string;
  channel: string;
  duration_seconds: number;
  thumbnail_url: string;
}

export interface TierCost {
  tier: "short" | "medium" | "full";
  duration_minutes: number;
  transcription_cost: number;
  translation_cost: number;
  tts_cost: number;
  stripe_fee: number;
  total_cost: number;
}

export interface AnalyzeResponse {
  video: VideoInfo;
  tiers: TierCost[];
}

export interface JobResponse {
  job_id: string;
  status: string;
  progress_pct: number;
  current_stage: string;
  error: string | null;
}

export interface Language {
  code: string;
  name: string;
}

export interface SSEProgress {
  status: string;
  progress_pct: number;
  current_stage: string;
  error: string | null;
}

// ---------- API calls ----------

export async function analyzeVideo(url: string): Promise<AnalyzeResponse> {
  const res = await fetch(`${BASE}/videos/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || err.detail || `Analyze failed (${res.status})`);
  }
  return res.json();
}

export async function createJob(
  url: string,
  tier: string,
  targetLanguage: string,
): Promise<JobResponse> {
  const res = await fetch(`${BASE}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, tier, target_language: targetLanguage }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.message || err.detail || `Job creation failed (${res.status})`);
  }
  return res.json();
}

export async function getJob(jobId: string): Promise<JobResponse> {
  const res = await fetch(`${BASE}/jobs/${jobId}`);
  if (!res.ok) throw new Error(`Job fetch failed (${res.status})`);
  return res.json();
}

export function getAudioUrl(jobId: string): string {
  return `${BASE}/jobs/${jobId}/audio`;
}

export async function fetchLanguages(): Promise<Language[]> {
  const res = await fetch(`${BASE}/languages`);
  if (!res.ok) throw new Error(`Languages fetch failed (${res.status})`);
  return res.json();
}

/**
 * Subscribe to job progress via SSE.
 * Returns an EventSource. Caller should add event listeners.
 */
export function subscribeJobProgress(jobId: string): EventSource {
  return new EventSource(`${BASE}/jobs/${jobId}/stream`);
}
