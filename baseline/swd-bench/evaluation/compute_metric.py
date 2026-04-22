import json
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, matthews_corrcoef
from sklearn.metrics import balanced_accuracy_score
from typing import List, Dict, Any, Tuple, Set
import os
import numpy as np
import csv

def read_jsonl(file_path: str) -> List[Dict[str, Any]]:
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.strip()))
    return data

def compute_task1(data: List[Dict[str, Any]]) -> Dict[str, float]:

    y_true = []
    y_pred = []

    for item in data:

        true_label_raw = item['task1_answer']
        if true_label_raw:
            y_true.append(True)
        else:
            y_true.append(False)

        y_pred.append(item['PR_binary_pred'])
    
    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0.0)
    recall = recall_score(y_true, y_pred, zero_division=0.0)
    f1 = f1_score(y_true, y_pred, zero_division=0.0)
    mcc = matthews_corrcoef(y_true, y_pred)
    balanced_acc = balanced_accuracy_score(y_true, y_pred)

    metrics = {
        'balanced_accuracy': balanced_acc * 100,
        'mcc': mcc * 100,
        'accuracy': accuracy * 100,
        'precision': precision * 100,
        'recall': recall * 100,
        'f1_score': f1 * 100,
    }
    return metrics

def compute_task2(data: List[Dict[str, Any]]) -> Dict[str, float]:

    all_f1s = []
    all_ious = []
    valid_records = 0
    for item in data:
        true_files: List[str] = item.get('task2_answer', [])
        pred_files: List[str] = item.get('PR_files_pred', [])

        valid_records += 1
        true_set: Set[str] = set(true_files)
        pred_set: Set[str] = set(pred_files)
        intersection_size = len(true_set.intersection(pred_set))
        true_size = len(true_set)
        pred_size = len(pred_set)
        union_size = len(true_set.union(pred_set))
        f1 = (2 * intersection_size) / (true_size + pred_size)
        all_f1s.append(f1)
        iou = intersection_size / union_size
        all_ious.append(iou)

    macro_f1 = np.mean(all_f1s) if all_f1s else 0.0
    mean_iou = np.mean(all_ious) if all_ious else 0.0
    metrics = {
        'Macro-F1': macro_f1 * 100,
        'mIoU': mean_iou * 100
    }
    return metrics

def _levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def compute_task3(data: List[Dict[str, Any]], em_thresholds: List[float] = [1.0, 0.8]) -> Dict[str, float]:
    
    def _levenshtein_distance(s1, s2):
        if len(s1) < len(s2):
            return _levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
    def _edit_similarity(s1, s2):
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        return 1.0 - (_levenshtein_distance(s1, s2) / max_len)

    all_em_case_thresholded = {f"EM_case_avg_at_{th}": [] for th in em_thresholds}
    global_em_correct_thresholded = {f"EM_global_at_{th}": 0 for th in em_thresholds}
    all_edit_sim_case = []
    all_edit_sim_token_case = []
    global_true_answers = []
    global_edit_sim_tokens = []
    valid_records = 0
    for item in data:
        true_answers = item.get('task3_answer', [])
        pred_answers_raw = item.get('masked_answers_pred', [])
        pred_answers = [str(ans) for ans in pred_answers_raw]
        if not true_answers:
            continue
        valid_records += 1
        min_len = min(len(true_answers), len(pred_answers))
        correct_in_order_thresholded = {th: 0 for th in em_thresholds}
        for i in range(min_len):
            similarity = _edit_similarity(true_answers[i], pred_answers[i])
            for th in em_thresholds:
                if similarity >= th:
                    correct_in_order_thresholded[th] += 1
        for th in em_thresholds:
            em_case = correct_in_order_thresholded[th] / len(true_answers)
            all_em_case_thresholded[f"EM_case_avg_at_{th}"].append(em_case)
        separator = " "
        seq_true = separator.join(true_answers)
        seq_pred = separator.join(pred_answers)
        all_edit_sim_case.append(_edit_similarity(seq_true, seq_pred))
        edit_sim_tokens = []
        for i in range(min_len):
            edit_sim_token = _edit_similarity(true_answers[i], pred_answers[i])
            edit_sim_tokens.append(edit_sim_token)
            global_edit_sim_tokens.append(edit_sim_token)
        if edit_sim_tokens:
            all_edit_sim_token_case.append(np.mean(edit_sim_tokens))
        
    metrics = {}
    for th in em_thresholds:
        key_case = f"EM_case_avg_at_{th}"
        metrics[key_case] = np.mean(all_em_case_thresholded[key_case]) * 100 if all_em_case_thresholded[key_case] else 0.0
        key_global = f"EM_global_at_{th}"
        num_correct = global_em_correct_thresholded[key_global]
        total_answers = len(global_true_answers)
        metrics[key_global] = (num_correct / total_answers) * 100 if total_answers else 0.0

    return metrics

