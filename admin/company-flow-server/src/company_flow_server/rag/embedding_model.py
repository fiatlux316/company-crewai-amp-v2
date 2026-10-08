import numpy as np
from tokenizers import Tokenizer
import onnxruntime as ort
import pathlib
import os

class E5QEmbeddings:
    def __init__(self, **kwargs):
        super().__init__()

        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__))
        local_dir_nm = os.path.join(current_dir, "multilingual-e5-large-quantized")
        
        if not os.path.exists(local_dir_nm):
            raise Exception(f"모델파일에러 (Model directory not found at {local_dir_nm})")

        self.model_path = str(pathlib.Path(local_dir_nm, 'multilingual-e5-large.opt.qint8.onnx'))
        self.tokenizer_path = str(pathlib.Path(local_dir_nm, 'tokenizer.json'))
        
        # Load Tokenizer (using huggingface tokenizers which is fast and small)
        self.tokenizer = Tokenizer.from_file(self.tokenizer_path)
        
        # Enable padding/truncation for the tokenizer
        # e5 padding token ID is typically 0 for xlm-roberta based models
        self.tokenizer.enable_truncation(max_length=512)
        self.tokenizer.enable_padding(pad_id=0, pad_token="[PAD]") 

        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        provider = 'CPUExecutionProvider'
        assert provider in ort.get_all_providers(), f"provider {provider} not found"
        
        self.session = ort.InferenceSession(self.model_path, sess_options, providers=[provider])
        self.session.disable_fallback()

    def __pool__(self, last_hidden_states: np.ndarray, attention_mask: np.ndarray, pool_type: str) -> np.ndarray:
        # last_hidden_states shape: (batch, seq_len, hidden_size)
        # attention_mask shape: (batch, seq_len)
        
        # Expand attention mask to match hidden states
        mask_expanded = np.expand_dims(attention_mask, axis=-1).astype(bool)
        
        # Fill masked tokens with 0
        last_hidden = np.where(mask_expanded, last_hidden_states, 0.0)
        
        if pool_type == "avg":
            # Sum over seq_len
            sum_embeddings = np.sum(last_hidden, axis=1)
            # Sum of mask
            sum_mask = np.clip(np.sum(attention_mask, axis=1, keepdims=True), a_min=1e-9, a_max=None)
            emb = sum_embeddings / sum_mask
        elif pool_type == "cls":
            emb = last_hidden[:, 0, :]
        else:
            raise ValueError(f"pool_type {pool_type} not supported")
        return emb

    def embed_query(self, text: str) -> list[float]:
        # Encode text
        encoded = self.tokenizer.encode(text)
        
        # Get input_ids and attention_mask
        input_ids = np.array([encoded.ids], dtype=np.int64)
        attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
        
        ort_inputs = {
            'input_ids': input_ids,
            'attention_mask': attention_mask
        }
        
        # Run ONNX Runtime
        outputs = self.session.run(None, ort_inputs)
        last_hidden_state = outputs[0]
        
        # Pool
        embeds = self.__pool__(last_hidden_state, attention_mask, 'avg')
        
        # L2 Normalize
        norms = np.linalg.norm(embeds, axis=1, keepdims=True)
        norms = np.clip(norms, a_min=1e-12, a_max=None)
        embeds = embeds / norms
        
        # Return as list for Langchain compatibility if needed, or keeping it numpy
        return embeds[0].tolist()
        
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Required by Langchain if this is used as an embeddings class
        return [self.embed_query(t) for t in texts]
