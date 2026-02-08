import { useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  IconButton,
  Snackbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import RefreshIcon from "@mui/icons-material/Refresh";
import NetworkCheckIcon from "@mui/icons-material/NetworkCheck";

import {
  listHosts,
  refreshHosts,
  testHostConnection,
} from "../api/endpoints";

interface HostRow {
  id: number;
  alias: string;
  hostname: string;
  ssh_user: string;
  port: number;
  identity_file: string;
  proxy_jump: string;
}

export default function Hosts() {
  const [rows, setRows] = useState<HostRow[]>([]);
  const [loading, setLoading] = useState(false);
  const [testResult, setTestResult] = useState<{
    open: boolean;
    success: boolean;
    message: string;
  }>({ open: false, success: false, message: "" });

  const loadHosts = async () => {
    const response = await listHosts();
    setRows(response.data);
  };

  useEffect(() => {
    loadHosts();
  }, []);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const res = await refreshHosts();
      const data = res.data as { discovered: number; created: number };
      setTestResult({
        open: true,
        success: true,
        message: `Scanned SSH config: ${data.discovered} hosts found, ${data.created} new hosts imported.`,
      });
      await loadHosts();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setTestResult({
        open: true,
        success: false,
        message: `Refresh failed: ${msg}`,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async (row: HostRow) => {
    try {
      const res = await testHostConnection({
        hostname: row.hostname,
        ssh_user: row.ssh_user,
        port: row.port,
      });
      const data = res.data as { success: boolean; error?: string };
      setTestResult({
        open: true,
        success: data.success,
        message: data.success
          ? `SSH connection to ${row.alias || row.hostname} succeeded`
          : `SSH failed: ${data.error}`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setTestResult({
        open: true,
        success: false,
        message: `Connection test failed: ${msg}`,
      });
    }
  };

  /** Show just the key filename rather than the full container path */
  const shortKeyName = (path: string) => {
    if (!path) return "—";
    const parts = path.split("/");
    return parts[parts.length - 1];
  };

  const columns: GridColDef[] = [
    { field: "alias", headerName: "Host", flex: 1, minWidth: 140 },
    { field: "hostname", headerName: "HostName", flex: 1, minWidth: 160 },
    { field: "ssh_user", headerName: "User", width: 110 },
    { field: "port", headerName: "Port", width: 80, type: "number" },
    {
      field: "identity_file",
      headerName: "IdentityFile",
      flex: 1,
      minWidth: 150,
      renderCell: (params) => (
        <Tooltip title={params.value || ""}>
          <span>{shortKeyName(params.value as string)}</span>
        </Tooltip>
      ),
    },
    {
      field: "proxy_jump",
      headerName: "ProxyJump",
      width: 130,
      renderCell: (params) => params.value || "—",
    },
    {
      field: "actions",
      headerName: "",
      width: 60,
      sortable: false,
      filterable: false,
      disableColumnMenu: true,
      renderCell: (params) => (
        <Tooltip title="Test SSH connection">
          <IconButton
            size="small"
            onClick={() => handleTest(params.row as HostRow)}
          >
            <NetworkCheckIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      ),
    },
  ];

  return (
    <Box>
      <Box
        display="flex"
        alignItems="center"
        justifyContent="space-between"
        sx={{ mb: 1 }}
      >
        <Typography variant="h4">Hosts</Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={loading}
        >
          {loading ? "Scanning…" : "Re-scan SSH Config"}
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Hosts are imported automatically from the server&apos;s{" "}
        <code>~/.ssh/config</code> on startup. To add or remove hosts, edit the
        SSH config file on the StreamGuard server and click{" "}
        <strong>Re-scan SSH Config</strong>.
      </Typography>

      <Box sx={{ height: 480 }}>
        <DataGrid
          rows={rows}
          columns={columns}
          getRowId={(row) => row.id}
          disableRowSelectionOnClick
          initialState={{
            sorting: { sortModel: [{ field: "alias", sort: "asc" }] },
          }}
        />
      </Box>

      <Snackbar
        open={testResult.open}
        autoHideDuration={5000}
        onClose={() =>
          setTestResult((prev) => ({ ...prev, open: false }))
        }
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          severity={testResult.success ? "success" : "error"}
          onClose={() =>
            setTestResult((prev) => ({ ...prev, open: false }))
          }
        >
          {testResult.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}
