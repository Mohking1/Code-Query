import os

from tree_sitter import Language, Parser

LANGUAGE_LOADERS: dict = {}


def _init_languages():
    if LANGUAGE_LOADERS:
        return

    try:
        import tree_sitter_python

        LANGUAGE_LOADERS["python"] = Language(tree_sitter_python.language())
    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"Failed to load tree-sitter python: {e}")

    try:
        import tree_sitter_javascript

        LANGUAGE_LOADERS["javascript"] = Language(tree_sitter_javascript.language())
    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"Failed to load tree-sitter javascript: {e}")

    try:
        import tree_sitter_typescript

        LANGUAGE_LOADERS["typescript"] = Language(
            tree_sitter_typescript.language_typescript()
        )
        LANGUAGE_LOADERS["tsx"] = Language(tree_sitter_typescript.language_tsx())
    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"Failed to load tree-sitter typescript: {e}")

    try:
        import tree_sitter_go

        LANGUAGE_LOADERS["go"] = Language(tree_sitter_go.language())
    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"Failed to load tree-sitter go: {e}")

    try:
        import tree_sitter_rust

        LANGUAGE_LOADERS["rust"] = Language(tree_sitter_rust.language())
    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"Failed to load tree-sitter rust: {e}")

    try:
        import tree_sitter_java

        LANGUAGE_LOADERS["java"] = Language(tree_sitter_java.language())
    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"Failed to load tree-sitter java: {e}")

    try:
        import tree_sitter_c

        LANGUAGE_LOADERS["c"] = Language(tree_sitter_c.language())
    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"Failed to load tree-sitter c: {e}")

    try:
        import tree_sitter_cpp

        LANGUAGE_LOADERS["cpp"] = Language(tree_sitter_cpp.language())
    except (ImportError, AttributeError, RuntimeError) as e:
        print(f"Failed to load tree-sitter cpp: {e}")


EXTENSION_TO_LANG = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
}


def get_parser_and_language(file_path: str) -> tuple[Parser | None, str | None]:
    _init_languages()
    ext = os.path.splitext(file_path)[1].lower()
    lang_name = EXTENSION_TO_LANG.get(ext)
    if not lang_name:
        return None, None

    lang = LANGUAGE_LOADERS.get(lang_name)
    if not lang:
        return None, lang_name

    try:
        parser = Parser(lang)
        return parser, lang_name
    except (TypeError, ValueError, RuntimeError):
        try:
            parser = Parser()
            parser.language = lang
            return parser, lang_name
        except (TypeError, ValueError, RuntimeError):
            return None, lang_name
