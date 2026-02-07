import client from "./client";

export const fetchStig = (distro: string, offline?: boolean) =>
  client.get(`/api/fetch_stig/${distro}`, { params: { offline } });

export const runAudit = (payload: {
  hosts: string[];
  distro: string;
  profile_name: string;
  profile_path: string;
}) => client.post("/api/audit", payload);

export const runMitigate = (payload: {
  hosts: string[];
  distro: string;
  profile_name: string;
  playbook_path: string;
  dry_run: boolean;
}) => client.post("/api/mitigate", payload);

export const listProfiles = () => client.get("/api/profiles");

export const createProfile = (payload: {
  name: string;
  distro: string;
  description: string;
  content: string;
}) => client.post("/api/profiles", payload);

export const listHosts = () => client.get("/api/hosts");

export const createHost = (payload: {
  hostname: string;
  ip_address: string;
  ssh_user: string;
  os_distro: string;
  os_version: string;
}) => client.post("/api/hosts", payload);

export const updateHost = (id: number, payload: Record<string, unknown>) =>
  client.put(`/api/hosts/${id}`, payload);

export const deleteHost = (id: number) => client.delete(`/api/hosts/${id}`);

export const testHostConnection = (payload: {
  hostname: string;
  ssh_user?: string;
  port?: number;
}) => client.post("/api/hosts/test-connection", payload);

export const dashboardSummary = () => client.get("/api/dashboard/summary");
export const dashboardSeverity = () =>
  client.get("/api/dashboard/severity-breakdown");
export const dashboardTopFailures = () =>
  client.get("/api/dashboard/top-failures");
export const dashboardTimeline = () => client.get("/api/dashboard/timeline");

export const auditHistory = () => client.get("/api/audit/history");
export const mitigateHistory = () => client.get("/api/mitigate/history");
