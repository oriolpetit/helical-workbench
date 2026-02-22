"use client";

import { useState } from "react";
import { TextInput, Select, Textarea, Button, Stack, Alert } from "@mantine/core";
import { useForm } from "@mantine/form";
import type { InferenceJobRun, Model } from "../services/backend/types.gen";
import { createInferenceJobRunInferenceJobRunsPost } from "../services/backend/sdk.gen";

interface JobLaunchFormProps {
  onJobCreated: (job: InferenceJobRun) => void;
}

export function JobLaunchForm({ onJobCreated }: JobLaunchFormProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const form = useForm({
    initialValues: {
      data_path: "helical-ai/yolksac_human",
      model: "geneformer" as string,
      parameters: "",
    },
  });

  async function handleSubmit(values: typeof form.values) {
    setLoading(true);
    setError(null);
    setSuccess(false);

    let parameters: Record<string, unknown> | undefined;
    if (values.parameters.trim()) {
      try {
        parameters = JSON.parse(values.parameters);
      } catch {
        setError("Invalid JSON in parameters field");
        setLoading(false);
        return;
      }
    }

    const result = await createInferenceJobRunInferenceJobRunsPost({
      body: {
        inputs: {
          data_path: values.data_path,
          model: values.model as Model,
          parameters,
        },
      },
    });

    setLoading(false);

    if (result.error) {
      setError("Failed to create job. Please try again.");
      return;
    }

    if (result.data) {
      setSuccess(true);
      onJobCreated(result.data);
      form.reset();
    }
  }

  return (
    <form onSubmit={form.onSubmit(handleSubmit)}>
      <Stack gap="md">
        {error && (
          <Alert color="red" title="Error" onClose={() => setError(null)} withCloseButton>
            {error}
          </Alert>
        )}
        {success && (
          <Alert color="green" title="Job submitted" onClose={() => setSuccess(false)} withCloseButton>
            Job created successfully. Check the Jobs tab to monitor progress.
          </Alert>
        )}
        <TextInput
          label="Dataset path"
          description="HuggingFace dataset path"
          required
          {...form.getInputProps("data_path")}
        />
        <Select
          label="Model"
          required
          data={[
            { value: "c2s", label: "Cell2Sentence (c2s)" },
            { value: "geneformer", label: "Geneformer" },
            { value: "genept", label: "GenePT" },
            { value: "helix_mrna", label: "Helix mRNA" },
            { value: "hyena_dna", label: "HyenaDNA" },
            { value: "mamba2_mrna", label: "Mamba2 mRNA" },
            { value: "scgpt", label: "scGPT" },
            { value: "transcriptformer", label: "TranscriptFormer" },
            { value: "uce", label: "UCE" },
          ]}
          {...form.getInputProps("model")}
        />
        <Textarea
          label="Parameters (optional JSON)"
          description="Additional model parameters as JSON object"
          placeholder='{"batch_size": 32}'
          rows={4}
          {...form.getInputProps("parameters")}
        />
        <Button type="submit" loading={loading}>
          Submit Job
        </Button>
      </Stack>
    </form>
  );
}
