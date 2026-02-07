import { Card } from "@mui/material";
import { DataGrid, GridColDef, GridToolbar } from "@mui/x-data-grid";

type Props = {
  rows: Record<string, unknown>[];
};

const columns: GridColDef[] = [
  { field: "host", headerName: "Host", flex: 1 },
  { field: "score", headerName: "Score", width: 120 },
  { field: "cat1", headerName: "CAT I", width: 120 },
  { field: "cat2", headerName: "CAT II", width: 120 },
  { field: "cat3", headerName: "CAT III", width: 120 },
];

export default function HostMatrix({ rows }: Props) {
  return (
    <Card sx={{ height: 360 }}>
      <DataGrid
        rows={rows}
        columns={columns}
        getRowId={(row) => row.id ?? row.host}
        slots={{ toolbar: GridToolbar }}
      />
    </Card>
  );
}
