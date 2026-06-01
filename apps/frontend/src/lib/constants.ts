// Centralized string constants for the frontend.
// Extracted to eliminate duplication and make future changes single-point.

// ─── Routes ───
export const ROUTES = {
  home: "/",
  login: "/login",
  dashboard: "/dashboard",
  anomalies: "/dashboard/anomalies",
  departments: "/dashboard/departments",
  reports: "/dashboard/reports",
  profile: "/dashboard/profile",
  connections: {
    home: "/dashboard/connections",
    sources: "/dashboard/connections/sources",
    datasets: "/dashboard/connections/datasets",
    runs: "/dashboard/connections/runs",
    setup: "/dashboard/connections/setup",
    lineage: "/dashboard/connections/lineage",
    datasetDetail: (id: string) => `/dashboard/connections/datasets/${id}`,
    datasetLineage: (id: string) => `/dashboard/connections/datasets/${id}?tab=Lineage`,
    runDetail: (id: string) => `/dashboard/connections/runs/${id}`,
    connectionLineage: (id: string) => `/dashboard/connections/lineage/${id}`,
    setupWithSource: (source: string) => `/dashboard/connections/setup?source=${encodeURIComponent(source)}`,
  },
  departmentDetail: (id: string) => `/dashboard/departments/${encodeURIComponent(id)}`,
  admin: {
    home: "/dashboard/admin",
    dataHealth: "/dashboard/admin/data-health",
  },
} as const;

// ─── Run / Refresh / Dataset Status ───
export type RunStatus = "completed" | "failed" | "running" | "queued";
export type RefreshStatusKey = "idle" | "queued" | "running" | "completed" | "failed";
export type VersionStatus = "ready" | "pending" | "processing";

export const STATUS_COLORS: Record<string, string> = {
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  running: "bg-blue-100 text-blue-800",
  queued: "bg-zinc-100 text-zinc-600",
};

// Connection-specific status colors (matches backend ConnectionStatus enum)
export const CONNECTION_STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  paused: "bg-amber-100 text-amber-800",
  archived: "bg-zinc-100 text-zinc-600",
  soft_deleted: "bg-zinc-100 text-zinc-500",
  deleted: "bg-red-100 text-red-800",
  inactive: "bg-zinc-100 text-zinc-600",
  error: "bg-red-100 text-red-800",
};

// Dataset-specific status colors (matches backend DatasetStatus enum)
export const DATASET_STATUS_COLORS: Record<string, string> = {
  active: "bg-green-100 text-green-800",
  pending_initial_run: "bg-amber-100 text-amber-800",
  inactive: "bg-zinc-100 text-zinc-600",
  error: "bg-red-100 text-red-800",
  blocked_schema_drift: "bg-orange-100 text-orange-800",
};

export const REFRESH_STATUS_LABELS: Record<
  RefreshStatusKey,
  { text: string; className: string }
> = {
  idle: { text: "Up to date", className: "bg-emerald-50 text-emerald-700" },
  queued: { text: "Queued", className: "bg-blue-50 text-blue-700" },
  running: { text: "Refreshing...", className: "bg-amber-50 text-amber-700" },
  completed: { text: "Completed", className: "bg-emerald-50 text-emerald-700" },
  failed: { text: "Failed", className: "bg-red-50 text-red-700" },
};

// ─── Anomaly Severity ───
export type Severity = "high" | "medium" | "low";

export const SEVERITIES: Severity[] = ["high", "medium", "low"];

export const SEVERITY_COLORS: Record<Severity, string> = {
  high: "bg-red-100 text-red-800",
  medium: "bg-amber-100 text-amber-800",
  low: "bg-blue-100 text-blue-800",
};

// ─── Sync Policy ───
export type SyncMode = "batch" | "real_time" | "direct_query";
export type BatchStrategy = "full_snapshot" | "incremental_cursor";
export type RealTimeStrategy = "cdc" | "polling";

export const SYNC_MODES: SyncMode[] = ["batch", "real_time", "direct_query"];
export const BATCH_STRATEGIES: BatchStrategy[] = ["full_snapshot", "incremental_cursor"];
export const REAL_TIME_STRATEGIES: RealTimeStrategy[] = ["cdc", "polling"];

// ─── Query Param Keys ───
export const QUERY_PARAMS = {
  range: "range",
  severity: "severity",
  departmentId: "department_id",
  anomalyId: "anomaly_id",
  source: "source",
  tab: "tab",
  year: "year",
  month: "month",
} as const;

// ─── LocalStorage Keys ───
export const LOCAL_STORAGE_KEYS = {
  sidebarCollapsed: "canopy-analytics-sidebar-collapsed",
} as const;

// ─── Source Detail Source Values ───
export const DETAIL_SOURCE = {
  dashboardAttention: "dashboard_attention",
  dashboardRanking: "dashboard_ranking",
  anomalies: "anomalies",
} as const;

// ─── Brand ───
export const BRAND = {
  name: "Canopy Intelligence",
} as const;

// ─── Default Formatting ───
export const DEFAULT_LOCALE = "en-US";
export const DEFAULT_CURRENCY = "USD";

// ─── Common UI Labels ───
export const UI_LABELS = {
  loading: "Loading...",
  loadingDashboard: "Loading dashboard...",
  loadingRunDetails: "Loading run details...",
  noData: "No data available",
  noRunsYet: "No runs yet",
  noDatasets: "No datasets",
  noConnections: "No connections",
  noAnomalies: "No anomalies detected",
  noDepartments: "No departments",
  refreshData: "Refresh data",
  refreshing: "Refreshing...",
  tryAgain: "Try again",
  cancel: "Cancel",
  confirm: "Confirm",
  delete: "Delete",
  deleting: "Deleting...",
  deploying: "Deploying...",
  back: "Back",
  next: "Next",
  finishAndDeploy: "Finish & Deploy",
  testConnection: "Test Connection",
  testing: "Testing...",
  search: "Search",
  previous: "Previous",
  view: "View",
  open: "Open",
  edit: "Edit",
  signIn: "Sign in",
  signingIn: "Signing in...",
  signOut: "Sign out",
  selectAll: "Select All",
} as const;

// ─── Error Message Patterns ───
export const errorMessageFailedToLoad = (resource: string): string => {
  return `Failed to load ${resource}`;
}

export const ERROR_MESSAGES = {
  loginFailed: "Login failed",
  sessionCheckFailed: "Session check failed",
  statusCheckFailed: "Status check failed",
  switchFailed: "Switch failed",
  uploadFailed: "Upload failed",
  connectionFailed: "Connection failed",
  connectionTestFailed: "Connection test failed",
  failedToDiscoverTables: "Failed to discover tables",
  failedToCreateDatasets: "Failed to create datasets",
  failedToSaveSyncPolicy: "Failed to save sync policy",
  failedToRefreshDataset: "Failed to refresh dataset",
  failedToDeleteDataset: "Failed to delete dataset",
  failedToDeleteVersion: "Failed to delete version",
  failedToDeleteConnection: "Failed to delete connection",
} as const;

// ─── File Upload ───
export const FILE_ACCEPT = ".xlsx,.csv";
