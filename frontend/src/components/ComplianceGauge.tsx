import { Card, CardContent, Typography } from "@mui/material";
import { Gauge } from "@mui/x-charts/Gauge";

type Props = {
  value: number;
};

export default function ComplianceGauge({ value }: Props) {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle1" gutterBottom>
          Compliance Score
        </Typography>
        <Gauge width={200} height={140} value={value} min={0} max={100} />
      </CardContent>
    </Card>
  );
}
