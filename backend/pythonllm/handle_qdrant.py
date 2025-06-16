import os
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
import json
import torch
from tqdm import tqdm
# Get the absolute path of the project root directory
# PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_qdrant_client(url: str, api_key: str) -> QdrantClient:
    return QdrantClient(
        url=url,
        api_key=api_key,
        prefer_grpc=False
    )

def initialize_qdrant_collection(client: QdrantClient, collection_name: str, vector_name_1: str, vector_name_2: str, vector_size: int, vector_distance: Distance) -> None:
    """
    Initialize Qdrant collection and load corpus embeddings if collection doesn't exist.
    
    Args:
        client: QdrantClient instance
        collection_name: str
        vector_name_1: str
        vector_name_2: str
        vector_size: int
        vector_distance: Distance
    """
    # Create collection if it doesn't exist
    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config={
                vector_name_1: VectorParams(
                    size=vector_size,
                    distance=vector_distance
                ),
                vector_name_2: VectorParams(
                    size=vector_size,
                    distance=vector_distance
                )
            }
        )
        print(f"Created collection: {collection_name}")
        
        # Load corpus embeddings
        try:
            corpus_embeddings_1 = torch.load(os.path.join(BACKEND_ROOT, "embedding/corpus_embeddings_v1.pt"), weights_only=False)
            corpus_embeddings_2 = torch.load(os.path.join(BACKEND_ROOT, "embedding/corpus_embeddings_v2.pt"), weights_only=False)
            with open(os.path.join(BACKEND_ROOT, "dataset/all_docs.json"), "r", encoding="utf-8") as f:
                all_docs = json.load(f)
            with open(os.path.join(BACKEND_ROOT, "dataset/all_doc_metas.json"), 'r', encoding='utf-8') as f:
                all_doc_metas = json.load(f)
            batch_size = 1000
            points = [
                PointStruct(
                    id=idx,
                    vector={
                        vector_name_1: corpus_embeddings_1[idx],
                        vector_name_2: corpus_embeddings_2[idx],
                    },
                    payload={"chunk_text": all_docs[idx], "corpus_id": f"corpus_{idx}", **all_doc_metas[idx]}
                )
                for idx in range(len(all_docs))
            ]
            for i in tqdm(range(0, len(points), batch_size)):
                batch = points[i:i+batch_size]
                client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
            
            print("Loaded corpus embeddings successfully")
        except Exception as e:
            print(f"Error loading corpus embeddings: {e}")

def delete_qdrant_collection(client: QdrantClient, collection_name: str) -> None:
    """
    Delete the Qdrant collection.
    
    Args:
        client: QdrantClient instance
        collection_name: str
    """
    if client.collection_exists(collection_name):
        client.delete_collection(collection_name=collection_name)