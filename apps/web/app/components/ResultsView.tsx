"use client";

import { useEffect, useState } from "react";
import { Table, Button, Text, Stack, Group, Badge, Loader, Alert } from "@mantine/core";
import type { InferenceJobRun } from "../services/backend/types.gen";

interface ResultsViewProps {
  job: InferenceJobRun;
}

const MAX_ROWS = 20;
const MAX_COLS = 8;

export function ResultsView({ job }: ResultsViewProps) {
  const [rows, setRows] = useState<number[][] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetch(`${apiUrl}/inference_job_runs/${job.id}/results`)
      .then((res) => {
        if (!res.ok) throw new Error("Failed to load results.");
        return res.text();
      })
      .then((csv) => {
        const parsed = csv
          .trim()
          .split("\n")
          .map((line) => line.split(",").map(Number));
        setRows(parsed);
      })
      .catch(() => setError("Failed to load results."))
      .finally(() => setLoading(false));
  }, [apiUrl, job.id]);

  return (
    <Stack gap="md">
      <Group gap="xl">
        <div>
          <Text size="xs" c="dimmed">Model</Text>
          <Badge>{job.inputs.model}</Badge>
        </div>
        <div>
          <Text size="xs" c="dimmed">Dataset</Text>
          <Text size="sm">{job.inputs.data_path}</Text>
        </div>
        <div>
          <Text size="xs" c="dimmed">Started</Text>
          <Text size="sm">{new Date(job.started_at).toLocaleString()}</Text>
        </div>
        {job.finished_at && (
          <div>
            <Text size="xs" c="dimmed">Finished</Text>
            <Text size="sm">{new Date(job.finished_at).toLocaleString()}</Text>
          </div>
        )}
      </Group>

      <Button
        variant="light"
        color="green"
        w="fit-content"
        onClick={async () => {
          const response = await fetch(
            `${apiUrl}/inference_job_runs/${job.id}/results`
          );
          const blob = await response.blob();
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `results_${job.id}.csv`;
          a.click();
          URL.revokeObjectURL(url);
        }}
      >
        Download CSV
      </Button>

      {loading && <Loader />}
      {error && <Alert color="red">{error}</Alert>}
      {rows && rows.length === 0 && <Text c="dimmed">No result data available.</Text>}
      {rows && rows.length > 0 && (
        <>
          <Text size="sm" c="dimmed">
            Showing first {Math.min(MAX_ROWS, rows.length)} of {rows.length} rows,{" "}
            {Math.min(MAX_COLS, rows[0]?.length ?? 0)} of {rows[0]?.length ?? 0} dimensions
          </Text>
          <Table withTableBorder withColumnBorders fz="xs" style={{ overflowX: "auto" }}>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>#</Table.Th>
                {Array.from({ length: Math.min(MAX_COLS, rows[0]?.length ?? 0) }, (_, i) => (
                  <Table.Th key={i}>dim_{i}</Table.Th>
                ))}
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {rows.slice(0, MAX_ROWS).map((row, rowIdx) => (
                <Table.Tr key={rowIdx}>
                  <Table.Td>{rowIdx}</Table.Td>
                  {row.slice(0, MAX_COLS).map((val, colIdx) => (
                    <Table.Td key={colIdx}>{val.toFixed(4)}</Table.Td>
                  ))}
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </>
      )}
    </Stack>
  );
}
