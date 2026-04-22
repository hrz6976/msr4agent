

import os
from tree_sitter import Language, Parser

EXTENSION_MAPPING = {
    'java': ['java'],
    'python': ['py'],
    'cpp': ['cpp', 'cc', 'cxx', 'h', 'hpp'],
    'c_sharp': ['cs'],
    'javascript': ['js'],
    'c': ['c', 'h'],
    'typescript': ['ts', 'tsx'],
    'go': ['go'],
    'ruby': ['rb'],
    'rust': ['rs'],
    'r': ['r'],
    'css': ['css'],
    'html': ['html'],
    'php': ['php']
}

binary_extensions = [
    '.exe', '.dll', '.so', '.a', '.lib', '.dylib', '.o', '.obj',
    '.zip', '.tar', '.tar.gz', '.tgz', '.rar', '.7z', '.bz2', '.gz', '.xz', '.z', '.lz', '.lzma', '.lzo', '.rz', '.sz', '.dz',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.odt', '.ods', '.odp',
    '.png', '.jpg', '.jpeg', '.gif', '.mp3', '.mp4', '.wav', '.flac', '.ogg', '.avi', '.mkv', '.mov', '.webm', '.wmv', '.m4a', '.aac',
    '.iso', '.vmdk', '.qcow2', '.vdi', '.vhd', '.vhdx', '.ova', '.ovf',
    '.db', '.sqlite', '.mdb', '.accdb', '.frm', '.ibd', '.dbf',
    '.jar', '.class', '.war', '.ear', '.jpi',
    '.pyc', '.pyo', '.pyd', '.egg', '.whl',
    '.deb', '.rpm', '.apk', '.msi', '.dmg', '.pkg', '.bin', '.dat', '.data',
    '.dump', '.img', '.toast', '.vcd', '.crx', '.xpi', '.lockb', 'package-lock.json', '.svg' ,
    '.eot', '.otf', '.ttf', '.woff', '.woff2',
    '.ico', '.icns', '.cur',
    '.cab', '.dmp', '.msp', '.msm',
    '.keystore', '.jks', '.truststore', '.cer', '.crt', '.der', '.p7b', '.p7c', '.p12', '.pfx', '.pem', '.csr',
    '.key', '.pub', '.sig', '.pgp', '.gpg',
    '.nupkg', '.snupkg', '.appx', '.msix', '.msp', '.msu',
    '.deb', '.rpm', '.snap', '.flatpak', '.appimage',
    '.ko', '.sys', '.elf',
    '.swf', '.fla', '.swc',
    '.rlib', '.pdb', '.idb', '.pdb', '.dbg',
    '.sdf', '.bak', '.tmp', '.temp', '.log', '.tlog', '.ilk',
    '.bpl', '.dcu', '.dcp', '.dcpil', '.drc',
    '.aps', '.res', '.rsrc', '.rc', '.resx',
    '.prefs', '.properties', '.ini', '.cfg', '.config', '.conf',
    '.DS_Store', '.localized', '.svn', '.git', '.gitignore', '.gitkeep',
    'json', 'yaml',
]

CALLER_NODES = {
    'python': ['call', 'await', 'expression_statement', 'return_statement', 'print_statement', 'raise_statement', 'assert_statement', 'exec_statement'],
    'java': ['method_invocation', 'expression_statement', 'return_statement', 'assignment_expression', 'new_expression'],
    'cpp': ['call_expression', 'expression_statement', 'return_statement', 'assignment_expression', 'new_expression'],
    'c_sharp': ['invocation_expression', 'expression_statement', 'return_statement', 'assignment_expression', 'new_expression'],
    'javascript': ['call_expression', 'expression_statement', 'return_statement', 'assignment_expression', 'new_expression'],
    'typescript': ['call_expression', 'expression_statement', 'return_statement', 'assignment_expression', 'new_expression'],
    'go': ['call_expression', 'expression_statement', 'return_statement', 'assignment_statement', 'short_var_declaration'],
    'ruby': ['call', 'expression_statement', 'return', 'assignment', 'method_call'],
    'rust': ['call_expression', 'expression_statement', 'return_expression', 'assignment_expression', 'macro_invocation'],
    'r': ['call', 'expression_statement', 'return_statement', 'assignment', 'function_call_expression'],
    'css': ['call_expression', 'expression_statement', 'return_statement', 'assignment_expression'],
    'html': ['call_expression', 'expression_statement', 'return_statement', 'assignment_expression'],
    'php': ['function_call_expression', 'expression_statement', 'return_statement', 'assignment_expression', 'new_expression']
}

CALLEE_NODES = {
    'python': ['function_definition', 'class_definition', 'lambda', 'decorated_definition'],
    'java': ['method_declaration', 'class_declaration', 'interface_declaration', 'lambda_expression'],
    'cpp': ['function_definition', 'method_declaration', 'class_specifier', 'lambda_expression'],
    'c_sharp': ['method_declaration', 'class_declaration', 'interface_declaration', 'lambda_expression'],
    'javascript': ['function_declaration', 'method_definition', 'class_declaration', 'arrow_function', 'generator_function'],
    'typescript': ['function_declaration', 'method_definition', 'class_declaration', 'arrow_function', 'generator_function'],
    'go': ['function_declaration', 'method_declaration', 'func_literal'],
    'ruby': ['method', 'class', 'module', 'lambda', 'block'],
    'rust': ['function_item', 'const_item', 'macro_definition'],
    'r': ['function_definition'],
    'css': ['function_name'],
    'html': ['function_name'],
    'php': ['function_definition', 'method_declaration', 'class_declaration', 'anonymous_function', 'arrow_function']
}
