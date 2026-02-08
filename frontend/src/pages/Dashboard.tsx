import { useEffect, useState } from "react";
import { Alert, Grid, Typography } from "@mui/material";

import ComplianceGauge from "../components/ComplianceGauge";
import SeverityPie from "../components/SeverityPie";
import TopFailsTable from "../components/TopFailsTable";
import TimelineChart from "../components/TimelineChart";
import HostMatrix from "../components/HostMatrix";
import {
  dashboardSeverity,
  dashboardSummary,
  dashboardTimeline,
  dashboardTopFailures,
} from "../api/endpoints";

export default function Dashboard() {
  const [summary, setSummary] = useState({
    fleet_score: 0,
    total_hosts: 0,
    critical_fails: 0,
  });
  const [severity, setSeverity] = useState({
    high: 0,
    medium: 0,
    low: 0,
  });
  const [timeline, setTimeline] = useState<{ time: string; score: number }[]>(
    []
  );
  const [topFails, setTopFails] = useState<
    { id: string; title: string; failures: number; trend: number[] }[]
  >([]);

  useEffect(() => {
    const load = async () => {
      const [summaryRes, severityRes, timelineRes, topRes] = await Promise.all([
        dashboardSummary(),
        dashboardSeverity(),
        dashboardTimeline(),
        dashboardTopFailures(),
      ]);
      setSummary(summaryRes.data);
      setSeverity(severityRes.data);
      setTimeline(
        timelineRes.data.map((item: { date: string; score: number }) => ({
          time: item.date,
          score: item.score,
        }))
      );
      setTopFails(
        topRes.data.map(
          (item: { rule_id: string; title: string; count: number }) => ({
            id: item.rule_id,
            title: item.title || item.rule_id,
            failures: item.count,
            trend: [item.count],
          })
        )
      );
    };
    load();
  }, []);

  const severityData = [
    { name: "High", value: severity.high },
    { name: "Medium", value: severity.medium },
    { name: "Low", value: severity.low },
  ];

  const hostMatrixRows = [
    {
      id: "fleet",
      host: "Fleet",
      score: summary.fleet_score,
      cat1: severity.high,
      cat2: severity.medium,
      cat3: severity.low,
    },
  ];

  return (
    <>
      <Typography variant="h4" gutterBottom>
        Compliance Dashboard
      </Typography>
      <Alert severity="warning" sx={{ mb: 2 }}>
        StreamGuard v1 runs in single-user mode — do not expose publicly without
        adding authentication.
      </Alert>
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 4 }}>
          <ComplianceGauge value={summary.fleet_score} />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <SeverityPie data={severityData} />
        </Grid>
        <Grid size={{ xs: 12, md: 4 }}>
          <TimelineChart data={timeline} />
        </Grid>
        <Grid size={12}>
          <TopFailsTable rows={topFails} />
        </Grid>
        <Grid size={12}>
          <HostMatrix rows={hostMatrixRows} />
        </Grid>
      </Grid>
    </>
  );
}
