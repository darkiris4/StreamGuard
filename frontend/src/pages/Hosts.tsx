import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  Grid,
  Snackbar,
  TextField,
  Typography,
} from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";

import {
  createHost,
  deleteHost,
  listHosts,
  testHostConnection,
} from "../api/endpoints";

const columns: GridColDef[] = [
  { field: "hostname", headerName: "Hostname", flex: 1 },
  { field: "ip_address", headerName: "IP Address", width: 150 },
  { field: "ssh_user", headerName: "SSH User", width: 120 },
  { field: "os_distro", headerName: "OS", width: 120 },
  { field: "os_version", headerName: "Version", width: 100 },
  {
    field: "source",
    headerName: "Source",
    width: 130,
    renderCell: (params) => {
      const label =
        params.value === "ssh_config"
          ? "SSH config"
          : params.value === "known_hosts"
            ? "known_hosts"
            : "Manual";
      const color =
        params.value === "ssh_config"
          ? "info"
          : params.value === "known_hosts"
            ? "warning"
            : "default";
      return (
        <Chip
          label={label}
          size="small"
          color={color as "info" | "warning" | "default"}
          variant="outlined"
        />
      );
    },
  },
];

export default function Hosts() {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [hostname, setHostname] = useState("");
  const [ipAddress, setIpAddress] = useState("");
  const [sshUser, setSshUser] = useState("root");
  const [osDistro, setOsDistro] = useState("");
  const [osVersion, setOsVersion] = useState("");
  const [testResult, setTestResult] = useState<{ open: boolean; success: boolean; message: string }>({
    open: false,
    success: false,
    message: "",
  });

  const loadHosts = async () => {
    const response = await listHosts();
    setRows(response.data);
  };

  useEffect(() => {
    loadHosts();
  }, []);

  const handleCreate = async () => {
    await createHost({
      hostname,
      ip_address: ipAddress,
      ssh_user: sshUser,
      os_distro: osDistro,
      os_version: osVersion,
    });
    setHostname("");
    setIpAddress("");
    setOsDistro("");
    setOsVersion("");
    await loadHosts();
  };

  const handleDelete = async (id: number) => {
    await deleteHost(id);
    await loadHosts();
  };

  const handleTest = async () => {
    if (!hostname) return;
    try {
      const res = await testHostConnection({ hostname, ssh_user: sshUser });
      const data = res.data as { success: boolean; error?: string };
      setTestResult({
        open: true,
        success: data.success,
        message: data.success ? `SSH connection to ${hostname} succeeded` : `SSH failed: ${data.error}`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setTestResult({ open: true, success: false, message: `Connection test failed: ${msg}` });
    }
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Hosts
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Hosts from your SSH config (<code>~/.ssh/config</code>) are imported automatically on startup.
        Add new hosts manually below, or add them to your SSH config on the server.
      </Typography>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={3}>
          <TextField
            label="Hostname"
            fullWidth
            value={hostname}
            onChange={(event) => setHostname(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={2}>
          <TextField
            label="IP Address"
            fullWidth
            value={ipAddress}
            onChange={(event) => setIpAddress(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={2}>
          <TextField
            label="SSH User"
            fullWidth
            value={sshUser}
            onChange={(event) => setSshUser(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={2}>
          <TextField
            label="OS Distro"
            fullWidth
            value={osDistro}
            onChange={(event) => setOsDistro(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={2}>
          <TextField
            label="OS Version"
            fullWidth
            value={osVersion}
            onChange={(event) => setOsVersion(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={1} display="flex" alignItems="center" gap={1}>
          <Button variant="contained" onClick={handleCreate}>
            Save
          </Button>
          <Button variant="outlined" onClick={handleTest}>
            Test
          </Button>
        </Grid>
      </Grid>
      <Box sx={{ height: 420 }}>
        <DataGrid
          rows={rows}
          columns={columns}
          getRowId={(row) => row.id}
          onRowDoubleClick={(params) => handleDelete(params.row.id)}
        />
      </Box>
      <Typography variant="caption" sx={{ mt: 1, display: "block" }}>
        Double-click a row to delete it.
      </Typography>
      <Snackbar
        open={testResult.open}
        autoHideDuration={5000}
        onClose={() => setTestResult((prev) => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          severity={testResult.success ? "success" : "error"}
          onClose={() => setTestResult((prev) => ({ ...prev, open: false }))}
        >
          {testResult.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
