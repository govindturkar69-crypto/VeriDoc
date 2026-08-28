import unittest
from unittest.mock import patch

import numpy as np

import retriever


class RetrieverTests(unittest.TestCase):
    @patch.object(retriever.config, "USE_RERANK", False)
    @patch.object(retriever, "get_embedder")
    @patch.object(retriever, "load_store")
    def test_limits_results_to_selected_documents(self, load_store, get_embedder):
        load_store.return_value = {
            "ids": ["a", "b"],
            "texts": ["first", "second"],
            "sources": ["one.pdf", "two.pdf"],
            "pages": [1, 2],
            "vectors": np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32),
        }
        get_embedder.return_value.encode.return_value = np.array(
            [[1.0, 0.0]], dtype=np.float32
        )

        results = retriever.retrieve("question", allowed_sources={"two.pdf"})

        self.assertEqual([result.source for result in results], ["two.pdf"])


if __name__ == "__main__":
    unittest.main()
