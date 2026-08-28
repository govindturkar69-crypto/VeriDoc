import unittest
from unittest.mock import patch

import numpy as np

import answer
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


class AnswerTests(unittest.TestCase):
    @patch.object(answer, "_call_llm")
    @patch.object(answer, "retrieve")
    def test_detailed_mode_changes_the_grounding_prompt(self, retrieve, call_llm):
        retrieve.return_value = [retriever.Passage("policy text", "policy.pdf", 1, 0.9)]
        call_llm.return_value = "Supported answer"

        result = answer.ask("Explain the policy", detail="Detailed")

        self.assertEqual(result.text, "Supported answer")
        self.assertIn("structured answer", call_llm.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
