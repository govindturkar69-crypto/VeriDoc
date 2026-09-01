# Database Documentation

## 1. Database Technology
The project **does not use a traditional database engine** (like PostgreSQL, MongoDB, or even a dedicated vector database like ChromaDB or Pinecone). 

Instead, it implements a **custom in-memory vector store** using a Python dictionary containing metadata and NumPy arrays, serialized to disk using Python's built-in `pickle` module.

> **Note:** Despite the existence of a directory named `chroma_db/`, the ChromaDB library is *not* used. This is a naming artifact.

## 2. Storage Location
- **File:** `chroma_db/store.pkl`
- The file is created automatically when `index_store.py` (or the "Add and rebuild index" button in the UI) is executed.

## 3. Data Structure (Schema)
The serialized object is a single Python dictionary with the following structure:

| Key | Data Type | Description |
|---|---|---|
| `ids` | `list[str]` | Unique identifiers for each chunk. Format: `{filename}::p{page_num}::c{chunk_index}` |
| `texts` | `list[str]` | The actual text content of the chunk. |
| `sources` | `list[str]` | The source filename (e.g., `fees_policy.pdf`). |
| `pages` | `list[int]` | The page number where the chunk originated (0 for non-paginated formats). |
| `vectors` | `numpy.ndarray` | A 2D array of shape `(N, 384)` containing the float32 embeddings for all chunks. |

## 4. Relationships
- Each index in the lists (`ids`, `texts`, `sources`, `pages`) corresponds to the row index in the `vectors` NumPy array.
- E.g., `texts[5]` is the text for the embedding at `vectors[5]`.

## 5. Operations
- **Read:** On startup (or first query), `load_store()` reads the entire `store.pkl` file into RAM.
- **Write:** When rebuilding the index, the *entire* index is regenerated from scratch by parsing all documents in the `documents/` folder. The `store.pkl` file is completely overwritten. There are no partial updates or upserts.
- **Query (Similarity Search):** Performed via matrix multiplication (dot product) between the query vector and the `vectors` array: `sims = store["vectors"] @ q_vec`.

## 6. Constraints and Validation
- **No strict schema enforcement:** Relies on Python application logic (`index_store.py`) to maintain parallel list lengths and array shapes.
- **Concurrency:** Not safe for concurrent writes. (Not an issue currently as Streamlit handles uploads sequentially and rebuilds the entire file).
