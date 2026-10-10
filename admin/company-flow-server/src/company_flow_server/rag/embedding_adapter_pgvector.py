import os
from sqlalchemy import create_engine
from langchain_postgres import PGVector
from company_flow_server.rag.embedding_model import E5QEmbeddings

class E5PGVectorEmbeddings:
    """PGVector가 사용할 수 있는 E5 임베딩 래퍼"""
    
    def __init__(self, connection_string: str, collection_name: str):
        self.embedder = E5QEmbeddings()
        # engine을 동기 방식으로 생성 (langchain-postgres는 동기/비동기 모두 지원)
        self.engine = create_engine(connection_string)
        self.collection_name = collection_name
        
        # PGVector 인스턴스 생성
        self.vectorstore = PGVector(
            embeddings=self.embedder,
            collection_name=self.collection_name,
            connection=self.engine,
            use_jsonb=True
        )
        # 런타임에 테이블(langchain_pg_collection, langchain_pg_embedding)이 없으면 생성
        self.vectorstore.create_tables_if_not_exists()

    def search(self, query: str, top_k: int) -> list:
        # Langchain PGVector의 similarity_search 이용
        docs = self.vectorstore.similarity_search(query, k=top_k)
        return [doc.page_content for doc in docs]

    def add_chunks(self, chunks: list):
        self.vectorstore.add_documents(chunks)

    def drop_tables(self):
        # 전체 테이블 삭제 대신 컬렉션만 안전하게 삭제
        try:
            self.vectorstore.delete_collection()
        except Exception as e:
            print(f"컬렉션 삭제 중 오류 발생 (무시됨): {e}")
