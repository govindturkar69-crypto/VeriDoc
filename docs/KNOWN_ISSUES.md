# Known Issues

## Missing sentence_transformers dependency

Running the test suite (python -m unittest test_retriever.py) fails with:
`
ImportError: No module named 'sentence_transformers'
`

The import occurs in index_store.py at module load time.

### How to work around it
1. **If you need full functionality (indexing, embedding):**
   pip install sentence-transformers   # pulls torch automatically
2. **If you only want to run the unit tests** (which mock the embedder):
   - You can **skip installing** the heavy library.
   - The tests will still run because the embedder is mocked in 	est_retriever.py.

### Recommended future improvement
* Move the sentence_transformers import inside get_embedder() with a clear error message if the package is missing. This will allow the repository to be cloned and its test suite to run without installing heavy ML dependencies, while still supporting full functionality when the library is present.
