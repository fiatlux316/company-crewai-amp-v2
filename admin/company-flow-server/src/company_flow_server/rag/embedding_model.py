import torch
import torch.nn.functional as F
import numpy as np
from transformers import AutoModel, AutoTokenizer
from torch import Tensor

import onnxruntime as ort
import onnx
import pathlib
import os

class E5QEmbeddings:
    def __init__(self, **kwargs):
        super().__init__()

        local_dir_nm = "multilingual-e5-large-quantized"

        if os.path.exists(local_dir_nm) is False:
            Exception("모델파일에러")

        self.model_path = pathlib.Path(local_dir_nm, 'multilingual-e5-large.opt.qint8.onnx')
        self.tokenizer_path = pathlib.Path(local_dir_nm)
        self.encoder = onnx.load(self.model_path, load_external_data=False)
        self.tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_path)
        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        provider = 'CPUExecutionProvider'
        assert provider in ort.get_all_providers(), f"provider {provider} not found"
        self.session = ort.InferenceSession(self.model_path, sess_options, providers=[provider])
        self.session.disable_fallback()

    def __pool__(self, last_hidden_states: Tensor,
                 attention_mask: Tensor,
                 pool_type: str) -> Tensor:
        last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)

        if pool_type == "avg":
            emb = last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]
        elif pool_type == "cls":
            emb = last_hidden[:, 0]
        else:
            raise ValueError(f"pool_type {pool_type} not supported")
        return emb

    @torch.no_grad()
    def embed_query(self, text: str) -> np.array:
        inputs = self.tokenizer([text], max_length=512,
                                padding=True,
                                truncation=True,
                                )
        ort_inputs = {'input_ids': inputs['input_ids'], 'attention_mask': inputs['attention_mask']}
        outputs = self.session.run(None, ort_inputs)[0]
        embeds = self.__pool__(torch.tensor(outputs[0]), torch.tensor(inputs['attention_mask']), 'avg')
        embeds = F.normalize(embeds, p=2, dim=-1).numpy()

        return embeds[0]