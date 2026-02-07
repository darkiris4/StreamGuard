import { DataGrid, GridColDef, GridToolbar } from "@mui/x-data-grid";
import { Card } from "@mui/material";

type Props = {
  rows: Record<string, unknown>[];
  columns: GridColDef[];
};

export default function ReportDataGrid({ rows, columns }: Props) {
  return (
    <Card sx={{ height: 420 }}>
      <DataGrid
        rows={rows}
        columns={columns}
        getRowId={(row) => row.id ?? row.rule_id ?? `${row.host}-${row.rule}`}
        slots={{ toolbar: GridToolbar }}
        disableRowSelectionOnClick
      />
    </Card>
  );
}
