"""
OpenSearch DB에 E5 임베딩 모델을 적용하기 위한 커스텀 어댑터
"""
import numpy as np
from embedding_model import E5QEmbeddings
import requests
import json

from dotenv import load_dotenv
import os
load_dotenv()

open_search_url = {
    "local": "",
    "dev": os.getenv("OPENSEARCH_HOST_DEV"),
    "stg": os.getenv("OPENSEARCH_HOST_STG"),
    "prd": os.getenv("OPENSEARCH_HOST_PRD")
}

class Base_Request():
    def get_request(self, url):
        try:
            res = requests.get(url)
            return json.loads(res.text)
        except Exception as e:
            print(e)
        return str(e)

    def post_request(self, url, data):
        try:
            res = requests.post(url, data=json.dumps(data), headers={'Content-Type': 'application/json; charset=utf-8'})
            return json.loads(res.text)
        except Exception as e:
            print(e)
        return str(e)

    def put_request(self, url, data):
        try:
            res = requests.put(url, data=json.dumps(data), headers={'Content-Type': 'application/json; charset=utf-8'})
            return json.loads(res.text)
        except Exception as e:
            print(e)
        return str(e)

    def del_request(self, url):
        try:
            res = requests.delete(url)
            return [True, ""]
        except Exception as e:
            print(e)
        return [False, str(e)]


class E5OpenSearchEmbeddings(Base_Request):
    def __init__(self):
        env = 'dev' #config.ENV
        self.open_search_id = os.getenv("OPENSEARCH_USER")
        self.open_search_pw = os.getenv("OPENSEARCH_PASSWORD")
        self.open_search_url = open_search_url[env]
        #print(f"OpenSearch URL: {self.open_search_url}")

        self.embedder = E5QEmbeddings()

    def get_opensearch_info(self):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}"
        return self.get_request(URL)

    def get_index_info(self, open_search_index='EM_chunk'):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}/{open_search_index.lower()}"
        return self.get_request(URL)

    def delete_index(self, open_search_index='EM_chunk'):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}/{open_search_index.lower()}"
        return self.del_request(URL)

    def create_index(self, open_search_index='EM_chunk'):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}/{open_search_index.lower()}"

        data = {
            "settings": {
                "index.knn": "true"
            },
            "mappings": {
                "properties": {
                    "text_embedding": {
                        "type": "knn_vector",
                        "dimension": 1024
                    },
                    "text": {
                        "type": "text"
                    },
                    "id": {
                        "type": "keyword"
                    }
                }
            }
        }

        return self.put_request(URL, data)

    def search_item(self, query, open_search_index='EM_chunk'):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}/{open_search_index.lower()}/_search/?pretty=true&filter_path=-hits.hits._source.text_embedding"
        data_old = {
            "from": 0, "size": 100, 
            "query": {
                "script_score": {
                    "query": {
                        "match_all": {}
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, doc['text_embedding']) + 1.0",
                        "params": {
                            "query_vector": self.embedder.embed_query(query).tolist()
                        }
                    }
                }
            }
        }
        data = {
            "_source": {
                "excludes": "text_embedding"
            },
            "query": {
                "script_score": {
                    "query": {
                        "match_all": {}
                    },
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, doc['text_embedding']) + 1.0",
                        "params": {
                            "query_vector": self.embedder.embed_query(query).tolist()
                        }
                    }
                }
            },
            "sort": [
                {
                    "_score": {
                        "order": "desc"
                    }
                }
            ],
            "size": 10
        }

        return self.post_request(URL, data)

    def create_item(self, id, chunk_text, open_search_index='EM_chunk'):
        URL = f"https://{self.open_search_id}:{self.open_search_pw}@{self.open_search_url}/{open_search_index.lower()}/_doc/"

        data = {
            "text": chunk_text,
            "id": id,
            "text_embedding": self.embedder.embed_query(chunk_text).tolist()
        }

        return self.post_request(URL, data)
