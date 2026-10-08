"""
Chroma DB에 E5 임베딩 모델을 적용하기 위한 커스텀 어댑터
"""
import numpy as np
from embedding_model import E5QEmbeddings


class E5ChromaEmbeddings:
    """Chroma가 사용할 수 있는 E5 임베딩 래퍼"""
    
    def __init__(self):
        self.embedder = E5QEmbeddings()
    
    def name(self) -> str:
        """ChromaDB가 요구하는 embedding_function의 name 메소드"""
        return "E5ChromaEmbeddings"
    
    def __call__(self, input):
        """
        input: str 또는 List[str]
        output: List[List[float]] 형태의 임베딩 벡터
        """
        if isinstance(input, str):
            # 단일 텍스트
            embedding = self.embedder.embed_query(input)
            return [embedding.tolist()]
        elif isinstance(input, list):
            # 리스트 형태
            embeddings = []
            for text in input:
                #print(f"Embedding text: {text[:30]}...")  # 임베딩할 텍스트 일부 출력
                embedding = self.embedder.embed_query(text)
                #print(f"Embedding vector (first 5 values): {embedding[:5]}")  # 임베딩 벡터 일부 출력
                embeddings.append(embedding.tolist())
            return embeddings
        else:
            raise ValueError(f"Unsupported input type: {type(input)}")

    def embed_documents(self, input):
        """ChromaDB가 요구하는 embed_documents 메소드"""
        return self.__call__(input)
    
    def embed_query(self, input):
        """ChromaDB가 요구하는 embed_query 메소드"""
        return self.__call__(input)