import { useState } from "react";
import {
  Box,
  Button,
  Grid,
  TextField,
  Typography,
} from "@mui/material";

import client from "../api/client";

export default function IsoBuilder() {
  const [distro, setDistro] = useState("ubuntu");
  const [baseIsoUrl, setBaseIsoUrl] = useState("");
  const [baseIsoFile, setBaseIsoFile] = useState<File | null>(null);

  const handleSubmit = async () => {
    const form = new FormData();
    form.append("distro", distro);
    if (baseIsoUrl) {
      form.append("base_iso_url", baseIsoUrl);
    }
    if (baseIsoFile) {
      form.append("base_iso", baseIsoFile);
    }

    const response = await client.post("/api/build_iso", form, {
      responseType: "blob",
    });

    const url = window.URL.createObjectURL(response.data);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${distro}_stig.iso`;
    link.click();
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        ISO Builder
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={12} md={3}>
          <TextField
            label="Distro"
            fullWidth
            value={distro}
            onChange={(event) => setDistro(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={5}>
          <TextField
            label="Base ISO URL"
            fullWidth
            value={baseIsoUrl}
            onChange={(event) => setBaseIsoUrl(event.target.value)}
          />
        </Grid>
        <Grid item xs={12} md={3}>
          <Button variant="outlined" component="label">
            Upload ISO
            <input
              type="file"
              hidden
              onChange={(event) =>
                setBaseIsoFile(event.target.files?.[0] ?? null)
              }
            />
          </Button>
        </Grid>
        <Grid item xs={12} md={1}>
          <Button variant="contained" onClick={handleSubmit}>
            Build
          </Button>
        </Grid>
      </Grid>
    </Box>
  );
}
