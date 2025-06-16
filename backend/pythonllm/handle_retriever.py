from langchain_core.retrievers import BaseRetriever
from typing import List, Any
from langchain.schema import Document
from qdrant_client import models
import json
from pydantic import Field
import re

class FusionRetriever(BaseRetriever):
    client: Any = Field(...)
    embeddings_1: Any = Field(...)
    embeddings_2: Any = Field(...)
    collection_name: str = Field(...)
    vector_name_1: str = Field(default="vn-law-embedding_1")
    vector_name_2: str = Field(default="vn-law-embedding_2")

    def __init__(
        self, 
        client,
        embeddings_1,
        embeddings_2,
        collection_name,
        vector_name_1="vn-law-embedding_1",
        vector_name_2="vn-law-embedding_2"
    ):
        super().__init__(
            client=client,
            embeddings_1=embeddings_1,
            embeddings_2=embeddings_2,
            collection_name=collection_name,
            vector_name_1=vector_name_1,
            vector_name_2=vector_name_2
        )

    def _get_relevant_documents(self, query: str) -> List[Document]:
        # Generate embeddings using both models
        vector_1 = self.embeddings_1.encode(query).tolist()
        vector_2 = self.embeddings_2.encode(query).tolist()
        
        # Set up prefetch queries for both vectors
        prefetch = [
            models.Prefetch(
                query=vector_1,
                using=self.vector_name_1,
                limit=20,
            ),
            models.Prefetch(
                query=vector_2,
                using=self.vector_name_2,
                limit=20,
            ),
        ]
        
        # Query with RRF fusion
        results = self.client.query_points(
            self.collection_name,
            prefetch=prefetch,
            query=models.FusionQuery(
                fusion=models.Fusion.RRF,
            ),
            with_payload=True,
            limit=3,
        )

        return [
            Document(
                page_content=point.payload.get("chunk_text", ""),
                metadata={k:v for k, v in point.payload.items() if k != "chunk_text"}
            )
            for point in results.points
        ]

def remove_special_chars(text):
    # Giữ lại chữ cái (cả có dấu Unicode), số và khoảng trắng
    cleaned = re.sub(r"[^\w\s]", " ", text, flags=re.UNICODE)
    # Chuẩn hóa khoảng trắng
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def extract_law_name_and_article(text: str) -> str:
    """Trích xuất tên luật và số điều từ văn bản"""
    text = text.lower()
    text = remove_special_chars(text)
    match = re.search(r"điều\s+(\d+)", text, re.IGNORECASE)
    article_num = None
    law_name = None

    if match:
        article_num = match.group(1)
        if "hiến pháp" in text:
            law_name = "HIẾN PHÁP NƯỚC CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"
        elif "luật dân sự" in text:
            law_name = "BỘ LUẬT DÂN SỰ"
        elif "luật lao động" in text:
            law_name = "BỘ LUẬT LAO ĐỘNG"
        elif "luật hình sự" in text:
            law_name = "BỘ LUẬT HÌNH SỰ"
        elif "luật an toàn vệ sinh lao động" in text:
            law_name = "LUẬT AN TOÀN, VỆ SINH LAO ĐỘNG"
        elif "luật bảo hiểm xã hội" in text:
            law_name = "LUẬT BẢO HIỂM XÃ HỘI"
        elif "luật bảo vệ quyền lợi người tiêu dùng" in text:
            law_name = "LUẬT BẢO VỆ QUYỀN LỢI NGƯỜI TIÊU DÙNG"
        elif "luật công đoàn" in text:
            law_name = "LUẬT CÔNG ĐOÀN"
        elif "luật hôn nhân và gia đình" in text:
            law_name = "LUẬT HÔN NHÂN VÀ GIA ĐÌNH"
        elif "luật việc làm" in text:
            law_name = "LUẬT VIỆC LÀM"
            
    return law_name, article_num

class LawIndexRetriever(BaseRetriever):
    docs: Any = Field(...)
    metas: Any = Field(...)

    def __init__(self, doc_path: str, meta_path: str):
        with open(doc_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
        with open(meta_path, "r", encoding="utf-8") as f:
            metas = json.load(f)
        super().__init__(docs = docs, metas = metas)

    def _get_relevant_documents(self, query: str) -> List[Document]:
        law_name, article_num = extract_law_name_and_article(query)
        # print(law_name, article_num)
        if not law_name or not article_num:
            return []  # Không tìm thấy thông tin đầy đủ

        for i in range(len(self.metas)):
            meta = self.metas[i]
            if meta["law_name"] == law_name and meta["article"] == article_num:
                content = self.docs[i]
                return [Document(page_content=content, metadata={"corpus_id": f"corpus_{i}", **meta})]

        return []  # Không tìm thấy tài liệu phù hợp
