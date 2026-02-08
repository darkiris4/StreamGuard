import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Grid,
  List,
  ListItem,
  TextField,
  Typography,
} from "@mui/material";

import { runMitigate, getCacStatus, fetchCacContent } from "../api/endpoints";
import useWebSocket from "../hooks/useWebSocket";

export default function Mitigate() {
  const [hosts, setHosts] = useState("localhost");
  const [distro, setDistro] = useState("rhel9");
  const [profileName, setProfileName] = useState("stig");
  const [playbookPath, setPlaybookPath] = useState("");
  const [jobId, setJobId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetching, setFetching] = useState(false);
  const [error, setError] = useState("");
  const [cacMissing, setCacMissing] = useState(false);

  const wsUrl = jobId
    ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}/ws/mitigate/${jobId}`
    : "";
  const { messages } = useWebSocket(wsUrl);

  const checkAndSubmit = async () => {
    setError("");
    setCacMissing(false);

    // If playbook_path is manually provided, skip the CAC check
    if (playbookPath) {
      return handleSubmit();
    }

    // Check whether cached content is available for this distro
    try {
      const statusRes = await getCacStatus();
      const available: string[] = statusRes.data.available_distros || [];
      const profiles: Record<string, string[]> = statusRes.data.profiles || {};
      const hasPlaybook = available.some((d: string) => {
        const match = distro.startsWith(d) || d.startsWith(distro) || d === distro;
        return match && profiles[d]?.includes(profileName);
      });
      if (!hasPlaybook) {
        setCacMissing(true);
        return;
      }
    } catch {
      // Backend unreachable — let the mitigate endpoint handle it
    }
    return handleSubmit();
  };

  const handleFetchContent = async () => {
    setFetching(true);
    setError("");
    try {
      await fetchCacContent(distro);
      setCacMissing(false);
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
      const response = await runMitigate({
        hosts: hosts.split(",").map((host) => host.trim()),
        distro,
        profile_name: profileName,
        playbook_path: playbookPath,
        dry_run: true,
      });
      setJobId(response.data.job_id);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(`Mitigation failed: ${msg}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Mitigate Hosts
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
          No cached CAC playbook found for <strong>{distro}</strong> / <strong>{profileName}</strong>.
          Fetch content from ComplianceAsCode first.
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
            label="Playbook Path (optional)"
            fullWidth
            value={playbookPath}
            onChange={(event) => setPlaybookPath(event.target.value)}
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
      <Typography variant="h6" gutterBottom>
        Live Logs
      </Typography>
      <List dense>
        {messages.map((message, index) => (
          <ListItem key={`${index}-${jobId}`}>
            <Typography variant="body2">
              {JSON.stringify(message)}
            </Typography>
          </ListItem>
        ))}
      </List>
    </Box>
  );
}
