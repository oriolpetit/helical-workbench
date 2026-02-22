from airflow.sdk import DAG, task, Param, get_current_context
import logging

with DAG(
        "execute_inference_helical_model_dag",
        params={
            "data_path": Param("helical-ai/yolksac_human", type="string"),
            "model_name": Param("geneformer", type="string"),
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
        # todo-llm Improve the message
        logger.info(f"{data_path=} {model_name=}")

        dataset = load_dataset(data_path, split="train[:10%]", trust_remote_code=True, download_mode="reuse_cache_if_exists")
        logger.info(f"dataset loaded")

        ann_data = get_anndata_from_hf_dataset(dataset)
        logger.info(f"anndata acquired")

        device = "cpu"
        logger.info(f"using device {device=}")
        model_config = GeneformerConfig(batch_size=10, device=device)
        geneformer = Geneformer(configurer=model_config)

        logger.info(f"Tokenizing data")
        dataset = geneformer.process_data(ann_data[:1], gene_names="gene_name")
        logger.info(f"Data tokenized")

        logger.info(f"Generating embeddings")
        embeddings = geneformer.get_embeddings(dataset)
        logger.info(f"embeddings generated")

        data_path = "/opt/airflow/dags/files/output.csv"
        os.makedirs(os.path.dirname(data_path), exist_ok=True)

        logger.info(f"Writing data")
        np.savetxt(data_path, embeddings, delimiter=",")
        logger.info(f"data written")

    inference_task()

if __name__ == "__main__":
    ...
    # dag.test(
    #     run_conf={"my_int_param": 42}
    # )
