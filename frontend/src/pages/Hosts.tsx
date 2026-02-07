import { useEffect, useState } from "react";
import {
  Box,
  Button,
  Grid,
  TextField,
  Typography,
} from "@mui/material";
import { DataGridPro, GridColDef } from "@mui/x-data-grid-pro";

import {
  createHost,
  deleteHost,
  listHosts,
  testHostConnection,
} from "../api/endpoints";

const columns: GridColDef[] = [
  { field: "hostname", headerName: "Hostname", flex: 1 },
  { field: "ip_address", headerName: "IP Address", width: 160 },
  { field: "ssh_user", headerName: "SSH User", width: 140 },
  { field: "os_distro", headerName: "OS", width: 140 },
  { field: "os_version", headerName: "Version", width: 140 },
];

export default function Hosts() {
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [hostname, setHostname] = useState("");
  const [ipAddress, setIpAddress] = useState("");
  const [sshUser, setSshUser] = useState("root");
  const [osDistro, setOsDistro] = useState("");
  const [osVersion, setOsVersion] = useState("");

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
    if (!hostname) {
      return;
    }
    await testHostConnection({ hostname, ssh_user: sshUser });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Hosts
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
        <DataGridPro
          rows={rows}
          columns={columns}
          getRowId={(row) => row.id}
          onRowDoubleClick={(params) => handleDelete(params.row.id)}
        />
      </Box>
      <Typography variant="caption" sx={{ mt: 1, display: "block" }}>
        Double-click a row to delete it.
      </Typography>
    </Box>
  );
}
