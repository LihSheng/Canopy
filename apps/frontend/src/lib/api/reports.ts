import { request } from './client';
import type {
  ExportHistory,
  ExportJob,
  ExportTriggerResponse,
} from './types';

export const fetchExportHistory = (): Promise<ExportHistory> => {
  return request<ExportHistory>('/api/exports/history');
}

export const triggerExport = (
  presetName: string,
  timeRange: string,
): Promise<ExportTriggerResponse> => {
  return request<ExportTriggerResponse>('/api/exports/trigger', {
    method: 'POST',
    body: JSON.stringify({ preset_name: presetName, time_range: timeRange }),
  });
}

export const fetchExportJob = (jobId: string): Promise<ExportJob> => {
  return request<ExportJob>(`/api/exports/jobs/${jobId}`);
}

export const rerunExportJob = (jobId: string): Promise<ExportTriggerResponse> => {
  return request<ExportTriggerResponse>(`/api/exports/jobs/${jobId}/rerun`, {
    method: 'POST',
  });
}
