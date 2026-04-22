import json
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional
import sys
import re 

def get_llm_response(model_name: str, messages: list, temperature: float):
    """
    This function should contain the code to call your actual LLM service.
    """
    raise NotImplementedError("Please implement your own get_llm_response function in the script.")


PROMPT_TEMPLATE = """
# ROLE: You are an expert software engineer with extensive experience in project development and maintenance. Your core mission is to create a benchmark task for evaluating repository-level documentation by analyzing Pull Request (PR) data.
# CONTEXT: I will provide you with comprehensive information about a single PR, including its metadata, code changes, and rich supplementary context like program dependencies, associated issues, external web pages, and commit history.
# INSTRUCTIONS:
You must follow a three-step Chain-of-Thought (CoT) process. First, analyze the context. Second, generate a description based on your analysis. Third, extract structured details from the description you wrote. Your final output MUST be a single, valid JSON object.
**IMPORTANT: All of your output, including all text within the JSON, must be in English.**

### STEP 1: Analysis (Internal Thought Process)
- Synthesize all provided context (PR info, code diffs, dependencies, issues, etc.) to form a deep, holistic understanding of the PR. Consider the background, motivation, implementation details, and impact scope.
- This is your internal reasoning to gather the necessary facts; do not include it in the final JSON output.

### STEP 2: Generate High-Quality PR Description
- Based on your analysis from Step 1, write a single, technically-rich paragraph that accurately describes the change implemented in the PR.
- When constructing the description, you must consciously weave together the following three dimensions to tell a complete story:
    *   **Start with the WHY:** What was the motivation, purpose, or root problem being addressed? (e.g., "To resolve a race condition...", "In order to improve database performance...").
    *   **Then, describe the WHAT:** What were the core code subjects or entities that were changed? (e.g., "...the `AuthManager` class was refactored...").
    *   **Finally, explain the HOW:** What were the technical means, specific methods, or patterns used to implement the change? (e.g., "...by implementing the Singleton pattern and using the `asyncio` library.").
- **Constraint:** Do NOT mention specific file names, file paths, or repository versions in the description.

### STEP 3: Extract Details and Create Masked Version
- **A. Extract Key Details:** From the description you just wrote in Step 2, identify a list of key, non-trivial technical terms. Each extracted detail must correspond to one of the three dimensions:
    - **WHAT (The Subject of Change):**
        *   **Definition:** The core code **subjects** or **entities** affected.
        *   **Maskable Types:**
            *   **Function/Method Names:** e.g., calculate_metrics
            *   **Class/Module Names:** e.g., AuthManager
            *   **Key Variable/Attribute Names:** e.g., self.retry_count
            *   **API Endpoints:** e.g., /api/v2/users
            *   **Data Types or Structures:** e.g., DataFrame, JSON
    - **WHY (The Motivation for Change):**
        *   **Definition:** The **motivation**, **purpose**, or **root problem** being addressed.
        *   **Maskable Types:**
            *   **Performance Metrics Optimized:** e.g., latency, throughput, memory usage
            *   **Abstract Concepts Introduced:** e.g., idempotency, concurrency, caching
            *   **Root Problems Solved:** e.g., race condition, memory leak, N+1 query problem

    - **HOW (The Method of Change):**
        *   **Definition:** The **technical means**, **specific methods**, or **patterns** used.
        *   **Maskable Types:**
            *   **Libraries/Frameworks Used:** e.g., numpy.vectorize, asyncio, React
            *   **Design Patterns Applied:** e.g., Singleton, Factory, Observer
            *   **Algorithms/Data Structures Used:** e.g., QuickSort, HashSet, Bloom filter
            *   **Specific API Calls or Functions:** e.g., bcrypt.hashpw, requests.post
- **B. Create Masked Description:** Create a "masked_description" by replacing each of the exact phrases you extracted in part A with a `[MASK]` placeholder.
- **C. Format Output:** Assemble your results into the final JSON object as specified below.
# OUTPUT FORMAT: You MUST provide your response as a single, valid JSON object. Do not add any text before or after the JSON object.
{
  "detailed_description": "The high-quality PR description generated in Step 2.",
  "masked_description": "The masked version of the description from Step 3-B.",
  "masked_answers": [
    {
      "answer": "The exact string for the first extracted detail from Step 3-A.",
      "type": "The dimension of the answer ('WHAT', 'WHY', or 'HOW')."
    },
    {
      "answer": "The exact string for the second extracted detail.",
      "type": "The dimension of the second answer."
    }
  ]
}
# EXAMPLE OF EXPECTED OUTPUT:
{
  "detailed_description": "To resolve a database performance bottleneck caused by not using bulk operations, the process_user_updates function was refactored. It now performs a single, batched database write by calling the User.batch_update method.",
  "masked_description": "To resolve a [MASK] caused by not using bulk operations, the [MASK] function was refactored. It now performs a single, batched database write by calling the [MASK] method.",
  "masked_answers": [
    {
      "answer": "database performance bottleneck",
      "type": "WHY"
    },
    {
      "answer": "process_user_updates",
      "type": "WHAT"
    },
    {
      "answer": "User.batch_update",
      "type": "HOW"
    }
  ]
}
# START OF CONTEXT
---
{{CONTEXT_STRING}}
---
# END OF CONTEXT
# YOUR JSON RESPONSE:
"""

def build_llm_context(pr_data: Dict[str, Any]) -> str:
    repo_id = pr_data.get("id", "N/A")
    repo_name = "/".join(repo_id.split('/')[:2]) if repo_id != "N/A" else "Unknown Repository"
    context = f"### Project Repository\n"
    context += f"The following Pull Request belongs to the {repo_name} repository.\n\n"
    context += f"### Pull Request Information\n"
    context += f"**Title:** {pr_data.get('title', 'N/A')}\n"
    context += f"**Body:**\n{pr_data.get('body', 'N/A')}\n\n"
    context += "### Changed Core Files and Code Diff (Patch)\n"
    if 'core_files_details' in pr_data and pr_data['core_files_details']:
        for file_info in pr_data['core_files_details']:
            context += f"**File:** {file_info['filename']}\n"
            patch = file_info.get('patch', '')
            if patch:
                patch_summary = (patch[:1500] + '\n...') if len(patch) > 1500 else patch
                context += f"**Patch:**\ndiff\n{patch_summary}\n\n"
    else:
        context += "No core file details provided.\n\n"
    context += "### Supplementary Context\n"
    if pr_data.get('dependency_analysis'):
        context += "#### Program Dependency Analysis\n"
        context += "Callers and callees of the modified code snippets:\n"
        context += f"{json.dumps(pr_data['dependency_analysis'], indent=2)}\n\n"
    if pr_data.get('associated_issues'):
        context += "#### Associated Issue Content\n"
        for issue_info in pr_data['associated_issues']:
            if issue_info.get('content'):
                context += f"--- Issue URL: {issue_info['url']} ---\n"
                context += f"{issue_info['content']}\n\n"
    if pr_data.get('external_pages'):
        context += "#### External Web Page Content\n"
        for page_info in pr_data['external_pages']:
            if page_info.get('content'):
                context += f"--- External URL: {page_info['url']} ---\n"
                context += f"{page_info['content']}\n\n"
    if pr_data.get('commit_history'):
        context += "#### Commit History Tracking\n"
        context += "The PR consists of the following commits:\n"
        for commit in pr_data['commit_history']:
             context += f"- Commit SHA: {commit.get('sha', 'N/A')}\n"
             context += f"  Message: {commit.get('message', 'N/A')}\n"
        context += "\n"
    return context

def generate_benchmark_task(pr_data: Dict[str, Any], max_retries: int = 3) -> Optional[Dict[str, Any]]:
    context_string = build_llm_context(pr_data)
    final_prompt = PROMPT_TEMPLATE.replace("{{CONTEXT_STRING}}", context_string)
    messages = [{"role": "user", "content": final_prompt}]
    repo_id = pr_data.get('id', 'Unknown')
    for attempt in range(max_retries):
        try:
            model_name = ""
            response_text, _ = get_llm_response(model_name, messages, 0.2)
            time.sleep(1)
            json_start = response_text[0].find('{')
            json_end = response_text[0].rfind('}') + 1
            if json_start == -1 or json_end == 0:
                print(f"  [Attempt {attempt+1}/{max_retries}] ID: {repo_id} - No valid JSON object found in LLM response.")
                continue
            clean_json_str = response_text[0][json_start:json_end]
            llm_output = json.loads(clean_json_str)
            detailed_description = llm_output.get("detailed_description", "")
            masked_description = llm_output.get("masked_description", "")
            masked_answers_list = llm_output.get("masked_answers", [])
            if not all([detailed_description, masked_description, masked_answers_list]):
                 print(f"  [Attempt {attempt+1}/{max_retries}] ID: {repo_id} - Validation failed: Missing required fields in JSON. Retrying...")
                 continue
            mask_count = masked_description.count("[MASK]")
            answer_count = len(masked_answers_list)
            if mask_count != answer_count:
                print(f"  [Attempt {attempt+1}/{max_retries}] ID: {repo_id} - Validation failed: MASK count ({mask_count}) does not match answer count ({answer_count}). Retrying...")
                continue
            if mask_count == 0:
                print(f"  [Attempt {attempt+1}/{max_retries}] ID: {repo_id} - Validation failed: No [MASK] placeholders found. Retrying...")
                continue
            
            try:
                all_answers_found = True

                for item in masked_answers_list:
                    if item['answer'] not in detailed_description:
                        print(f"  [Attempt {attempt+1}/{max_retries}] ID: {repo_id} - Validation failed: Answer '{item['answer']}' not found in detailed_description. Retrying...")
                        all_answers_found = False
                        break
                if not all_answers_found:
                    continue

                reconstructed_task_desc = detailed_description
                for item in masked_answers_list:
                    reconstructed_task_desc = reconstructed_task_desc.replace(item['answer'], '[MASK]', 1)

                if reconstructed_task_desc != masked_description:
                    print(f"  [Attempt {attempt+1}/{max_retries}] ID: {repo_id} - Validation failed: Reconstructed masked_description does not match the provided one. Retrying...")
                    continue

            except (KeyError, IndexError, TypeError, re.error) as e:
                print(f"  [Attempt {attempt+1}/{max_retries}] ID: {repo_id} - Validation failed: Error while trying to reconstruct description: {e}. Retrying...")
                continue

            repo_owner, repo_name_part = pr_data['id'].split('/')[:2]
            new_pr_data = {
                "id": pr_data["id"],
                "repo": f"{repo_owner}/{repo_name_part}",
                "number": pr_data["number"],
                "version": pr_data.get("milestone"),
                "PR_binary": pr_data.get("history"),
                "PR_files": pr_data.get("core_files"),
                "detailed_description": detailed_description,
                "masked_description": masked_description,
                "masked_answers": masked_answers_list
            }
            print(f"  [Success] ID: {repo_id} - Task generated and validated successfully.")
            return new_pr_data
        except json.JSONDecodeError as e:
            print(f"  [Attempt {attempt+1}/{max_retries}] ID: {repo_id} - JSON parsing failed: {e}. Retrying...")
        except NotImplementedError as e:
            print(f"[CRITICAL] {e}")
            sys.exit(1)
        except Exception as e:
            print(f"  [Attempt {attempt+1}/{max_retries}] ID: {repo_id} - An error occurred during LLM call or processing: {e}. Retrying...")
        time.sleep(1)
    print(f"  [Failure] ID: {repo_id} - Reached max retries, abandoning this item.")
    return None

def main():
    input_file = "your_input_file.jsonl"
    output_file = "your_output_file.jsonl"
    
    max_workers = 8
    max_tasks_to_run = -1
    if not os.path.exists(input_file):
        print(f"[ERROR] Input file '{input_file}' not found. Please create it and populate with valid data.")
        return
    completed_repo_ids = set()
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f_out_check:
            for line in f_out_check:
                try:
                    completed_repo_ids.add(json.loads(line)['id'])
                except (json.JSONDecodeError, KeyError):
                    continue
        print(f"Output file detected, loaded {len(completed_repo_ids)} completed IDs.")
    tasks_to_process = []
    with open(input_file, 'r', encoding='utf-8') as infile:
        for line in infile:
            try:
                pr_data = json.loads(line)
                if pr_data.get('id') not in completed_repo_ids:
                    tasks_to_process.append(pr_data)
            except (json.JSONDecodeError, KeyError):
                continue
    print(f"File loading complete, found {len(tasks_to_process)} new tasks to process.")
    if max_tasks_to_run > 0:
        tasks_to_process = tasks_to_process[:max_tasks_to_run]
        print(f"Based on settings, this run will process a maximum of {len(tasks_to_process)} tasks.")
    if not tasks_to_process:
        print("No new tasks to process.")
        return
    processed_count = 0
    failed_count = 0
    output_lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=max_workers) as executor, \
         open(output_file, 'a', encoding='utf-8') as outfile:
        future_to_pr = {executor.submit(generate_benchmark_task, pr_data): pr_data for pr_data in tasks_to_process}
        print(f"\n--- Starting to process tasks with {max_workers} threads ---")
        for future in as_completed(future_to_pr):
            pr_data = future_to_pr[future]
            try:
                result = future.result()
                if result:
                    with output_lock:
                        outfile.write(json.dumps(result) + '\n')
                        outfile.flush()
                    processed_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"  [Critical] ID: {pr_data.get('id')} - An uncaught exception occurred during task execution: {e}")
                failed_count += 1
    print("\n--- Processing Complete ---")
    print(f"Successfully generated {processed_count} benchmark tasks in this run.")
    print(f"Failed or abandoned {failed_count} tasks.")

if __name__ == "__main__":
    main()
