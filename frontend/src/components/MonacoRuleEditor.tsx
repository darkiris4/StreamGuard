import { Card, CardContent, Typography } from "@mui/material";
import Editor from "@monaco-editor/react";

type Props = {
  value: string;
  onChange: (value: string) => void;
};

export default function MonacoRuleEditor({ value, onChange }: Props) {
  return (
    <Card>
      <CardContent>
        <Typography variant="subtitle1" gutterBottom>
          Profile Editor
        </Typography>
        <Editor
          height="400px"
          defaultLanguage="xml"
          value={value}
          theme="vs-dark"
          onChange={(val) => onChange(val ?? "")}
        />
      </CardContent>
    </Card>
  );
}
