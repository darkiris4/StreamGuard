import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Grid,
  TextField,
  Typography,
} from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";

import { runAudit, getCacStatus, fetchCacContent } from "../api/endpoints";
import ReportDataGrid from "../components/ReportDataGrid";

const columns: GridColDef[] = [
  { field: "rule_id", headerName: "Rule ID", flex: 1 },
  { field: "severity", headerName: "Severity", width: 120 },
  { field: "status", headerName: "Status", width: 120 },
  { field: "host", headerName: "Host", width: 160 },
];

export default function Audit() {
  const [hosts, setHosts] = useState("localhost");
  const [distro, setDistro] = useState("rhel9");
  const [profileName, setProfileName] = useState("stig");
  const [profilePath, setProfilePath] = useState("");
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState("");
  const [cacMissing, setCacMissing] = useState(false);

  const checkAndSubmit = async () => {
    setError("");
    setCacMissing(false);

    // If profile_path is manually provided, skip the CAC check
    if (profilePath) {
      return handleSubmit();
    }

    // Check whether cached content is available for this distro
    try {
      const statusRes = await getCacStatus();
      const available: string[] = statusRes.data.available_distros || [];
      if (!available.includes(distro) && !available.some((d: string) => distro.startsWith(d) || d.startsWith(distro))) {
        setCacMissing(true);
        return;
      }
    } catch {
      // Backend unreachable — let the audit endpoint handle it
    }
    return handleSubmit();
  };

  const handleFetchContent = async () => {
    setFetching(true);
    setError("");
    try {
      await fetchCacContent(distro);
      setCacMissing(false);
      // Content fetched — now run the audit
      await handleSubmit();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Failed to fetch CAC content: ${msg}`);
    } finally {
      setFetching(false);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await runAudit({
        hosts: hosts.split(",").map((host) => host.trim()),
        distro,
        profile_name: profileName,
        profile_path: profilePath,
      });
      const data = response.data as {
        results: {
          host: string;
          rules: { rule_id: string; severity: string; status: string }[];
        }[];
      };
      const flattened = data.results.flatMap((result) =>
        result.rules.map((rule) => ({
          id: `${result.host}-${rule.rule_id}`,
          host: result.host,
          rule_id: rule.rule_id,
          severity: rule.severity,
          status: rule.status,
        }))
      );
      setRows(flattened);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Audit failed: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Audit Hosts
      </Typography>

      {cacMissing && (
        <Alert
          severity="warning"
          sx={{ mb: 2 }}
          action={
            <Button
              color="inherit"
              size="small"
              onClick={handleFetchContent}
              disabled={fetching}
              startIcon={fetching ? <CircularProgress size={16} /> : undefined}
            >
              {fetching ? "Fetching…" : "Fetch Now"}
            </Button>
          }
        >
          No cached CAC content found for <strong>{distro}</strong>. Fetch
          content from ComplianceAsCode first.
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={3}>
          <TextField
            label="Hosts (comma-separated)"
            fullWidth
            value={hosts}
            onChange={(event) => setHosts(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={2}>
          <TextField
            label="Distro"
            fullWidth
            value={distro}
            onChange={(event) => setDistro(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <TextField
            label="Profile Name"
            fullWidth
            value={profileName}
            onChange={(event) => setProfileName(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <TextField
            label="Profile Path (optional)"
            fullWidth
            value={profilePath}
            onChange={(event) => setProfilePath(event.target.value)}
            helperText="Leave empty to auto-resolve from CAC cache"
          />
        </Grid>
        <Grid item xs={12} md={1} display="flex" alignItems="center">
          <Button
            variant="contained"
            onClick={checkAndSubmit}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : undefined}
          >
            Run
          </Button>
        </Grid>
      </Grid>
      <ReportDataGrid rows={rows} columns={columns} />
    </Box>
  );
}
