import os
from langchain_community.document_loaders import PyPDFLoader, PyMuPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from dotenv import load_dotenv
load_dotenv()

from vs_manager import VectorStoreManager

def load_and_chunk_documents(doc_dir="docs", chunk_size=500, chunk_overlap=50):
    if not os.path.exists(doc_dir):
        print(f"문서 디렉토리가 존재하지 않습니다: {doc_dir}")
        return []

    documents = []
    
    # 1. 파일 읽기 (Text / PDF)
    for filename in os.listdir(doc_dir):
        file_path = os.path.join(doc_dir, filename)
        #print(f"Processing file: {filename}")
 
        if filename.endswith(".pdf"):
            try:
                #loader = PyPDFLoader(file_path)
                loader = PyMuPDFLoader(file_path)
                documents.extend(loader.load())
                print(f"Loaded PDF: {filename}")
            except Exception as e:
                print(f"Error loading PDF {filename}: {e}")
                
        elif filename.endswith(".txt"):
            try:
                loader = TextLoader(file_path, encoding='utf-8')
                documents.extend(loader.load())
                print(f"Loaded TXT: {filename}")
            except Exception as e:
                print(f"Error loading TXT {filename}: {e}")

    if not documents:
        print("읽어들일 문서가 없습니다. pdf 또는 txt 파일이 docs 폴더에 존재하는지 확인해주세요.")
        return []

    # 2. Chunking (일정 길이로 자르기)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"총 {len(documents)}개의 문서를 읽어 {len(chunks)}개의 Chunk로 분할했습니다.")
    return chunks


if __name__ == "__main__":
    # 1) 작업하고자 하는 문서 디렉토리명을 지정해주세요
    DOCS_DIRECTORY = "./docs" 
    
    # 디렉토리가 없다면 테스트를 위해 생성해둡니다.
    os.makedirs(DOCS_DIRECTORY, exist_ok=True)
    
    # 2. 청크사이즈, 겹침길이를 조절해주세요.
    # chunk_size: 한 청크에 들어갈 텍스트 길이 (가장 일반적인 500자 기준)
    # chunk_overlap: 문맥 단절 방지를 위해 겹치게 가져갈 글자 수단위
    chunks = load_and_chunk_documents(
        doc_dir=DOCS_DIRECTORY, 
        chunk_size=500,     
        chunk_overlap=50    
    )
    
    if chunks:
        PROVIDER = os.getenv("VS_TYPE", "chroma")
        
        # type : opensearch, chroma 중 선택
        vs_manager = VectorStoreManager(provider=PROVIDER)
        try:
            # 컬렉션(인덱스)이 이미 존재한다면 먼저 삭제 후 다시 처리
            print("기존 컬렉션/인덱스가 존재한다면 삭제를 시도합니다...")
            vs_manager.delete_index("EM_chunk")
            vs_manager.ingest_chunks(chunks=chunks, index_name="EM_chunk")
        except ValueError as e:
            print(e)
    else:
        print(f"'{DOCS_DIRECTORY}' 폴더에 txt나 pdf 문서를 추가하신 후 다시 실행해 주십시오.")
