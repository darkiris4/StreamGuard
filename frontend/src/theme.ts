import { createTheme } from "@mui/material/styles";

const theme = createTheme({
  palette: {
    mode: "dark",
    primary: {
      main: "#4fc3f7",
    },
    secondary: {
      main: "#7c4dff",
    },
    background: {
      default: "#0b0f14",
      paper: "#121821",
    },
  },
  shape: {
    borderRadius: 8,
  },
});

export default theme;
