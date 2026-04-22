import json
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import logging
import torch
from sentence_transformers import SentenceTransformer
import chromadb
from pathlib import Path
import tiktoken
from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.preprocessing import normalize
from vertexai.preview import tokenization

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)
from benchmark.utils.llm import get_llm_response

RQ1 = "RQ1"
RQ2 = "RQ2"
RQ3 = "RQ3"
SYSTEM_PROMPT = "SYSTEM_PROMPT"
USER_PROMPT = "USER_PROMPT"
source_dir = ""
input_file = f""

model_name = ""
max_workers = 4
max_tasks_to_run = -1

class SearchConfig:
    MODEL_NAME = 'Salesforce/SFR-Embedding-Code-400M_R'
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    TOKENIZER_NAME = "cl100k_base"
    MERGED_DB_PATH = Path("../embedding/chroma_dbs")
    ALL_METHODS = []

class SearchContext:
    def __init__(self, config: SearchConfig):
        self.config = config
        self.model: Optional[SentenceTransformer] = None
        self.tokenizer: Optional["tokenization.Tokenizer"] = None
        self.client: Optional[chromadb.PersistentClient] = None
        self.collections: Dict[str, chromadb.Collection] = {}
    def initialize(self):

        try:
            self.model = SentenceTransformer(self.config.MODEL_NAME, trust_remote_code=True, device=self.config.DEVICE)
            self.tokenizer = tokenization.get_tokenizer_for_model("gemini-1.5-pro-001")
            print("Model and tokenizer loaded successfully.")
        except Exception as e:
            print(f"Fatal: Failed to load model or tokenizer. Error: {e}")
            raise

        try:
            self.client = chromadb.PersistentClient(path=str(self.config.MERGED_DB_PATH))
            print(f"Connected to merged DB at {self.config.MERGED_DB_PATH}")
            all_db_collections = self.client.list_collections()
            collection_names_in_db = {c.name for c in all_db_collections}
            for method in self.config.ALL_METHODS:
                collection_name = f"collection_{method.lower()}"
                if collection_name in collection_names_in_db:
                    self.collections[method] = self.client.get_collection(name=collection_name)
                    print(f"  - Loaded collection: '{collection_name}'")
                else:
                    print(f"  - Collection '{collection_name}' for method '{method}' not found in the database.")
        except Exception as e:
            print(f"Fatal: Failed to connect or load collections from merged DB. Error: {e}")
            raise
        print("--- Global Search Context Initialized ---")


SEARCH_CONTEXT = SearchContext(SearchConfig())
SEARCH_CONTEXT.initialize()

def normalize_embedding(embedding: List[float]) -> List[float]:
    embedding_np = np.array(embedding).reshape(1, -1)
    normalized_embedding = normalize(embedding_np, norm='l2', axis=1)
    return normalized_embedding[0].tolist()

def search_top_n(
    collections: List[chromadb.Collection],
    query_embedding: List[float],
    repo_name: str,
    n: int = 100,
) -> List[Dict[str, Any]]:
 
    all_results = []
    normalized_query_embedding = normalize_embedding(query_embedding)

    n_to_fetch = n * 5
    for collection in collections:
        try:
            results = collection.query(
                query_embeddings=[normalized_query_embedding],
                n_results=n_to_fetch,
                include=["metadatas", "documents", "distances"]
            )
            if not results or not results['ids'] or not results['ids'][0]:
                continue
            ids, distances, metadatas, documents = results['ids'][0], results['distances'][0], results['metadatas'][0], results['documents'][0]
            for i in range(len(ids)):
                metadata = metadatas[i]
                if repo_name:
                    repo_field = metadata.get("repo")
                    if not repo_field or repo_field not in repo_name:
                        continue

                l2_distance_squared = distances[i]
                cosine_similarity_score = 1 - (l2_distance_squared / 2.0)
                all_results.append({
                    'id': ids[i],
                    'score': cosine_similarity_score,
                    'metadata': metadata,
                    'document': documents[i],
                    'method': collection.metadata.get("source_method", "unknown")
                })
        except Exception as e:
            print(f"Error querying collection {collection.name}: {e}")

    all_results.sort(key=lambda x: x['score'], reverse=True)
    return all_results[:n]

def search_by_token_limit(
    collections: List[chromadb.Collection],
    query_embedding: List[float],
    tokenizer: "Tokenizer",
    token_limit: int,
    repo_name: str,
) -> List[Dict[str, Any]]:
    min_truncate_tokens = 50
    candidate_results = search_top_n(
        collections, 
        query_embedding, 
        repo_name=repo_name, 
    )
    final_results = []
    total_tokens = 0
    for res in candidate_results:
        document_text = res.get('document', '')
        if not document_text:
            continue
        num_tokens = tokenizer.count_tokens(document_text).total_tokens
        remaining_space = token_limit - total_tokens
        if num_tokens <= remaining_space:
            final_results.append(res)
            total_tokens += num_tokens
        elif remaining_space >= min_truncate_tokens:
            estimated_char_len = int(len(document_text) * (remaining_space / num_tokens) * 0.95)
            truncated_text = document_text[:estimated_char_len]
            if not truncated_text:
                break
            truncated_num_tokens = tokenizer.count_tokens(truncated_text).total_tokens
            if min_truncate_tokens <= truncated_num_tokens <= remaining_space:
                truncated_res = res.copy()
                truncated_res['document'] = truncated_text
                final_results.append(truncated_res)
                total_tokens += truncated_num_tokens
            break 
        else:
            break 
    return final_results

PROMPT_TEMPLATES ={
RQ1:{
SYSTEM_PROMPT:"""
# ROLE
You are an expert software engineer with extensive experience in project development and maintenance. 
Your task is to perform ``Functionality Existence Discrimination`` by determining if a specific functionality, as described in a Pull Request (PR), is currently implemented within the code repository.

# CONTEXT
You will be provided with two kinds of information:
1.  **PR Information:** The detailed description of the pull request.
2.  **Repository-level Code Documentation:** Relevant code documentation snippets from the code repository.

# INSTRUCTIONS
1.  Analyze the PR description to understand the functionality.
2.  Based on this analysis, determine if the functionality described in the PR is currently implemented according to the given context.

Your response MUST be a single, valid JSON object containing two keys:
1.  `"function_exists"`: Provide a boolean value (`true` if the functionality exists, `false` otherwise).
2.  `"reasoning"`: Provide a very concise reason (in 30 words) in English, explaining how you reached your conclusion according to the given context.

Do not add any text before or after the JSON object. For example:
{"function_exists": true, "reasoning": "...(in 30 words)"}
""",
USER_PROMPT:"""
# START OF CONTEXT
---
## 1. PR Information
{PR_DESCRIPTION}

## 2. Repository-level Code Documentation
{DOCUMENTATION_CONTEXT}
---
# END OF CONTEXT

# YOUR JSON RESPONSE:
"""
},

RQ2: {
SYSTEM_PROMPT:"""
# ROLE
You are an expert software engineer with extensive experience in project development and maintenance. 
Your task is to perform ``Functionality Module Localization`` by identifying the primary code file(s) responsible for implementing a specific functionality described in a Pull Request (PR).

# CONTEXT
You will be provided with three kinds of information:
1.  **PR Information:** The detailed description of the pull request.
2.  **Repository-level Code Documentation:** Relevant code documentation snippets from the repository.

# INSTRUCTIONS
1.  Analyze the PR description to understand the functionality.
2.  Focus on identifying the main implementation files. Test files or general documentation files should be excluded, but `__init__.py` files are permissible if they contain relevant logic.
3.  The `"implementation_files"` list in your response must not be empty. You must identify at least one most relevant file according to the given context.

Your response MUST be a single, valid JSON object containing two keys:
1.  `"implementation_files"`: Provide a list of strings, where each string is the full path to a source code file primarily responsible for the described functionality. The list should be ordered by relevance.
2.  `"reasoning"`: Provide a very concise reason (in 30 words) in English, explaining how you reached your conclusion according to the given context.

Do not add any text before or after the JSON object. For example:
{"implementation_files": ["src/api/auth/services.py", "src/api/auth/routes.py"], "reasoning": "...(in 30 words)"}
""", 
USER_PROMPT:"""
# START OF CONTEXT
---
## 1. PR Information
{PR_DESCRIPTION}

## 2. Repository-level Code Documentation
{DOCUMENTATION_CONTEXT}
---
# END OF CONTEXT

# YOUR JSON RESPONSE:
"""
},

RQ3: {
SYSTEM_PROMPT:"""
# ROLE
You are an expert software engineer with extensive experience in project development and maintenance. 
Your task is to perform `Functionality Detail Completion` by filling in the `[MASK]` placeholders in a "fill-in-the-blank" Pull Request (PR) description with the correct terms.

# CONTEXT
You will be provided with two kinds of information:
1.  **Incomplete PR Information:** The detailed description of the pull request, containing one or more `[MASK]` placeholders.
2.  **Repository-level Code Documentation:** Relevant code documentation snippets from the repository.

# INSTRUCTIONS
1.  Analyze the incomplete PR description to understand the functionality.
2.  You must find a value for **every** `[MASK]` placeholder according to the given context, which can range from code entities like function or class names to abstract concepts like design patterns or performance metrics, and so on.
3.  The order of the details in your response list MUST match the order of appearance of the `[MASK]` placeholders.

Your response MUST be a single, valid JSON object containing two keys:
1.  `"missing_details"`: Provide a list of strings, where each string correctly fills a `[MASK]` placeholder. The length of this list must equal the number of `[MASK]` placeholders.
2.  `"reasoning"`: Provide a very concise reason (in 30 words) in English, explaining how you reached your conclusion according to the given context.

Do not add any text before or after the JSON object. For example:
If the PR description is "This PR updates the `[MASK]` function to use the new `[MASK]` constant for retries.", your response should look like this:
{"missing_details": ["fetch_remote_data", "MAX_API_RETRIES"], "reasoning": "...(in 30 words)"}
""",

USER_PROMPT:"""
# START OF CONTEXT
---
## 1. Incomplete PR Information
{PR_DESCRIPTION}

## 2. Repository-level Code Documentation
{DOCUMENTATION_CONTEXT}
---
# END OF CONTEXT

# NOTICE
{TIPS}

# YOUR JSON RESPONSE:
"""
}
}

def build_prompt(pr_data, choose_BASE, choose_ID, choose_OD, experiment_mode, top):
    repo_name = pr_data.get('repo')
    
    system_prompt = PROMPT_TEMPLATES[experiment_mode][SYSTEM_PROMPT]
    user_prompt = PROMPT_TEMPLATES[experiment_mode][USER_PROMPT]

    if experiment_mode == RQ3:
        user_prompt = user_prompt.replace("{PR_DESCRIPTION}", pr_data.get("masked_description"))
        tip = f"Notice that you have {len(pr_data["masked_answers"])} `[MASK]` placeholders to fill."
        user_prompt = user_prompt.replace("{TIPS}", tip)
    else:
        user_prompt = user_prompt.replace("{PR_DESCRIPTION}", pr_data.get("detailed_description"))

    documentation_context = ""
    methods_to_search = [choose_BASE, choose_ID, choose_OD]
    methods_to_search = [item for item in methods_to_search if item != 'None']
    if methods_to_search:
        if experiment_mode == RQ3:
            query_text = pr_data.get("masked_description")
        else:
            query_text = pr_data.get("detailed_description")
        query_emb_raw = SEARCH_CONTEXT.model.encode(query_text)
        query_emb = normalize(query_emb_raw.reshape(1, -1), norm='l2', axis=1)[0].tolist()
        top_n_results = []
        for method in methods_to_search: 
            top_n_results.extend(search_by_token_limit(collections=[SEARCH_CONTEXT.collections[method]], query_embedding=query_emb, tokenizer=SEARCH_CONTEXT.tokenizer, token_limit=top, repo_name=repo_name))

        snippets = []
        for r in top_n_results:
            metadata = r.get('metadata', {})
            file_path = metadata.get('file_path', 'Unknown File')
            document_content = r.get('document', '')
            header = f"--------------- Start of Snippet from: {file_path} ---------------"
            footer = f"--------------- End of Snippet from: {file_path} ---------------\n"
            formatted_snippet = f"{header}\n{document_content}\n{footer}"
            snippets.append(formatted_snippet)
        documentation_context = "\n".join(snippets)
    else:
        documentation_context = "No valid code documentation. Finish your task by using your general knowledge of the project."

    user_prompt = user_prompt.replace("{DOCUMENTATION_CONTEXT}", documentation_context)
    return system_prompt, user_prompt

def process_pr_for_existence(pr_data, choose_BASE, choose_ID, choose_OD, experiment_mode, top, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    repo_id = pr_data.get('id', 'Unknown')
    
    system_prompt, user_prompt = build_prompt(pr_data, choose_BASE, choose_ID, choose_OD, experiment_mode, top)
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    for attempt in range(max_retries):
        try:
            response_text, _ = get_llm_response(model_name, messages, 0.2)
            time.sleep(1)

            json_start = response_text[0].find('{')
            json_end = response_text[0].rfind('}') + 1
            if json_start == -1 or json_end == 0:
                continue
            
            clean_json_str = response_text[0][json_start:json_end]
            llm_output = json.loads(clean_json_str)

            if "reasoning" not in llm_output:
                continue

            if experiment_mode == RQ1: 
                if "function_exists" not in llm_output:
                    continue
            
                if llm_output["function_exists"] != True and llm_output["function_exists"] != False:
                    continue
                
                result_data = {
                    "id": pr_data["id"],
                    "PR_binary": pr_data["PR_binary"],
                    "PR_binary_pred": llm_output["function_exists"],
                    "reasoning": llm_output["reasoning"]
                }
                
            if experiment_mode == RQ2:
                if "implementation_files" not in llm_output:
                    continue
                
                if not isinstance(llm_output["implementation_files"], list):
                    continue

                result_data = {
                    "id": pr_data["id"],
                    "PR_files": pr_data["PR_files"],
                    "PR_files_pred": llm_output["implementation_files"],
                    "reasoning": llm_output["reasoning"]
                }

            if experiment_mode == RQ3:
  
                if "missing_details" not in llm_output:
                    continue
                
                if not isinstance(llm_output["missing_details"], list):
                    continue

                if len(llm_output["missing_details"]) != len(pr_data["masked_answers"]):
                    continue
                
                result_data = {
                    "id": pr_data["id"],
                    "masked_answers": pr_data["masked_answers"],
                    "masked_answers_pred": llm_output["missing_details"],
                    "reasoning": llm_output["reasoning"]
                }

            return result_data

        except Exception as e:
            print(f"  [Attempt {attempt+1}/{max_retries}] ID: {repo_id} - An error occurred: {e}. Retrying...")
            print(f'-------------- {attempt} ---------------')
            print(response_text)
            time.sleep(1)

    print(f"  [Failure] ID: {repo_id} - Max retries reached. Giving up.")
    return None
