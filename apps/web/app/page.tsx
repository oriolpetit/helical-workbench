"use client";

import "./lib/api";
import { useEffect, useState } from "react";
import {
  Container,
  Title,
  Text,
  Tabs,
  Modal,
  Stack,
  Group,
} from "@mantine/core";
import type { InferenceJobRun } from "./services/backend/types.gen";
import { listInferenceJobRunsInferenceJobRunsGet } from "./services/backend/sdk.gen";
import { JobLaunchForm } from "./components/JobLaunchForm";
import { JobList } from "./components/JobList";
import { ResultsView } from "./components/ResultsView";

export default function Home() {
  const [jobs, setJobs] = useState<InferenceJobRun[]>([]);
  const [selectedJob, setSelectedJob] = useState<InferenceJobRun | null>(null);
  const [activeTab, setActiveTab] = useState<string | null>("launch");

  useEffect(() => {
    async function fetchJobs() {
      const result = await listInferenceJobRunsInferenceJobRunsGet();
      if (result.data) {
        setJobs(result.data);
      }
    }

    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  function handleJobCreated(job: InferenceJobRun) {
    setJobs((prev) => [job, ...prev]);
    setActiveTab("jobs");
  }

  return (
    <Container size="xl" py="xl">
      <Stack gap="xs" mb="xl">
        <Group>
          <Title order={1}>Helical Workbench</Title>
        </Group>
        <Text c="dimmed">
          Submit genomic model inference jobs and explore embedding results.
        </Text>
      </Stack>

      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List mb="md">
          <Tabs.Tab value="launch">Launch Job</Tabs.Tab>
          <Tabs.Tab value="jobs">Jobs {jobs.length > 0 ? `(${jobs.length})` : ""}</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="launch">
          <JobLaunchForm onJobCreated={handleJobCreated} />
        </Tabs.Panel>

        <Tabs.Panel value="jobs">
          <JobList jobs={jobs} onSelect={setSelectedJob} />
        </Tabs.Panel>
      </Tabs>

      <Modal
        opened={selectedJob !== null}
        onClose={() => setSelectedJob(null)}
        title={`Results — ${selectedJob?.inputs.model} / ${selectedJob?.id.slice(0, 8)}`}
        size="90%"
      >
        {selectedJob && <ResultsView job={selectedJob} />}
      </Modal>
    </Container>
  );
}
