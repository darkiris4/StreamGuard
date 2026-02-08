import { useEffect, useMemo, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import {
  AppBar,
  Box,
  Chip,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Switch,
  Toolbar,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import MenuIcon from "@mui/icons-material/Menu";
import DashboardIcon from "@mui/icons-material/Dashboard";
import ComputerIcon from "@mui/icons-material/Computer";
import FactCheckIcon from "@mui/icons-material/FactCheck";
import BuildIcon from "@mui/icons-material/Build";
import LibraryBooksIcon from "@mui/icons-material/LibraryBooks";
import ImageIcon from "@mui/icons-material/Image";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import CloudIcon from "@mui/icons-material/Cloud";
import CloudOffIcon from "@mui/icons-material/CloudOff";

import { setOfflineMode, getCacStatus } from "../api/endpoints";
const logoUrl = "/assets/logo.jpg";

const drawerWidth = 260;

const navItems = [
  { label: "Dashboard", path: "/", icon: <DashboardIcon /> },
  { label: "Hosts", path: "/hosts", icon: <ComputerIcon /> },
  { label: "Audit", path: "/audit", icon: <FactCheckIcon /> },
  { label: "Mitigate", path: "/mitigate", icon: <BuildIcon /> },
  { label: "ISO Builder", path: "/iso", icon: <ImageIcon /> },
  { label: "Profiles", path: "/profiles", icon: <LibraryBooksIcon /> },
  { label: "User Guide", path: "/docs/intro", icon: <HelpOutlineIcon />, external: true },
];

export default function Layout() {
  const theme = useTheme();
  const isLgUp = useMediaQuery(theme.breakpoints.up("lg"));
  const [mobileOpen, setMobileOpen] = useState(false);
  const [offline, setOffline] = useState(false);
  const [cacheVersion, setCacheVersion] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("offlineMode");
    if (saved === "true") setOffline(true);

    // Fetch current CAC cache status on mount
    getCacStatus()
      .then((res) => {
        setCacheVersion(res.data.cache_version || "");
        // Sync mode with backend
        if (res.data.mode === "offline" && saved !== "true") {
          setOffline(true);
          localStorage.setItem("offlineMode", "true");
        }
      })
      .catch(() => {
        // Backend may not be reachable yet
      });
  }, []);

  const handleToggle = async (checked: boolean) => {
    setOffline(checked);
    localStorage.setItem("offlineMode", String(checked));
    try {
      await setOfflineMode(checked);
    } catch {
      // Tolerate backend unavailability
    }
  };

  const drawer = useMemo(
    () => (
      <Box>
        <Box sx={{ p: 2, display: "flex", alignItems: "center", gap: 2 }}>
          <Box
            component="img"
            src={logoUrl}
            alt="StreamGuard"
            sx={{ width: 40, height: 40, borderRadius: 1 }}
          />
          <Typography variant="h6">StreamGuard</Typography>
        </Box>
        <Divider />
        <List>
          {navItems.map((item) => (
            <ListItemButton
              key={item.path}
              component={item.external ? "a" : NavLink}
              to={item.external ? undefined : item.path}
              href={item.external ? item.path : undefined}
              onClick={() => setMobileOpen(false)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Box>
    ),
    []
  );

  return (
    <Box sx={{ display: "flex" }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        color="transparent"
        sx={{ zIndex: theme.zIndex.drawer + 1 }}
      >
        <Toolbar>
          {!isLgUp && (
            <IconButton
              edge="start"
              color="inherit"
              onClick={() => setMobileOpen(true)}
              sx={{ mr: 2 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          {!isLgUp && (
            <Typography variant="h6" sx={{ flexGrow: 1 }}>
              StreamGuard
            </Typography>
          )}
          {isLgUp && <Box sx={{ flexGrow: 1 }} />}
          {cacheVersion && (
            <Chip
              size="small"
              label={`CAC ${cacheVersion}`}
              sx={{ mr: 2, opacity: 0.8 }}
            />
          )}
          <Tooltip title={offline ? "Offline mode — uses local git clone" : "Online mode — fetches from GitHub releases"}>
            <Box sx={{ display: "flex", alignItems: "center" }}>
              <CloudIcon fontSize="small" sx={{ mr: 0.5, opacity: offline ? 0.3 : 1 }} />
              <Switch
                checked={offline}
                onChange={(event) => handleToggle(event.target.checked)}
                size="small"
              />
              <CloudOffIcon fontSize="small" sx={{ ml: 0.5, opacity: offline ? 1 : 0.3 }} />
            </Box>
          </Tooltip>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { lg: drawerWidth }, flexShrink: { lg: 0 } }}
      >
        <Drawer
          variant={isLgUp ? "permanent" : "temporary"}
          open={isLgUp || mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            "& .MuiDrawer-paper": {
              width: drawerWidth,
              boxSizing: "border-box",
            },
          }}
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{ flexGrow: 1, p: 3, mt: 8, width: "100%" }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
