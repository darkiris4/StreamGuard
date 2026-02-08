import { useEffect, useState } from "react";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Chip,
  CircularProgress,
  Grid,
  MenuItem,
  TextField,
  Typography,
} from "@mui/material";
import { GridColDef } from "@mui/x-data-grid";

import {
  runAudit,
  getCacDistros,
  getCacProfiles,
  listHosts,
} from "../api/endpoints";
import ReportDataGrid from "../components/ReportDataGrid";

interface HostOption {
  id: number;
  alias: string;
  hostname: string;
}

interface ProfileOption {
  id: string;
  title: string;
}

const columns: GridColDef[] = [
  { field: "rule_id", headerName: "Rule ID", flex: 1 },
  { field: "severity", headerName: "Severity", width: 120 },
  { field: "status", headerName: "Status", width: 120 },
  { field: "host", headerName: "Host", width: 160 },
];

export default function Audit() {
  // --- data sources ---
  const [hostOptions, setHostOptions] = useState<HostOption[]>([]);
  const [distroOptions, setDistroOptions] = useState<string[]>([]);
  const [profileOptions, setProfileOptions] = useState<ProfileOption[]>([]);
  const [profilesLoading, setProfilesLoading] = useState(false);

  // --- form state ---
  const [selectedHosts, setSelectedHosts] = useState<HostOption[]>([]);
  const [distro, setDistro] = useState("");
  const [profileName, setProfileName] = useState("");
  const [profilePath, setProfilePath] = useState("");

  // --- results ---
  const [rows, setRows] = useState<Record<string, unknown>[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Load host list + distro list on mount
  useEffect(() => {
    listHosts().then((res) => setHostOptions(res.data));
    getCacDistros().then((res) => setDistroOptions(res.data.distros));
  }, []);

  // When distro changes, load available profiles
  useEffect(() => {
    if (!distro) {
      setProfileOptions([]);
      setProfileName("");
      return;
    }
    setProfilesLoading(true);
    getCacProfiles(distro)
      .then((res) => {
        const profiles: ProfileOption[] = res.data.profiles || [];
        setProfileOptions(profiles);
        // Auto-select first profile if available
        if (profiles.length > 0 && !profileName) {
          setProfileName(profiles[0].id);
        }
      })
      .catch(() => {
        setProfileOptions([]);
      })
      .finally(() => setProfilesLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [distro]);

  const checkAndSubmit = async () => {
    setError("");

    if (!selectedHosts.length) {
      setError("Select at least one host.");
      return;
    }
    if (!distro) {
      setError("Select a distro.");
      return;
    }

    return handleSubmit();
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await runAudit({
        hosts: selectedHosts.map((h) => h.hostname),
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

  /** Extract a short display label from a long XCCDF profile id */
  const shortProfileLabel = (id: string) => {
    // e.g. "xccdf_org.ssgproject.content_profile_stig" → "stig"
    const parts = id.split("_");
    return parts[parts.length - 1] || id;
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Audit Hosts
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError("")}>
          {error}
        </Alert>
      )}

      <Grid container spacing={2} sx={{ mb: 2 }}>
        {/* Hosts — multi-select autocomplete */}
        <Grid item xs={12} md={4}>
          <Autocomplete
            multiple
            options={hostOptions}
            getOptionLabel={(opt) =>
              opt.alias ? `${opt.alias} (${opt.hostname})` : opt.hostname
            }
            value={selectedHosts}
            onChange={(_e, value) => setSelectedHosts(value)}
            renderTags={(value, getTagProps) =>
              value.map((opt, index) => (
                <Chip
                  label={opt.alias || opt.hostname}
                  size="small"
                  {...getTagProps({ index })}
                  key={opt.id}
                />
              ))
            }
            renderInput={(params) => (
              <TextField {...params} label="Hosts" placeholder="Select hosts" />
            )}
          />
        </Grid>

        {/* Distro dropdown */}
        <Grid item xs={12} md={2}>
          <TextField
            select
            label="Distro"
            fullWidth
            value={distro}
            onChange={(e) => {
              setDistro(e.target.value);
              setProfileName("");
            }}
          >
            {distroOptions.map((d) => (
              <MenuItem key={d} value={d}>
                {d}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        {/* Profile dropdown */}
        <Grid item xs={12} md={3}>
          <TextField
            select
            label="Profile"
            fullWidth
            value={profileName}
            onChange={(e) => setProfileName(e.target.value)}
            disabled={!distro || profilesLoading}
            helperText={
              profilesLoading
                ? "Loading profiles…"
                : !distro
                  ? "Select a distro first"
                  : profileOptions.length === 0
                    ? "No profiles cached — fetch content first"
                    : undefined
            }
          >
            {profileOptions.map((p) => (
              <MenuItem key={p.id} value={p.id}>
                {shortProfileLabel(p.id)} — {p.title}
              </MenuItem>
            ))}
          </TextField>
        </Grid>

        {/* Profile path override */}
        <Grid item xs={12} md={2}>
          <TextField
            label="Path override"
            fullWidth
            value={profilePath}
            onChange={(e) => setProfilePath(e.target.value)}
            helperText="Optional manual path"
            size="small"
            sx={{ mt: "4px" }}
          />
        </Grid>

        <Grid item xs={12} md={1} display="flex" alignItems="center">
          <Button
            variant="contained"
            onClick={checkAndSubmit}
            disabled={loading}
            startIcon={
              loading ? <CircularProgress size={16} /> : undefined
            }
          >
            Run
          </Button>
        </Grid>
      </Grid>

      <ReportDataGrid rows={rows} columns={columns} />
    </Box>
  );
}
