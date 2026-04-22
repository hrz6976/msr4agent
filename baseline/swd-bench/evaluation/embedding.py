import json
import logging
from pathlib import Path
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import chromadb
import concurrent.futures
import numpy as np
from sklearn.preprocessing import normalize

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

REPO_NAME_SOURCE_LIST = [
    # repos
]

TARGET_REPO_NAMES = [name.split('/')[-1] for name in REPO_NAME_SOURCE_LIST]

def transform_repo_name_by_substring(original_repo_name: str) -> str:
    for target_name in TARGET_REPO_NAMES:
        if target_name in original_repo_name:
            return target_name
    return original_repo_name

class Config:
    METHODS = [
        # methods
    ]
    MODEL_NAME = 'Salesforce/SFR-Embedding-Code-400M_R'
    DEVICE = "cpu"
    BATCH_SIZE = 32
    MAX_WORKERS = 4
    CHROMA_PATH = Path("./chroma_dbs")

def setup_model_and_device(model_name, device_str):
    if device_str == "cuda" and not torch.cuda.is_available():
        logging.warning("CUDA is not available. Falling back to CPU.")
        device = "cpu"
    else:
        device = device_str
    logging.info(f"Using device: {device}")
    try:
        model = SentenceTransformer(model_name, trust_remote_code=True, device=device)
        logging.info(f"Successfully loaded model: {model_name}")
    except Exception as e:
        logging.error(f"Failed to load model {model_name}. Error: {e}")
        exit(1)
    return model

def index_method_data(method: str, client: chromadb.Client, model: SentenceTransformer, config: Config):

    input_file = Path(f"{method.lower()}_chunks.jsonl")
    collection_name = f"collection_{method.lower()}"
    logging.info(f"[{method}] Starting indexing for file: {input_file}")

    if not input_file.exists():
        logging.warning(f"[{method}] Input file not found: {input_file}. Skipping.")
        return

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"embedding_model": config.MODEL_NAME, "source_method": method, "normalized": "l2"}
    )

    with open(input_file, 'r', encoding='utf-8') as f:
        repo_records = json.load(f)

    all_potential_chunks = []
    for record in tqdm(repo_records, desc=f"[{method}] Preparing data from {input_file.name}"):
        
        original_repo_name = record.get('repo', 'unknown_repo')
        repo_name = transform_repo_name_by_substring(original_repo_name)
        for file_chunks in record.get('all_chunks', []):
            file_path = file_chunks.get('file_path', 'unknown_file')
            for i, chunk_content in enumerate(file_chunks.get('chunks', [])):
                if not chunk_content or not chunk_content.strip():
                    continue
                chunk_id = f"{repo_name}_{file_path}_{i}"
                metadata = {"repo": repo_name, "file_path": file_path, "chunk_index": i}
                all_potential_chunks.append({"id": chunk_id, "document": chunk_content, "metadata": metadata})

    if not all_potential_chunks:
        logging.warning(f"[{method}] No valid chunks found in {input_file}.")
        return

    potential_ids = [c['id'] for c in all_potential_chunks]
    existing_ids = set()
    batch_size_for_get = 20000
    logging.info(f"[{method}] Checking for {len(potential_ids)} potential chunks in the database...")
    for i in tqdm(range(0, len(potential_ids), batch_size_for_get), desc=f"[{method}] Batch checking existing IDs"):
        batch_ids = potential_ids[i : i + batch_size_for_get]
        try:
            response = collection.get(ids=batch_ids, include=[])
            existing_ids.update(response['ids'])
        except Exception as e:
            logging.error(f"[{method}] Error during batch get from ChromaDB. Batch size: {len(batch_ids)}. Error: {e}", exc_info=True)
            continue

    to_be_indexed = [chunk for chunk in all_potential_chunks if chunk['id'] not in existing_ids]

    if not to_be_indexed:
        logging.info(f"[{method}] All {len(all_potential_chunks)} chunks already indexed. Nothing to do.")
        return

    logging.info(f"[{method}] Found {len(all_potential_chunks)} total chunks. {len(existing_ids)} already indexed. Indexing {len(to_be_indexed)} new chunks.")

    contents_to_encode = [c['document'] for c in to_be_indexed]
    metadatas_to_add = [c['metadata'] for c in to_be_indexed]
    ids_to_add = [c['id'] for c in to_be_indexed]

    logging.info(f"[{method}] Encoding {len(contents_to_encode)} items...")
    embeddings_raw = model.encode(contents_to_encode, batch_size=config.BATCH_SIZE, show_progress_bar=True)

    logging.info(f"[{method}] Normalizing {len(embeddings_raw)} embeddings using L2 norm.")
    embeddings_normalized = normalize(embeddings_raw, norm='l2', axis=1)

    for i in tqdm(range(0, len(to_be_indexed), config.BATCH_SIZE), desc=f"[{method}] Adding to collection {collection.name}"):
        batch_end = i + config.BATCH_SIZE
        collection.add(
            embeddings=embeddings_normalized[i:batch_end].tolist(),
            documents=contents_to_encode[i:batch_end],
            metadatas=metadatas_to_add[i:batch_end],
            ids=ids_to_add[i:batch_end]
        )

    logging.info(f"[{method}] Finished indexing. Total items in collection '{collection.name}': {collection.count()}")

def main_indexing(client: chromadb.Client, model: SentenceTransformer, config: Config):
    logging.info("--- Starting Indexing Chunks from all Methods (Multi-threaded) ---")
    with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
        future_to_method = {executor.submit(index_method_data, method, client, model, config): method for method in config.METHODS}
        for future in concurrent.futures.as_completed(future_to_method):
            method = future_to_method[future]
            try:
                future.result()
                logging.info(f"Successfully completed indexing for method: {method}")
            except Exception as exc:
                logging.error(f"Method '{method}' generated an exception: {exc}", exc_info=True)

if __name__ == "__main__":
    cfg = Config()
    model = setup_model_and_device(cfg.MODEL_NAME, cfg.DEVICE)
    chroma_client = chromadb.PersistentClient(path=str(cfg.CHROMA_PATH))
    main_indexing(chroma_client, model, cfg)
    logging.info("\nAll indexing processes finished.")
