import { request } from './client';
import type {
  ExportHistory,
  ExportJob,
  ExportTriggerResponse,
} from './types';

export function fetchExportHistory(): Promise<ExportHistory> {
  return request<ExportHistory>('/api/exports/history');
}

export function triggerExport(
  presetName: string,
  timeRange: string,
): Promise<ExportTriggerResponse> {
  return request<ExportTriggerResponse>('/api/exports/trigger', {
    method: 'POST',
    body: JSON.stringify({ preset_name: presetName, time_range: timeRange }),
  });
}

export function fetchExportJob(jobId: string): Promise<ExportJob> {
  return request<ExportJob>(`/api/exports/jobs/${jobId}`);
}

export function rerunExportJob(jobId: string): Promise<ExportTriggerResponse> {
  return request<ExportTriggerResponse>(`/api/exports/jobs/${jobId}/rerun`, {
    method: 'POST',
  });
}
