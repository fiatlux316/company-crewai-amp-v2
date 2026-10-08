import chromadb
from embedding_adapter_opensearch import E5OpenSearchEmbeddings
from embedding_adapter_chroma import E5ChromaEmbeddings
import uuid

class VectorStoreManager:
    def __init__(self, provider: str = "opensearch"):

        self.provider = provider.lower()
        self.vector_store_client = None

        if self.provider == "opensearch":
            print("Vector Store Provider로 OpenSearch가 선택되었습니다.")
            self.vector_store_client = E5OpenSearchEmbeddings()
        elif self.provider == "chroma":
            print("Vector Store Provider로 ChromaDB가 선택되었습니다.")
            # E5 임베딩 모델 적용
            self._embedding_function = E5ChromaEmbeddings()
            self.vector_store_client = chromadb.PersistentClient(
                path="./chroma_db",
                settings=chromadb.config.Settings(anonymized_telemetry=False)
            )
        else:
            raise ValueError(f"지원하지 않는 Vector Store 제공자입니다: {provider}")    
        

    def delete_index(self, index_name: str):
        """
        기존 인덱스/컬렉션이 존재하면 삭제합니다.
        """
        if self.provider == "opensearch":
            self.vector_store_client.delete_index(index_name)
            print(f"OpenSearch '{index_name}' 인덱스가 삭제되었습니다.")
        elif self.provider == "chroma":
            try:
                self.vector_store_client.delete_collection(name=index_name)
                print(f"ChromaDB '{index_name}' 컬렉션이 삭제되었습니다.")
            except Exception:
                pass
        else:
            raise ValueError(f"지원하지 않는 Vector Store 제공자입니다: {self.provider}")


    def search_chunks(self, query: str, index_name: str, top_k: int = 3) -> list:
        """
        주어진 쿼리로 벡터 저장소를 검색하여 청크 텍스트 리스트를 반환합니다.
        """

        if self.provider == "opensearch":
            return self._search_opensearch(query, index_name, top_k)
        elif self.provider == "chroma":
            return self._search_chroma(query, index_name, top_k)
        else:
            raise ValueError(f"지원하지 않는 Vector Store 제공자입니다: {self.provider}")

    def _search_opensearch(self, query: str, index_name: str, top_k: int) -> list:
        res_embedding = self.vector_store_client.search_item(query, index_name)
        
        # 에러 응답 처리
        if isinstance(res_embedding, dict) and 'error' in res_embedding:
            return []

        cnt = res_embedding.get('hits', {}).get('total', {}).get('value', 0)
        if cnt == 0:
            return []

        chunks = []
        check_ids = set()
        
        for row in res_embedding['hits']['hits']:
            if len(chunks) >= top_k:
                break
                
            _id = row.get('_id', str(row.get('_source', {}).get('id', '')))
            
            if _id not in check_ids:
                _chunk = row['_source'].get('text', '')
                if _chunk:
                    chunks.append(_chunk)
                check_ids.add(_id)
                
        return chunks

    def _search_chroma(self, query: str, collection_name: str, top_k: int) -> list:
        if not self.vector_store_client:
            raise Exception("chromadb 패키지가 설치되지 않았습니다.")
        
        try:
            collection = self.vector_store_client.get_collection(
                name=collection_name,
                embedding_function=self._embedding_function
            )
            # E5 임베딩된 쿼리로 검색
            query_embedding = self._embedding_function([query])[0]
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            return [doc for doc in results['documents'][0]] if results and results.get('documents') else []
        except Exception as e:
            print(f"ChromaDB 검색 오류: {e}")
            return []

    def ingest_chunks(self, chunks: list, index_name: str):
        """
        생성된 청크들을 지정한 Vector Store에 삽입(인덱싱)합니다.
        """
        if self.provider == "opensearch":
            self._ingest_opensearch(chunks, index_name)
        elif self.provider == "chroma":
            self._ingest_chroma(chunks, index_name)
        else:
            raise ValueError(f"지원하지 않는 Vector Store 제공자입니다: {self.provider}")

    def _ingest_opensearch(self, chunks: list, index_name: str):
        index_info = self.vector_store_client.get_index_info(index_name)
        
        if isinstance(index_info, dict) and 'error' in index_info:
            print(f"'{index_name}' 인덱스가 존재하지 않아 새로 생성합니다...")
            self.vector_store_client.create_index(index_name)
        elif isinstance(index_info, str):
            self.vector_store_client.create_index(index_name)
        
        success_count = 0
        for idx, chunk in enumerate(chunks):
            doc_id = str(uuid.uuid4())
            print(f"[{idx+1}/{len(chunks)}] 인덱싱 중... (튜플 ID: {doc_id})")
            
            try:
                self.vector_store_client.create_item(id=doc_id, chunk_text=chunk.page_content, open_search_index=index_name)
                success_count += 1
            except Exception as e:
                print(f"인덱싱 오류 발생 (ID: {doc_id}): {e}")
                
        print(f"인덱싱 완료: 총 {success_count}개의 Chunk가 '{index_name}' 인덱스에 성공적으로 업로드되었습니다.")

    def _ingest_chroma(self, chunks: list, collection_name: str):
        if not self.vector_store_client:
            print("chromadb 패키지가 설치되지 않았습니다. 'pip install chromadb'를 실행해주세요.")
            return
            
        collection = self.vector_store_client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_function
        )
        documents = [chunk.page_content for chunk in chunks]
        ids = [str(uuid.uuid4()) for _ in chunks]
        
        print(f"ChromaDB '{collection_name}' 컬렉션에 {len(documents)}개의 청크를 인덱싱합니다...")
        
        # E5 임베딩 모델로 documents 벡터화
        embeddings = self._embedding_function(documents)
        collection.add(documents=documents, embeddings=embeddings, ids=ids)
        print(f"인덱싱 완료: 총 {len(documents)}개의 Chunk가 ChromaDB에 E5 임베딩과 함께 성공적으로 업로드되었습니다.")