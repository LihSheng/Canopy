import { describe, expect, it, vi, beforeEach } from "vitest";
import { request } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({
  request: vi.fn(),
  API_BASE: "http://localhost:8005",
}));

import {
  fetchProjects,
  fetchProject,
  createProject,
  fetchSourceTypes,
  fetchConnections,
  fetchConnection,
  fetchConnectionDependencies,
  createConnection,
  deleteConnection,
  previewStaticFile,
  deleteStaticFilePreview,
  fetchDatasets,
  createDataset,
  fetchDataset,
  fetchDatasetVersions,
  fetchDatasetPreview,
  fetchDatasetLineage,
  fetchDatasetHealth,
  fetchDatasetDeleteSummary,
  fetchDatasetVersionDeleteSummary,
  deleteDataset,
  deleteDatasetVersion,
  fetchRuns,
  reimportDatasetVersion,
  fetchRun,
  createRun,
  fetchConnectionTest,
  fetchTableDiscovery,
  fetchTablePreview,
  updateSyncPolicy,
} from "@/lib/api/data-source";

const mockRequest = vi.mocked(request);

describe("data-source API", () => {
  beforeEach(() => {
    mockRequest.mockReset();
  });

  describe("projects", () => {
    it("fetchProjects calls GET /api/projects/", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchProjects();
      expect(mockRequest).toHaveBeenCalledWith("/api/projects/");
    });

    it("fetchProject calls GET /api/projects/:id", async () => {
      mockRequest.mockResolvedValue({ id: "p1" });
      const result = await fetchProject("p1");
      expect(mockRequest).toHaveBeenCalledWith("/api/projects/p1");
      expect(result.id).toBe("p1");
    });

    it("createProject calls POST /api/projects/", async () => {
      mockRequest.mockResolvedValue({ id: "p1", name: "Test" });
      const result = await createProject({ name: "Test" });
      expect(mockRequest).toHaveBeenCalledWith("/api/projects/", {
        method: "POST",
        body: JSON.stringify({ name: "Test" }),
      });
      expect(result.name).toBe("Test");
    });
  });

  describe("source types", () => {
    it("fetchSourceTypes calls GET /api/source-types/", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchSourceTypes();
      expect(mockRequest).toHaveBeenCalledWith("/api/source-types/");
    });
  });

  describe("connections", () => {
    it("fetchConnections without projectId", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchConnections();
      expect(mockRequest).toHaveBeenCalledWith("/api/connections/");
    });

    it("fetchConnections with projectId", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchConnections("p1");
      expect(mockRequest).toHaveBeenCalledWith("/api/connections/?project_id=p1");
    });

    it("fetchConnection calls GET /api/connections/:id", async () => {
      mockRequest.mockResolvedValue({ id: "c1" });
      const result = await fetchConnection("c1");
      expect(mockRequest).toHaveBeenCalledWith("/api/connections/c1");
      expect(result.id).toBe("c1");
    });

    it("fetchConnectionDependencies calls GET /api/connections/:id/dependencies", async () => {
      mockRequest.mockResolvedValue({ connection_id: "c1", can_delete: true });
      await fetchConnectionDependencies("c1");
      expect(mockRequest).toHaveBeenCalledWith("/api/connections/c1/dependencies");
    });

    it("createConnection calls POST /api/connections/ with config_json", async () => {
      const payload = {
        project_id: "p1",
        source_type: "postgresql",
        name: "my-db",
        config_json: { host: "localhost", port: 5432 },
      };
      mockRequest.mockResolvedValue({ id: "c1" });
      const result = await createConnection(payload);
      expect(mockRequest).toHaveBeenCalledWith("/api/connections/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      expect(result.id).toBe("c1");
    });

    it("deleteConnection calls DELETE /api/connections/:id", async () => {
      mockRequest.mockResolvedValue({ deleted: true, id: "c1" });
      const result = await deleteConnection("c1");
      expect(mockRequest).toHaveBeenCalledWith("/api/connections/c1", {
        method: "DELETE",
      });
      expect(result.deleted).toBe(true);
    });

    it("fetchConnectionTest calls POST /api/connections/:id/test", async () => {
      mockRequest.mockResolvedValue({ success: true });
      const result = await fetchConnectionTest("c1");
      expect(mockRequest).toHaveBeenCalledWith("/api/connections/c1/test", {
        method: "POST",
      });
      expect(result.success).toBe(true);
    });
  });

  describe("static file preview", () => {
    it("previewStaticFile sends FormData", async () => {
      mockRequest.mockResolvedValue({ source_file_path: "/tmp/x.csv" });
      const file = new File(["a,b\n1,2"], "test.csv", { type: "text/csv" });

      const result = await previewStaticFile(file);

      expect(mockRequest).toHaveBeenCalledTimes(1);
      const [url, opts] = mockRequest.mock.calls[0];
      expect(url).toBe("/api/connections/preview");
      expect(opts.method).toBe("POST");
      expect(opts.body).toBeInstanceOf(FormData);
      expect(result.source_file_path).toBe("/tmp/x.csv");
    });

    it("deleteStaticFilePreview calls DELETE /api/connections/preview", async () => {
      mockRequest.mockResolvedValue({ deleted: true });
      const result = await deleteStaticFilePreview("/tmp/x.csv");
      expect(mockRequest).toHaveBeenCalledWith("/api/connections/preview", {
        method: "DELETE",
        body: JSON.stringify({ source_file_path: "/tmp/x.csv" }),
      });
      expect(result.deleted).toBe(true);
    });
  });

  describe("datasets", () => {
    it("fetchDatasets without filters", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchDatasets();
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/");
    });

    it("fetchDatasets with projectId and connectionId", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchDatasets("p1", "c1");
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/?project_id=p1&connection_id=c1");
    });

    it("createDataset calls POST /api/datasets/", async () => {
      const payload = {
        project_id: "p1",
        connection_id: "c1",
        name: "users",
        source_object_name: "users",
        sync_mode: "batch",
        batch_strategy: "full_snapshot",
        real_time_strategy: null,
        cursor_column: null,
      };
      mockRequest.mockResolvedValue({ id: "ds-1" });
      const result = await createDataset(payload);
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      expect(result.id).toBe("ds-1");
    });

    it("fetchDataset calls GET /api/datasets/:id", async () => {
      mockRequest.mockResolvedValue({ id: "ds-1" });
      const result = await fetchDataset("ds-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1");
      expect(result.id).toBe("ds-1");
    });

    it("fetchDatasetVersions calls GET /api/datasets/:id/versions", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchDatasetVersions("ds-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1/versions");
    });

    it("fetchDatasetPreview without params", async () => {
      mockRequest.mockResolvedValue({ columns: [], rows: [] });
      await fetchDatasetPreview("ds-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1/preview");
    });

    it("fetchDatasetPreview with page params", async () => {
      mockRequest.mockResolvedValue({ columns: [], rows: [] });
      await fetchDatasetPreview("ds-1", { page: 2, page_size: 50 });
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1/preview?page=2&page_size=50");
    });

    it("fetchDatasetLineage calls GET /api/datasets/:id/lineage", async () => {
      mockRequest.mockResolvedValue({ nodes: [], edges: [] });
      const result = await fetchDatasetLineage("ds-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1/lineage");
      expect(result.nodes).toEqual([]);
    });

    it("fetchDatasetHealth calls GET /api/datasets/:id/health", async () => {
      mockRequest.mockResolvedValue({ dataset_id: "ds-1", row_count: 100 });
      const result = await fetchDatasetHealth("ds-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1/health");
      expect(result.dataset_id).toBe("ds-1");
    });

    it("fetchDatasetDeleteSummary calls GET /api/datasets/:id/dependencies", async () => {
      mockRequest.mockResolvedValue({ dataset_id: "ds-1", can_delete: true });
      await fetchDatasetDeleteSummary("ds-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1/dependencies");
    });

    it("fetchDatasetVersionDeleteSummary calls correct path", async () => {
      mockRequest.mockResolvedValue({ dataset_id: "ds-1", version_id: "v1" });
      await fetchDatasetVersionDeleteSummary("ds-1", "v1");
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1/versions/v1/dependencies");
    });

    it("deleteDataset calls DELETE /api/datasets/:id", async () => {
      mockRequest.mockResolvedValue({ deleted: true, id: "ds-1" });
      const result = await deleteDataset("ds-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1", {
        method: "DELETE",
      });
      expect(result.deleted).toBe(true);
    });

    it("deleteDatasetVersion calls DELETE for specific version", async () => {
      mockRequest.mockResolvedValue({ deleted: true, id: "v1" });
      const result = await deleteDatasetVersion("ds-1", "v1");
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1/versions/v1", {
        method: "DELETE",
      });
      expect(result.deleted).toBe(true);
    });

    it("updateSyncPolicy calls PATCH /api/datasets/:id/sync-policy", async () => {
      const policy = { sync_mode: "batch" };
      mockRequest.mockResolvedValue({ id: "ds-1" });
      const result = await updateSyncPolicy("ds-1", policy);
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1/sync-policy", {
        method: "PATCH",
        body: JSON.stringify(policy),
      });
      expect(result.id).toBe("ds-1");
    });
  });

  describe("runs", () => {
    it("fetchRuns without datasetId", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchRuns();
      expect(mockRequest).toHaveBeenCalledWith("/api/runs/");
    });

    it("fetchRuns with datasetId", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchRuns("ds-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/runs/?dataset_id=ds-1");
    });

    it("fetchRun calls GET /api/runs/:id", async () => {
      mockRequest.mockResolvedValue({ id: "run-1" });
      const result = await fetchRun("run-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/runs/run-1");
      expect(result.id).toBe("run-1");
    });

    it("createRun calls POST /api/runs/", async () => {
      mockRequest.mockResolvedValue({ id: "run-1" });
      const result = await createRun({ dataset_id: "ds-1" });
      expect(mockRequest).toHaveBeenCalledWith("/api/runs/", {
        method: "POST",
        body: JSON.stringify({ dataset_id: "ds-1" }),
      });
      expect(result.id).toBe("run-1");
    });

    it("reimportDatasetVersion calls POST /api/datasets/:id/reimport", async () => {
      mockRequest.mockResolvedValue({ id: "v2", status: "processing" });
      const result = await reimportDatasetVersion("ds-1", "/data/v1", ["col1"]);
      expect(mockRequest).toHaveBeenCalledWith("/api/datasets/ds-1/reimport", {
        method: "POST",
        body: JSON.stringify({ data_path: "/data/v1", columns: ["col1"] }),
      });
      expect(result.id).toBe("v2");
    });
  });

  describe("table discovery", () => {
    it("fetchTableDiscovery calls POST /api/connections/:id/discover", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchTableDiscovery("c1");
      expect(mockRequest).toHaveBeenCalledWith("/api/connections/c1/discover");
    });

    it("fetchTablePreview calls GET with encoded table name", async () => {
      mockRequest.mockResolvedValue({ columns: [], rows: [] });
      await fetchTablePreview("c1", "my table");
      expect(mockRequest).toHaveBeenCalledWith(
        "/api/connections/c1/discover/my%20table",
      );
    });
  });
});
