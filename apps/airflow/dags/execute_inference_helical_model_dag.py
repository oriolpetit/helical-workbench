from airflow.sdk import DAG, task, Param, get_current_context
import logging

with DAG(
        "execute_inference_helical_model_dag",
        params={
            "data_path": Param("helical-ai/yolksac_human", type="string"),
            "model_name": Param("geneformer", type="string"),
            "results_path": Param(None, type="string"),
        },
) as dag:
    @task.python
    def inference_task():
        ctx = get_current_context()
        logger = logging.getLogger("airflow.task")
        logger.info("Triggering imports")
        import os
        import numpy as np
        import torch

        from datasets import load_dataset
        from helical.models.geneformer import Geneformer, GeneformerConfig
        from helical.utils import get_anndata_from_hf_dataset

        data_path = ctx["params"]["data_path"]
        model_name = ctx["params"]["model_name"]
        results_path = ctx["params"]["results_path"]
        logger.info(f"Running inference with {model_name=} on {data_path=} with {results_path=}")

        dataset = load_dataset(data_path, split="train[:10%]", trust_remote_code=True, download_mode="reuse_cache_if_exists")
        logger.info(f"Dataset loaded from '{data_path}' (split: train[:10%])")

        ann_data = get_anndata_from_hf_dataset(dataset)
        logger.info(f"Converted dataset to AnnData: {ann_data.shape[0]} cells, {ann_data.shape[1]} genes")

        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Initializing Geneformer model (batch_size=10, device='{device}')")
        model_config = GeneformerConfig(batch_size=10, device=device)
        geneformer = Geneformer(configurer=model_config)

        logger.info("Tokenizing data (1 sample)")
        dataset = geneformer.process_data(ann_data[:1], gene_names="gene_name")
        logger.info("Data tokenized successfully")

        logger.info("Generating embeddings")
        embeddings = geneformer.get_embeddings(dataset)
        logger.info(f"Embeddings generated: shape={embeddings.shape}")

        run_id = ctx["run_id"]
        safe_run_id = run_id.replace(":", "-").replace("+", "-")
        output_path = f"/opt/airflow/results/{results_path or safe_run_id}"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        logger.info(f"Writing embeddings to '{output_path}'")
        np.savetxt(output_path, embeddings, delimiter=",")
        logger.info(f"Embeddings written successfully to '{output_path}'")

    inference_task()

if __name__ == "__main__":
    ...
    # dag.test(
    #     run_conf={"my_int_param": 42}
    # )
