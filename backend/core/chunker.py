from pydantic import BaseModel

from backend.core.tree_sitter_parsers import get_parser_and_language


class CodeChunk(BaseModel):
    chunk_id: str
    file_path: str
    language: str
    chunk_type: str
    symbol_name: str | None = None
    parent_symbol: str | None = None
    start_line: int
    end_line: int
    start_col: int = 0
    end_col: int = 0
    code: str
    docstring: str | None = None


class SemanticChunker:
    def chunk_file(self, file_path: str, content: str) -> list[CodeChunk]:
        if not content or not content.strip():
            return []

        parser, language = get_parser_and_language(file_path)
        if parser and language:
            try:
                tree = parser.parse(bytes(content, "utf8"))
                chunks = self._extract_nodes(
                    file_path, content, tree.root_node, language
                )
                if chunks:
                    return chunks
            except (ValueError, TypeError, RuntimeError) as e:
                print(f"Error parsing {file_path} with Tree-sitter: {e}")

        return self._fallback_chunking(file_path, content, language or "text")

    def _extract_docstring(self, node, content_bytes: bytes) -> str | None:
        def find_string_or_comment(n, depth=0):
            if depth > 3:
                return None
            if n.type in ("string", "comment", "block_comment", "line_comment"):
                raw = (
                    content_bytes[n.start_byte : n.end_byte]
                    .decode("utf-8", errors="ignore")
                    .strip()
                )
                return raw.strip("\"'/* \t\n")
            if n.type in ("block", "expression_statement", "body", "statement_block"):
                for child in n.children:
                    res = find_string_or_comment(child, depth + 1)
                    if res:
                        return res
            return None

        for child in node.children:
            doc = find_string_or_comment(child)
            if doc:
                return doc
        return None

    def _extract_nodes(
        self, file_path: str, content: str, root_node, language: str
    ) -> list[CodeChunk]:
        chunks: list[CodeChunk] = []
        lines = content.splitlines()
        content_bytes = bytes(content, "utf8")

        def traverse(node, current_parent: str | None = None):
            node_type = node.type
            symbol_name = None
            chunk_type = None

            if any(
                k in node_type
                for k in (
                    "function_definition",
                    "function_item",
                    "function_declaration",
                    "method_definition",
                    "method_declaration",
                    "arrow_function",
                    "function",
                )
            ):
                chunk_type = "method" if current_parent else "function"
                for child in node.children:
                    if child.type in (
                        "identifier",
                        "name",
                        "property_identifier",
                        "field_identifier",
                        "type_identifier",
                    ):
                        symbol_name = content_bytes[
                            child.start_byte : child.end_byte
                        ].decode("utf-8", errors="ignore")
                        break
            elif any(
                k in node_type
                for k in (
                    "class_definition",
                    "class_declaration",
                    "struct_specifier",
                    "struct_item",
                    "interface_declaration",
                    "impl_item",
                    "class",
                    "interface",
                )
            ):
                chunk_type = "class"
                for child in node.children:
                    if child.type in ("identifier", "name", "type_identifier"):
                        symbol_name = content_bytes[
                            child.start_byte : child.end_byte
                        ].decode("utf-8", errors="ignore")
                        break

            if chunk_type:
                start_row = node.start_point[0]
                end_row = node.end_point[0]
                start_line = start_row + 1
                end_line = end_row + 1

                if start_row < len(lines):
                    code_snippet = "\n".join(
                        lines[start_row : min(len(lines), end_row + 1)]
                    )
                else:
                    code_snippet = content_bytes[
                        node.start_byte : node.end_byte
                    ].decode("utf-8", errors="ignore")

                docstring = self._extract_docstring(node, content_bytes)

                cid = f"{file_path}::{symbol_name or 'block'}::{start_line}_{end_line}"
                chunks.append(
                    CodeChunk(
                        chunk_id=cid,
                        file_path=file_path,
                        language=language,
                        chunk_type=chunk_type,
                        symbol_name=symbol_name,
                        parent_symbol=current_parent,
                        start_line=start_line,
                        end_line=end_line,
                        start_col=node.start_point[1],
                        end_col=node.end_point[1],
                        code=code_snippet,
                        docstring=docstring,
                    )
                )

            next_parent = symbol_name if chunk_type == "class" else current_parent
            for child in node.children:
                traverse(child, next_parent)

        traverse(root_node)
        return chunks

    def _fallback_chunking(
        self, file_path: str, content: str, language: str
    ) -> list[CodeChunk]:
        lines = content.splitlines()
        chunks: list[CodeChunk] = []
        window_size = 50
        step = 40

        for i in range(0, max(1, len(lines)), step):
            window_lines = lines[i : i + window_size]
            if not window_lines:
                break
            start_line = i + 1
            end_line = min(len(lines), i + len(window_lines))
            code_snippet = "\n".join(window_lines)
            chunks.append(
                CodeChunk(
                    chunk_id=f"{file_path}::block::{start_line}_{end_line}",
                    file_path=file_path,
                    language=language,
                    chunk_type="block",
                    symbol_name=None,
                    parent_symbol=None,
                    start_line=start_line,
                    end_line=end_line,
                    code=code_snippet,
                )
            )
        return chunks
