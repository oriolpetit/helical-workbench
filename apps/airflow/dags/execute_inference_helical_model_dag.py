import logging
from typing import Dict, Any

from airflow.sdk import DAG, task, Param, get_current_context

with DAG(
        "execute_inference_helical_model_dag",
        params={
            "data_path": Param("helical-ai/yolksac_human", type="string"),
            "model_name": Param("geneformer", type="string"),
            "results_path": Param(None, type="string"),
            "parameters": Param({}, type="object"),
        },
) as dag:
    @task.python
    def inference_task():
        ctx = get_current_context()
        logger = logging.getLogger("airflow.task")
        logger.info("Triggering imports")
        import os
        import numpy as np

        from datasets import load_dataset
        from helical.models.base_models import HelicalBaseFoundationModel
        from helical.models.c2s import Cell2Sen, Cell2SenConfig
        from helical.models.caduceus import Caduceus, CaduceusConfig
        from helical.models.evo_2 import Evo2, Evo2Config
        from helical.models.geneformer import Geneformer, GeneformerConfig
        from helical.models.genept import GenePT, GenePTConfig
        from helical.models.helix_mrna import HelixmRNA, HelixmRNAConfig
        from helical.models.hyena_dna import HyenaDNA, HyenaDNAConfig
        from helical.models.mamba2_mrna import Mamba2mRNA, Mamba2mRNAConfig
        from helical.models.scgpt import scGPT, scGPTConfig
        from helical.models.tahoe import Tahoe, TahoeConfig
        from helical.models.transcriptformer import TranscriptFormer, TranscriptFormerConfig
        from helical.models.uce import UCE, UCEConfig
        from helical.utils import get_anndata_from_hf_dataset

        data_path = ctx["params"]["data_path"]
        model_name = ctx["params"]["model_name"]
        results_path = ctx["params"]["results_path"]
        parameters = ctx["params"]["parameters"]
        logger.info(f"Running inference with {model_name=} on {data_path=} with {results_path=} {parameters=}")

        dataset = load_dataset(data_path, split="train[:10%]", trust_remote_code=True, download_mode="reuse_cache_if_exists")
        logger.info(f"Dataset loaded from '{data_path}' (split: train[:10%])")

        ann_data = get_anndata_from_hf_dataset(dataset)
        logger.info(f"Converted dataset to AnnData: {ann_data.shape[0]} cells, {ann_data.shape[1]} genes")

        def model_factory(model_name: str, params: Dict[str, Any] | None = None) -> HelicalBaseFoundationModel:
            params = params or {}
            if model_name == 'c2s':
                return Cell2Sen(configurer=Cell2SenConfig(**params))
            elif model_name == 'caduceus':
                return Caduceus(configurer=CaduceusConfig(**params))
            elif model_name == 'evo_2':
                return Evo2(configurer=Evo2Config(**params))
            elif model_name == 'geneformer':
                return Geneformer(configurer=GeneformerConfig(**params))
            elif model_name == 'genept':
                return GenePT(configurer=GenePTConfig(**params))
            elif model_name == 'helix_mrna':
                return HelixmRNA(configurer=HelixmRNAConfig(**params))
            elif model_name == 'hyena_dna':
                return HyenaDNA(configurer=HyenaDNAConfig(**params))
            elif model_name == 'mamba2_mrna':
                return Mamba2mRNA(configurer=Mamba2mRNAConfig(**params))
            elif model_name == 'scgpt':
                return scGPT(configurer=scGPTConfig(**params))
            elif model_name == 'tahoe':
                return Tahoe(configurer=TahoeConfig(**params))
            elif model_name == 'transcriptformer':
                return TranscriptFormer(configurer=TranscriptFormerConfig(**params))
            elif model_name == 'uce':
                return UCE(configurer=UCEConfig(**params))
            else:
                raise ValueError(f"Unsupported model: {model_name}")

        model = model_factory(model_name, parameters)

        logger.info("Tokenizing data (1 sample)")
        dataset = model.process_data(ann_data[:1], gene_names="gene_name")
        logger.info("Data tokenized successfully")

        logger.info("Generating embeddings")
        embeddings = model.get_embeddings(dataset)
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
