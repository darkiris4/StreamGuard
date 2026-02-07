import { Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Audit from "./pages/Audit";
import Hosts from "./pages/Hosts";
import Mitigate from "./pages/Mitigate";
import IsoBuilder from "./pages/IsoBuilder";
import ProfileEditor from "./pages/ProfileEditor";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/hosts" element={<Hosts />} />
        <Route path="/audit" element={<Audit />} />
        <Route path="/mitigate" element={<Mitigate />} />
        <Route path="/iso" element={<IsoBuilder />} />
        <Route path="/profiles" element={<ProfileEditor />} />
      </Route>
    </Routes>
  );
}
