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

    @patch.object(answer, "_call_llm")
    @patch.object(answer, "retrieve")
    def test_llm_failure_sets_is_error_flag(self, retrieve, call_llm):
        retrieve.return_value = [retriever.Passage("policy text", "policy.pdf", 1, 0.9)]
        call_llm.side_effect = ConnectionError("Ollama server unreachable")

        result = answer.ask("What is the fee?")

        self.assertTrue(result.is_error)
        self.assertFalse(result.refused)
        self.assertEqual(result.passages, [])
        self.assertIn("Ollama server unreachable", result.error_message)

    def test_multilingual_refusal_detection(self):
        # English
        self.assertTrue(answer.is_refusal("I could not find this information in the official documents."))
        self.assertTrue(answer.is_refusal("This information was not found in the official documents."))
        # Hindi
        self.assertTrue(answer.is_refusal("आधिकारिक दस्तावेज़ों में यह जानकारी नहीं मिली।"))
        self.assertTrue(answer.is_refusal("दस्तावेजों में यह जानकारी उपलब्ध नहीं है।"))
        # Marathi
        self.assertTrue(answer.is_refusal("अधिकृत कागदपत्रांमध्ये ही माहिती आढळली नाही."))
        self.assertTrue(answer.is_refusal("याबद्दल माहिती सापडली नाही."))
        # Valid answer
        self.assertFalse(answer.is_refusal("The semester fee is Rs 45,000 payable by August 15."))


class UtilityTests(unittest.TestCase):
    def test_stable_sigmoid_handles_extremes_without_overflow(self):
        self.assertAlmostEqual(retriever._stable_sigmoid(0.0), 0.5)
        self.assertEqual(retriever._stable_sigmoid(-1000.0), 0.0)
        self.assertEqual(retriever._stable_sigmoid(1000.0), 1.0)


if __name__ == "__main__":
    unittest.main()
