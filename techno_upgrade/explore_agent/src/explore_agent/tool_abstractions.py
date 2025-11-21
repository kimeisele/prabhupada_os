"""Intelligent tool abstractions for explore agent.

Instead of giving the LLM raw shell_run, we provide high-level "Baustein" tools
that are:
- Fast (no subprocess overhead for common operations)
- Safe (validation built-in, no injection possible)
- Composable (can be chained together)
- Semantic (LLM understands the intent, not the syntax)
"""

from pathlib import Path
from typing import Any, Dict, List, Optional


class ToolAbstraction:
    """Base class for intelligent tool abstractions."""

    def __init__(self, api: Any):
        self._api = api


class FileFinder(ToolAbstraction):
    """Find files matching patterns - like 'find' but safe and semantic."""

    # Standard ignore patterns for find command - prevents searching irrelevant directories
    DEFAULT_IGNORE_DIRS = [
        ".git",
        "venv",
        ".venv",
        "env",
        ".env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "node_modules",
        ".tox",
        "dist",
        "build",
        "*.egg-info",
    ]

    def search(
        self,
        directory: str = ".",
        name_pattern: str = "*",
        file_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Find files matching a pattern using native Python (fast, safe).

        Args:
            directory: Directory to search in
            name_pattern: Filename pattern (e.g., "*.py", "test_*.py")
            file_type: Optional type filter ("f"=file, "d"=dir)

        Returns:
            Dict with success status and list of found files
        """
        try:
            import os
            from fnmatch import fnmatch

            base_path = Path(directory).resolve()
            if not base_path.exists():
                return {
                    "success": False,
                    "detail": f"Directory not found: {directory}",
                    "files": [],
                    "data": [],
                }

            files = []

            # Walk directory tree with native Python (os.walk for compatibility)
            for root, dirs, filenames in os.walk(base_path):
                root_path = Path(root)

                # Filter out ignored directories IN-PLACE to prevent traversal
                dirs[:] = [
                    d
                    for d in dirs
                    if not any(
                        fnmatch(d, pattern) for pattern in self.DEFAULT_IGNORE_DIRS
                    )
                ]

                # Collect matching items based on type filter
                if file_type == "d":
                    # Looking for directories
                    for dirname in dirs:
                        if fnmatch(dirname, name_pattern):
                            files.append(str(root_path / dirname))
                else:
                    # Looking for files (default)
                    for filename in filenames:
                        if fnmatch(filename, name_pattern):
                            files.append(str(root_path / filename))

            return {
                "success": True,
                "files": files,
                "data": files,
                "count": len(files),
                "detail": f"Found {len(files)} file(s)",
            }
        except Exception as e:
            return {"success": False, "detail": str(e), "files": [], "data": []}


class ContentSearcher(ToolAbstraction):
    """Search file content - like 'grep' but semantic."""

    # Standard ignore patterns for grep - prevents searching irrelevant files
    DEFAULT_IGNORE_PATTERNS = [
        ".git",
        "venv",
        ".venv",
        "env",
        ".env",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "node_modules",
        ".tox",
        "dist",
        "build",
        "*.egg-info",
        ".coverage",
        "*.pyc",
    ]

    def search(
        self,
        pattern: str,
        files: Optional[List[str]] = None,
        directory: str = ".",
        regex: bool = True,
        case_sensitive: bool = False,
    ) -> Dict[str, Any]:
        """
        Search for pattern in files using native Python (fast, safe).

        Args:
            pattern: Text or regex pattern to search for
            files: Specific files to search (if None, searches directory)
            directory: Directory to search if files is None
            regex: Whether pattern is regex or literal
            case_sensitive: Case sensitivity

        Returns:
            Dict with matches
        """
        try:
            import os
            import re
            from fnmatch import fnmatch

            # Compile pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            if regex:
                pattern_re = re.compile(pattern, flags)
            else:
                pattern_re = re.compile(re.escape(pattern), flags)

            matches = []

            # Determine which files to search
            if files:
                search_files = [Path(f) for f in files if Path(f).is_file()]
            else:
                # Walk directory for text files (using os.walk for compatibility)
                search_files = []
                base_path = Path(directory).resolve()
                if base_path.exists():
                    for root, dirs, filenames in os.walk(base_path):
                        root_path = Path(root)

                        # Skip ignored directories IN-PLACE
                        dirs[:] = [
                            d
                            for d in dirs
                            if not any(
                                fnmatch(d, pat) for pat in self.DEFAULT_IGNORE_PATTERNS
                            )
                        ]

                        for filename in filenames:
                            # Skip ignored file patterns
                            if any(
                                fnmatch(filename, pat)
                                for pat in self.DEFAULT_IGNORE_PATTERNS
                            ):
                                continue
                            search_files.append(root_path / filename)

            # Search each file
            for file_path in search_files:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            if pattern_re.search(line):
                                matches.append(
                                    f"{file_path}:{line_num}:{line.rstrip()}"
                                )
                except (OSError, UnicodeDecodeError):
                    # Skip files that can't be read
                    continue

            return {
                "success": True,
                "matches": matches,
                "data": matches,
                "count": len(matches),
                "detail": f"Found {len(matches)} match(es)",
            }
        except Exception as e:
            return {"success": False, "detail": str(e), "matches": [], "data": []}


class CodeAnalyzer(ToolAbstraction):
    """Analyze code structure - Python AST based."""

    def find_functions(self, file_path: str) -> Dict[str, Any]:
        """Find all function definitions in a Python file."""
        try:
            import ast

            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "docstring": ast.get_docstring(node),
                        }
                    )

            return {
                "success": True,
                "functions": functions,
                "data": functions,  # ← Make data available
                "count": len(functions),
                "detail": f"Found {len(functions)} function(s)",
            }
        except Exception as e:
            return {"success": False, "detail": str(e), "functions": [], "data": []}

    def find_classes(self, file_path: str) -> Dict[str, Any]:
        """Find all class definitions in a Python file."""
        try:
            import ast

            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(
                        {
                            "name": node.name,
                            "line": node.lineno,
                            "docstring": ast.get_docstring(node),
                            "methods": [
                                m.name
                                for m in node.body
                                if isinstance(m, ast.FunctionDef)
                            ],
                        }
                    )

            return {
                "success": True,
                "classes": classes,
                "data": classes,  # ← Make data available
                "count": len(classes),
                "detail": f"Found {len(classes)} class(es)",
            }
        except Exception as e:
            return {"success": False, "detail": str(e), "classes": [], "data": []}

    def find_imports(self, file_path: str) -> Dict[str, Any]:
        """Find all imports in a Python file."""
        try:
            import ast

            with open(file_path, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())

            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({"module": alias.name, "type": "import"})
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for alias in node.names:
                        imports.append(
                            {
                                "module": f"{module}.{alias.name}",
                                "type": "from_import",
                            }
                        )

            return {
                "success": True,
                "imports": imports,
                "data": imports,  # ← Make data available
                "count": len(imports),
                "detail": f"Found {len(imports)} import(s)",
            }
        except Exception as e:
            return {"success": False, "detail": str(e), "imports": [], "data": []}


class DirectoryAnalyzer(ToolAbstraction):
    """Composite tool: Analyze entire directory without LLM iteration.

    This is the key solution to "Context Explosion". Instead of:
    1. LLM calls find_files (returns 30 files)
    2. LLM loops 30 times, calling analyze_python_file for each
    3. Context grows exponentially

    We do:
    1. LLM calls analyze_directory once
    2. Python loops internally 30 times
    3. Context grows only by the summary
    """

    def analyze(
        self,
        directory: str = ".",
        pattern: str = "*.py",
        file_type: str = "f",
    ) -> Dict[str, Any]:
        """
        Analyze all files in a directory matching pattern.
        Returns consolidated statistics, not individual results.

        Args:
            directory: Directory to analyze
            pattern: File pattern to match (e.g., "*.py")
            file_type: Type filter ("f"=file, "d"=dir)

        Returns:
            Dict with consolidated analysis results
        """
        try:
            # Step 1: Find all files matching pattern (in Python, not via LLM)
            finder = FileFinder(self._api)
            find_result = finder.search(
                directory=directory,
                name_pattern=pattern,
                file_type=file_type,
            )

            if not find_result["success"]:
                return {
                    "success": False,
                    "detail": find_result["detail"],
                    "data": None,
                }

            files = find_result["files"]

            # Step 2: Analyze each file (in Python loop, not via LLM)
            analyzer = CodeAnalyzer(self._api)
            total_classes = 0
            total_functions = 0
            total_imports = 0
            files_analyzed = 0
            errors = []

            for file_path in files:
                try:
                    if not Path(file_path).exists():
                        continue

                    classes_result = analyzer.find_classes(file_path)
                    funcs_result = analyzer.find_functions(file_path)
                    imports_result = analyzer.find_imports(file_path)

                    if classes_result["success"]:
                        total_classes += classes_result["count"]
                    if funcs_result["success"]:
                        total_functions += funcs_result["count"]
                    if imports_result["success"]:
                        total_imports += imports_result["count"]

                    files_analyzed += 1

                except Exception as e:
                    errors.append(f"{file_path}: {str(e)}")

            # Step 3: Return consolidated summary (not individual results)
            summary = {
                "success": True,
                "directory": directory,
                "pattern": pattern,
                "files_found": len(files),
                "files_analyzed": files_analyzed,
                "total_classes": total_classes,
                "total_functions": total_functions,
                "total_imports": total_imports,
                "errors": errors,
                "detail": (
                    f"Analyzed {files_analyzed}/{len(files)} files: "
                    f"{total_classes} classes, {total_functions} functions, "
                    f"{total_imports} imports"
                ),
                "data": {
                    "total_classes": total_classes,
                    "total_functions": total_functions,
                    "total_imports": total_imports,
                    "files_analyzed": files_analyzed,
                },
            }

            return summary

        except Exception as e:
            return {"success": False, "detail": str(e), "data": None}

    def search_codebase(
        self,
        directory: str = ".",
        pattern: str = "*",
        content_pattern: str = None,
        file_type: str = "f",
    ) -> Dict[str, Any]:
        """
        Find files matching pattern, optionally filtering by content.
        Returns consolidated results.

        Args:
            directory: Directory to search
            pattern: File name pattern
            content_pattern: Optional content regex to filter files
            file_type: Type filter

        Returns:
            Dict with consolidated search results
        """
        try:
            finder = FileFinder(self._api)
            find_result = finder.search(
                directory=directory,
                name_pattern=pattern,
                file_type=file_type,
            )

            if not find_result["success"]:
                return {
                    "success": False,
                    "detail": find_result["detail"],
                    "data": None,
                }

            files = find_result["files"]

            # If no content pattern, just return the files
            if not content_pattern:
                return {
                    "success": True,
                    "files_found": len(files),
                    "files": files,
                    "data": {
                        "files_found": len(files),
                        "files": files[:100],  # Limit to 100 for context
                    },
                    "detail": f"Found {len(files)} file(s)",
                }

            # If content pattern specified, filter files by content
            searcher = ContentSearcher(self._api)
            matching_files = []

            for file_path in files:
                search_result = searcher.search(
                    pattern=content_pattern,
                    files=[file_path],
                    regex=True,
                )
                if search_result["success"] and search_result["matches"]:
                    matching_files.append(
                        {
                            "file": file_path,
                            "matches": len(search_result["matches"]),
                        }
                    )

            return {
                "success": True,
                "files_found": len(files),
                "files_matching_content": len(matching_files),
                "matching_files": matching_files,
                "data": {
                    "files_found": len(files),
                    "files_matching_content": len(matching_files),
                    "matching_files": matching_files[:50],  # Limit for context
                },
                "detail": (
                    f"Found {len(matching_files)}/{len(files)} file(s) matching content"
                ),
            }

        except Exception as e:
            return {"success": False, "detail": str(e), "data": None}
