import { useState } from "react";
import { Box, Button, Grid, TextField, Typography } from "@mui/material";

import { createProfile } from "../api/endpoints";
import MonacoRuleEditor from "../components/MonacoRuleEditor";

export default function ProfileEditor() {
  const [name, setName] = useState("Custom STIG");
  const [distro, setDistro] = useState("rhel");
  const [description, setDescription] = useState("Custom profile");
  const [content, setContent] = useState("<xccdf></xccdf>");

  const handleSave = async () => {
    await createProfile({ name, distro, description, content });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Profile Editor
      </Typography>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={3}>
          <TextField
            label="Profile Name"
            fullWidth
            value={name}
            onChange={(event) => setName(event.target.value)}
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
        <Grid item xs={12} md={5}>
          <TextField
            label="Description"
            fullWidth
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={2}>
          <Button variant="contained" onClick={handleSave}>
            Save
          </Button>
        </Grid>
      </Grid>
      <MonacoRuleEditor value={content} onChange={setContent} />
    </Box>
  );
}
