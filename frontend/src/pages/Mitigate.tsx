import { useState } from "react";
import {
  Box,
  Button,
  Grid,
  List,
  ListItem,
  TextField,
  Typography,
} from "@mui/material";

import { runMitigate } from "../api/endpoints";
import useWebSocket from "../hooks/useWebSocket";

export default function Mitigate() {
  const [hosts, setHosts] = useState("localhost");
  const [distro, setDistro] = useState("rhel");
  const [profileName, setProfileName] = useState("stig");
  const [playbookPath, setPlaybookPath] = useState("");
  const [jobId, setJobId] = useState<number | null>(null);

  const wsUrl = jobId
    ? `ws://localhost:8000/ws/mitigate/${jobId}`
    : "";
  const { messages } = useWebSocket(wsUrl);

  const handleSubmit = async () => {
    const response = await runMitigate({
      hosts: hosts.split(",").map((host) => host.trim()),
      distro,
      profile_name: profileName,
      playbook_path: playbookPath,
      dry_run: true,
    });
    setJobId(response.data.job_id);
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Mitigate Hosts
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
            label="Playbook Path"
            fullWidth
            value={playbookPath}
            onChange={(event) => setPlaybookPath(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={1} display="flex" alignItems="center">
          <Button variant="contained" onClick={handleSubmit}>
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
