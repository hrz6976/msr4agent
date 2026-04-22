import sys
import os
from tree_sitter import Language, Parser
from utils import EXTENSION_MAPPING, CALLEE_NODES, CALLER_NODES, DEFINITION_CONTAINER_NODES

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def get_language_for_extension(extension):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for lang, exts in EXTENSION_MAPPING.items():
        if f".{extension}" in exts:
            so_path = os.path.join(current_dir, 'build/languages.so')
            if not os.path.exists(so_path):
                raise FileNotFoundError(f"Language library not found at: {so_path}")
            return Language(so_path, lang), lang
    return None, None

def parse_code_snippet(language, code_snippet):
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(bytes(code_snippet, "utf8"))
    return tree

def expand_lines_to_full_definitions(root_node, line_numbers, lang_name):
    expanded_nodes = set()
    nodes_to_visit = [root_node]
    
    while nodes_to_visit:
        node = nodes_to_visit.pop(0)
        node_start_line, _ = node.start_point
        node_end_line, _ = node.end_point
        
        is_relevant = False
        for start, end in line_numbers:
            if max(node_start_line + 1, start) <= min(node_end_line + 1, end):
                is_relevant = True
                break
        
        if not is_relevant:
            continue

        if node.type in DEFINITION_CONTAINER_NODES.get(lang_name, []):
            expanded_nodes.add(node)
        else:
            nodes_to_visit.extend(node.children)
            
    return list(expanded_nodes)

def extract_definitions_and_calls(node, definitions_and_calls, language):
    if node.type in CALLEE_NODES.get(language, []):
        definitions_and_calls.append(('callee', node))
    elif node.type in CALLER_NODES.get(language, []):
        definitions_and_calls.append(('caller', node))
    
    for child in node.children:
        extract_definitions_and_calls(child, definitions_and_calls, language)

def extract_names(definitions_and_calls):
    definitions = set()
    calls = set()
    for kind, node in definitions_and_calls:
        if kind == 'callee':
            name_node = node.child_by_field_name('name')
            if name_node:
                definitions.add(name_node.text.decode('utf-8'))
        elif kind == 'caller':
            name_node = node.child_by_field_name('function') or \
                        node.child_by_field_name('constructor') or \
                        node.child_by_field_name('name') or \
                        node.child_by_field_name('property')
            if name_node:
                calls.add(name_node.text.decode('utf-8'))
    return definitions, calls

def analyze_file(file_path, language, lang_name, line_numbers):
    with open(file_path, 'r', encoding='utf-8') as file:
        code = file.read()
    
    file_tree = parse_code_snippet(language, code)
    
    if not line_numbers:
        definitions_and_calls = []
        extract_definitions_and_calls(file_tree.root_node, definitions_and_calls, lang_name)
        return definitions_and_calls

    full_definition_nodes = expand_lines_to_full_definitions(file_tree.root_node, line_numbers, lang_name)
    
    relevant_definitions_and_calls = []
    for node in full_definition_nodes:
        extract_definitions_and_calls(node, relevant_definitions_and_calls, lang_name)
        
    return relevant_definitions_and_calls

def analyze_directory(directory, language, lang_name, relevant_definitions, relevant_calls):
    definitions_and_calls = []
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in EXTENSION_MAPPING.get(lang_name, [])):
                file_path = os.path.join(root, file)
                file_definitions_and_calls = analyze_file(file_path, language, lang_name, [])
                for kind, node in file_definitions_and_calls:
                    if kind == 'callee':
                        name_node = node.child_by_field_name('name')
                        if name_node and name_node.text.decode('utf-8') in relevant_calls:
                            description = (f"This code snippet defines the function or class '{name_node.text.decode('utf-8')}' which is called by the provided code change.")
                            definitions_and_calls.append((kind, node, file_path, description))
                    elif kind == 'caller':
                        name_node = node.child_by_field_name('function') or node.child_by_field_name('constructor') or node.child_by_field_name('property')
                        if name_node and name_node.text.decode('utf-8') in relevant_definitions:
                            description = f"This code snippet calls the function or class '{name_node.text.decode('utf-8')}' defined in the provided code change."
                            definitions_and_calls.append((kind, node, file_path, description))
    return definitions_and_calls

def format_definitions_and_calls(definitions_and_calls):
    result = []
    for kind, node, file_path, description in definitions_and_calls:
        start_line, _ = node.start_point
        code_fragment = node.text.decode('utf-8')
        lines = code_fragment.split('\n')
        numbered_lines = [f'[{start_line + 1 + i}] {line}' for i, line in enumerate(lines)]
        numbered_code_fragment = '\n'.join(numbered_lines)
        result.append(f'File Path: {file_path}\nDescription: {description}\nCode Snippet:\n{numbered_code_fragment}')

    return '\n\n'.join(result)

def generate_call(repo_path, line_numbers, file_path):
    try:
        extension = file_path.split('.')[-1]
    except IndexError:
        return f"Could not determine file extension for: {file_path}"

    language, lang_name = get_language_for_extension(extension)

    if language:
        relevant_definitions_and_calls = analyze_file(file_path, language, lang_name, line_numbers)
        relevant_definitions, relevant_calls = extract_names(relevant_definitions_and_calls)
        
        directory_definitions_and_calls = analyze_directory(repo_path, language, lang_name, relevant_definitions, relevant_calls)
        
        result = format_definitions_and_calls(directory_definitions_and_calls)
    else:
        print(f'Unsupported file extension: {extension}')
        result = ''
    return result

def generate_code_change(code_change):
    lines = code_change.split('\n')
    code_change_before = []
    code_change_before_with_line_numbers = []
    code_change_after = []
    code_change_after_with_line_numbers = []
    code_change_with_line_numbers = []
    line_numbers_before = []
    line_numbers_after = []

    current_chunk_before = []
    current_chunk_before_with_line_numbers = []
    current_chunk_after = []
    current_chunk_after_with_line_numbers = []
    current_line_number_before = None
    current_line_number_after = None

    for line in lines:
        if line.startswith('@@'):
            if current_chunk_before:
                code_change_before.append('\n'.join(current_chunk_before))
                code_change_before_with_line_numbers.append('\n'.join(current_chunk_before_with_line_numbers))
                line_numbers_before.append((start_line_number_before, current_line_number_before - 1))
                current_chunk_before = []
                current_chunk_before_with_line_numbers = []
            if current_chunk_after:
                code_change_after.append('\n'.join(current_chunk_after))
                code_change_after_with_line_numbers.append('\n'.join(current_chunk_after_with_line_numbers))
                line_numbers_after.append((start_line_number_after, current_line_number_after - 1))
                current_chunk_after = []
                current_chunk_after_with_line_numbers = []
            
            parts = line.split(' ')
            start_line_number_before = int(parts[1].split(',')[0][1:])
            current_line_number_before = start_line_number_before
            start_line_number_after = int(parts[2].split(',')[0][1:])
            current_line_number_after = start_line_number_after
        elif line.startswith(('diff --git', '+++', '---', 'index', 'new file mode', 'deleted file mode')):
            continue
        elif line.startswith('+'):
            current_chunk_after.append(' ' + line[1:])
            current_chunk_after_with_line_numbers.append(f"[{current_line_number_after}] {' ' + line[1:]}")
            code_change_with_line_numbers.append(f"[], [{current_line_number_after}], {'[+]' + line[1:]}")
            current_line_number_after += 1
        elif line.startswith('-'):
            current_chunk_before.append(' ' + line[1:])
            current_chunk_before_with_line_numbers.append(f"[{current_line_number_before}] {' ' + line[1:]}")
            code_change_with_line_numbers.append(f"[{current_line_number_before}], [], {'[-]' + line[1:]}")
            current_line_number_before += 1
        else:
            current_chunk_before.append(line)
            current_chunk_before_with_line_numbers.append(f"[{current_line_number_before}] {line}")
            current_chunk_after.append(line)
            current_chunk_after_with_line_numbers.append(f"[{current_line_number_after}] {line}")
            code_change_with_line_numbers.append(f"[{current_line_number_before}], [{current_line_number_after}], [~] {line}")
            current_line_number_before += 1
            current_line_number_after += 1

    if current_chunk_before:
        code_change_before.append('\n'.join(current_chunk_before))
        code_change_before_with_line_numbers.append('\n'.join(current_chunk_before_with_line_numbers))
        line_numbers_before.append((start_line_number_before, current_line_number_before - 1))
    if current_chunk_after:
        code_change_after.append('\n'.join(current_chunk_after))
        code_change_after_with_line_numbers.append('\n'.join(current_chunk_after_with_line_numbers))
        line_numbers_after.append((start_line_number_after, current_line_number_after - 1))

    return code_change_before, code_change_before_with_line_numbers, code_change_after, code_change_after_with_line_numbers, line_numbers_before, line_numbers_after, code_change_with_line_numbers

def generate_file(file_content):
    lines = file_content.split('\n')
    numbered_lines = []
    for line_number, line in enumerate(lines, start=1):
        numbered_lines.append(f"[{line_number}] {line}")
    return '\n'.join(numbered_lines)

def generate_context(repo_path, changes):
    context = ''
    file_paths = []
    for change in changes:
        if change['file_path'] not in file_paths:
            file_paths.append(change['file_path'])
        
        _, _, _, _, _, line_numbers_after, _ = generate_code_change(change['diff'])

        call_context = generate_call(repo_path, line_numbers_after, change['file_path'])
        
