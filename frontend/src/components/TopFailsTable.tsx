import {
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { Line, LineChart, ResponsiveContainer } from "recharts";

type Props = {
  rows: { id: string; title: string; failures: number; trend: number[] }[];
};

export default function TopFailsTable({ rows }: Props) {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle1" gutterBottom>
          Top Failing Rules
        </Typography>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Rule</TableCell>
              <TableCell>Failures</TableCell>
              <TableCell>Trend</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.id}>
                <TableCell>{row.title}</TableCell>
                <TableCell>{row.failures}</TableCell>
                <TableCell sx={{ width: 120 }}>
                  <ResponsiveContainer width="100%" height={40}>
                    <LineChart
                      data={row.trend.map((value, index) => ({
                        index,
                        value,
                      }))}
                    >
                      <Line
                        type="monotone"
                        dataKey="value"
                        stroke="#4fc3f7"
                        dot={false}
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
