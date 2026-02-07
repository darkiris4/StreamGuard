import { useState } from "react";
import {
  Box,
  Button,
  Grid,
  TextField,
  Typography,
} from "@mui/material";
import { GridColDef } from "@mui/x-data-grid-pro";

import { runAudit } from "../api/endpoints";
import ReportDataGrid from "../components/ReportDataGrid";

const columns: GridColDef[] = [
  { field: "rule_id", headerName: "Rule ID", flex: 1 },
  { field: "severity", headerName: "Severity", width: 120 },
  { field: "status", headerName: "Status", width: 120 },
  { field: "host", headerName: "Host", width: 160 },
];

export default function Audit() {
  const [hosts, setHosts] = useState("localhost");
  const [distro, setDistro] = useState("rhel");
  const [profileName, setProfileName] = useState("stig");
  const [profilePath, setProfilePath] = useState("");
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);

  const handleSubmit = async () => {
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
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Audit Hosts
      </Typography>
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
            label="Profile Path"
            fullWidth
            value={profilePath}
            onChange={(event) => setProfilePath(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={1} display="flex" alignItems="center">
          <Button variant="contained" onClick={handleSubmit}>
            Run
          </Button>
        </Grid>
      </Grid>
      <ReportDataGrid rows={rows} columns={columns} />
    </Box>
  );
}
