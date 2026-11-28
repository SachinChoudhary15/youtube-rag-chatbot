


from abc import abstractmethod

from langchain_core.embeddings import Embeddings


class BaseEmbedding(Embeddings):

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the dimension of the embeddings."""
        raise NotImplementedError