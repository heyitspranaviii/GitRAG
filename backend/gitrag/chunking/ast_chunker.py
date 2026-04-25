from __future__ import annotations
import re
from gitrag.core.types import Chunk, ChunkType, RawFile
from gitrag.core.logging import get_logger
from gitrag.chunking.text_chunker import chunk_by_window

logger = get_logger(__name__)

def _try_import(mod_name: str):
    try: return __import__(mod_name)
    except ImportError: return None

_ts_python     = _try_import("tree_sitter_python")
_ts_javascript = _try_import("tree_sitter_javascript")
_ts_typescript = _try_import("tree_sitter_typescript")
_ts_java       = _try_import("tree_sitter_java")
_ts_go         = _try_import("tree_sitter_go")
_ts_rust       = _try_import("tree_sitter_rust")
_ts_c          = _try_import("tree_sitter_c")
_ts_cpp        = _try_import("tree_sitter_cpp")
_ts_csharp     = _try_import("tree_sitter_c_sharp")
_ts_ruby       = _try_import("tree_sitter_ruby")
_ts_php        = _try_import("tree_sitter_php")

try:
    from tree_sitter import Language, Parser
    TS_CORE = True
except ImportError:
    TS_CORE = False

LANG_REGISTRY: dict[str, tuple] = {
    "python":     (_ts_python,     ["function_definition","async_function_definition"], ["class_definition"]),
    "javascript": (_ts_javascript, ["function_declaration","arrow_function","function_expression","method_definition"], ["class_declaration","class_expression"]),
    "typescript": (_ts_typescript, ["function_declaration","arrow_function","function_expression","method_definition","function_signature"], ["class_declaration","class_expression","interface_declaration"]),
    "java":       (_ts_java,       ["method_declaration","constructor_declaration"], ["class_declaration","interface_declaration","enum_declaration"]),
    "go":         (_ts_go,         ["function_declaration","method_declaration","func_literal"], ["type_declaration"]),
    "rust":       (_ts_rust,       ["function_item","closure_expression"], ["struct_item","impl_item","trait_item","enum_item"]),
    "c":          (_ts_c,          ["function_definition"], ["struct_specifier","enum_specifier"]),
    "cpp":        (_ts_cpp,        ["function_definition","lambda_expression"], ["class_specifier","struct_specifier","namespace_definition"]),
    "csharp":     (_ts_csharp,     ["method_declaration","constructor_declaration","local_function_statement"], ["class_declaration","interface_declaration","struct_declaration","namespace_declaration"]),
    "ruby":       (_ts_ruby,       ["method","singleton_method"], ["class","module"]),
    "php":        (_ts_php,        ["function_definition","method_declaration"], ["class_declaration","interface_declaration","trait_declaration"]),
}

def _make_id(file: str, symbol: str, start: int) -> str:
    return re.sub(r"[^\w]", "_", file) + f"__{symbol}__{start}"

def _extract_name(node, source: bytes) -> str:
    for child in node.children:
        if child.type in ("name","identifier","property_identifier"):
            return source[child.start_byte:child.end_byte].decode("utf-8","ignore")
    n = node.child_by_field_name("name")
    if n: return source[n.start_byte:n.end_byte].decode("utf-8","ignore")
    return f"<anonymous>_{node.start_point[0]+1}"

def _extract_docstring(node, source: bytes, lang: str) -> str:
    try:
        if lang == "python":
            for child in node.children:
                if child.type == "block":
                    for stmt in child.children:
                        if stmt.type == "expression_statement":
                            for sub in stmt.children:
                                if sub.type == "string":
                                    raw = source[sub.start_byte:sub.end_byte].decode("utf-8","ignore")
                                    return raw.strip('"""').strip("'''").strip('"').strip("'").strip()
        else:
            prev = node.prev_sibling
            if prev and prev.type in ("comment","block_comment","line_comment"):
                raw = source[prev.start_byte:prev.end_byte].decode("utf-8","ignore")
                return raw.strip("/*").strip("*/").strip("///").strip("//").strip()
    except Exception:
        pass
    return ""

def _chunk_with_treesitter(raw_file: RawFile) -> list[Chunk]:
    lang = raw_file.language
    if lang not in LANG_REGISTRY or not TS_CORE:
        return []
    ts_module, func_types, class_types = LANG_REGISTRY[lang]
    if ts_module is None:
        return []
    try:
        ts_lang = Language(ts_module.language())
        parser  = Parser(ts_lang)
    except Exception as e:
        logger.warning("grammar_load_failed", language=lang, error=str(e))
        return []
    source_bytes = raw_file.content.encode("utf-8")
    try:
        tree = parser.parse(source_bytes)
    except Exception:
        return []
    chunks: list[Chunk] = []
    def walk(node):
        is_func  = node.type in func_types
        is_class = node.type in class_types
        if is_func or is_class:
            name = _extract_name(node, source_bytes)
            text = source_bytes[node.start_byte:node.end_byte].decode("utf-8","ignore")
            chunks.append(Chunk(
                chunk_id   =_make_id(raw_file.path, name, node.start_point[0]+1),
                symbol_name=name, file=raw_file.path, language=lang,
                start_line =node.start_point[0]+1, end_line=node.end_point[0]+1,
                raw_text   =text,
                docstring  =_extract_docstring(node, source_bytes, lang),
                chunk_type =ChunkType.CLASS if is_class else ChunkType.FUNCTION,
            ))
        for child in node.children:
            walk(child)
    walk(tree.root_node)
    return chunks

def chunk_file(raw_file: RawFile) -> list[Chunk]:
    chunks = _chunk_with_treesitter(raw_file)
    return chunks if chunks else chunk_by_window(raw_file)

def chunk_repo(raw_files: list[RawFile]) -> list[Chunk]:
    all_chunks: list[Chunk] = []
    lang_counts: dict[str, int] = {}
    for f in raw_files:
        fc = chunk_file(f)
        all_chunks.extend(fc)
        lang_counts[f.language] = lang_counts.get(f.language, 0) + len(fc)
    logger.info("chunking_complete", total=len(all_chunks), breakdown=lang_counts)
    return all_chunks
