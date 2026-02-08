import client from "./client";

// ---- CAC Content Fetching ----

export const fetchCacContent = (distro: string, offline?: boolean) =>
  client.get(`/api/cac/fetch/${distro}`, { params: { offline } });

export const getCacStatus = () => client.get("/api/cac/status");

export const getCacProfiles = (distro: string) =>
  client.get(`/api/cac/profiles/${distro}`);

export const getCacDistros = () => client.get("/api/cac/distros");

export const setOfflineMode = (offline: boolean) =>
  client.post("/api/cac/offline-mode", { offline });

// Legacy alias
export const fetchStig = fetchCacContent;

// ---- Audit ----

export const runAudit = (payload: {
  hosts: string[];
  distro: string;
  profile_name: string;
  profile_path: string;
}) => client.post("/api/audit", payload);

export const auditHistory = () => client.get("/api/audit/history");

// ---- Mitigate ----

export const runMitigate = (payload: {
  hosts: string[];
  distro: string;
  profile_name: string;
  playbook_path: string;
  dry_run: boolean;
}) => client.post("/api/mitigate", payload);

export const mitigateHistory = () => client.get("/api/mitigate/history");

// ---- Profiles ----

export const listProfiles = () => client.get("/api/profiles");

export const createProfile = (payload: {
  name: string;
  distro: string;
  description: string;
  content: string;
}) => client.post("/api/profiles", payload);

// ---- Hosts ----

export const listHosts = () => client.get("/api/hosts");

export const refreshHosts = () => client.post("/api/hosts/refresh");

export const testHostConnection = (payload: {
  hostname: string;
  ssh_user?: string;
  port?: number;
}) => client.post("/api/hosts/test-connection", payload);

// ---- Dashboard ----

export const dashboardSummary = () => client.get("/api/dashboard/summary");
export const dashboardSeverity = () =>
  client.get("/api/dashboard/severity-breakdown");
export const dashboardTopFailures = () =>
  client.get("/api/dashboard/top-failures");
export const dashboardTimeline = () => client.get("/api/dashboard/timeline");
