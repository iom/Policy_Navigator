from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# Define the models
class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column()
    fileurl: Mapped[str] = mapped_column()
    page: Mapped[str] = mapped_column()
    typedoc: Mapped[str] = mapped_column()
    pagenumber: Mapped[int] = mapped_column()
    chunk: Mapped[int] = mapped_column()
    # Embeddings for different models:
    embedding_3l: Mapped[Vector] = mapped_column(Vector(1024), nullable=True)  # text-embedding-3-large

    def to_dict(self, include_embedding: bool = False):
        model_dict = {column.name: getattr(self, column.name) for column in self.__table__.columns}
        if include_embedding:
            model_dict["embedding_3l"] = model_dict.get("embedding_3l", [])
        else:
            del model_dict["embedding_3l"]
        return model_dict

    def to_str_for_rag(self):
        return f"Name:{self.name} Description:{self.description} Price:{self.price} Brand:{self.brand} Type:{self.type}"

    def to_str_for_embedding(self):
        return f"Name: {self.name} Description: {self.description} Type: {self.type}"


"""
**Define HNSW index to support vector similarity search**

We use the vector_cosine_ops access method (cosine distance)
 since it works for both normalized and non-normalized vector embeddings
If you know your embeddings are normalized,
 you can switch to inner product for potentially better performance.
The index operator should match the operator used in queries.
"""

table_name = Item.__tablename__

index_3l = Index(
    f"hnsw_index_for_cosine_{table_name}_embedding_3l",
    Item.embedding_3l,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding_3l": "vector_cosine_ops"},
)

