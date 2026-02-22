"use client";

import { Table, Badge, ActionIcon, Text, Tooltip } from "@mantine/core";
import type { InferenceJobRun, JobRunStatus } from "../services/backend/types.gen";

const STATUS_COLORS: Record<JobRunStatus, string> = {
  pending: "gray",
  running: "blue",
  succeeded: "green",
  failed: "red",
};

interface JobListProps {
  jobs: InferenceJobRun[];
  onSelect: (job: InferenceJobRun) => void;
}

export function JobList({ jobs, onSelect }: JobListProps) {
  if (jobs.length === 0) {
    return <Text c="dimmed">No jobs yet. Launch one from the Launch Job tab.</Text>;
  }

  return (
    <Table striped highlightOnHover>
      <Table.Thead>
        <Table.Tr>
          <Table.Th>ID</Table.Th>
          <Table.Th>Model</Table.Th>
          <Table.Th>Dataset</Table.Th>
          <Table.Th>Status</Table.Th>
          <Table.Th>Started At</Table.Th>
          <Table.Th>Actions</Table.Th>
        </Table.Tr>
      </Table.Thead>
      <Table.Tbody>
        {jobs.map((job) => (
          <Table.Tr key={job.id}>
            <Table.Td>
              <Text size="xs" ff="monospace" title={job.id}>
                {job.id.slice(0, 8)}…
              </Text>
            </Table.Td>
            <Table.Td>{job.inputs.model}</Table.Td>
            <Table.Td>
              <Text size="sm" title={job.inputs.data_path}>
                {job.inputs.data_path.length > 30
                  ? job.inputs.data_path.slice(0, 30) + "…"
                  : job.inputs.data_path}
              </Text>
            </Table.Td>
            <Table.Td>
              <Badge color={STATUS_COLORS[job.status]}>{job.status}</Badge>
            </Table.Td>
            <Table.Td>
              <Text size="sm">{new Date(job.started_at).toLocaleString()}</Text>
            </Table.Td>
            <Table.Td>
              {job.status === "succeeded" && (
                <Tooltip label="View results">
                  <ActionIcon variant="light" color="green" onClick={() => onSelect(job)}>
                    📊
                  </ActionIcon>
                </Tooltip>
              )}
              {job.status === "failed" && job.error && (
                <Tooltip label={job.error} multiline w={300}>
                  <ActionIcon variant="light" color="red">
                    ⚠
                  </ActionIcon>
                </Tooltip>
              )}
            </Table.Td>
          </Table.Tr>
        ))}
      </Table.Tbody>
    </Table>
  );
}
