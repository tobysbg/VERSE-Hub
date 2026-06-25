"""File system tools - real, working implementations.

Safety notes baked in:
  * ``write_text_file`` escalates to HIGH risk + confirmation when it would
    overwrite an existing file.
  * ``move_file`` always requires confirmation.
  * ``delete_file`` ALWAYS requires confirmation and is treated as HIGH risk.
  * Reads/searches/listing are low risk.
A large ``MAX_READ_BYTES`` guard prevents accidentally slurping huge files.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

from pydantic import BaseModel, Field

from ..storage.models import RiskLevel
from .base_tool import BaseTool, ToolResult

MAX_READ_BYTES = 2_000_000  # 2 MB safety cap for text reads


def _expand(path: str) -> Path:
    return Path(os.path.expanduser(os.path.expandvars(path))).resolve()


# --------------------------------------------------------------------------- #
# search_files
# --------------------------------------------------------------------------- #
class SearchFilesArgs(BaseModel):
    query: str = Field(..., description="Filename substring or glob to search for.")
    folder: str = Field(default="~", description="Folder to search within (recursive).")
    max_results: int = Field(default=50, ge=1, le=500)


class SearchFilesTool(BaseTool):
    name = "search_files"
    description = "Search for files by name within a folder (recursive)."
    InputModel = SearchFilesArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: SearchFilesArgs) -> str:
        return f"Search for files matching '{args.query}' under {args.folder}."

    def execute(self, args: SearchFilesArgs) -> ToolResult:
        root = _expand(args.folder)
        if not root.exists() or not root.is_dir():
            return ToolResult.fail(f"Folder does not exist: {root}")
        pattern = args.query if any(c in args.query for c in "*?[") else f"*{args.query}*"
        matches: list[str] = []
        try:
            for p in root.rglob(pattern):
                matches.append(str(p))
                if len(matches) >= args.max_results:
                    break
        except (PermissionError, OSError) as exc:
            return ToolResult.fail(f"Search error: {exc}")
        return ToolResult.ok(
            f"Found {len(matches)} match(es).", matches=matches
        )


# --------------------------------------------------------------------------- #
# list_directory
# --------------------------------------------------------------------------- #
class ListDirArgs(BaseModel):
    path: str = Field(default="~", description="Directory to list.")


class ListDirectoryTool(BaseTool):
    name = "list_directory"
    description = "List the entries of a directory."
    InputModel = ListDirArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: ListDirArgs) -> str:
        return f"List the contents of {args.path}."

    def execute(self, args: ListDirArgs) -> ToolResult:
        path = _expand(args.path)
        if not path.exists() or not path.is_dir():
            return ToolResult.fail(f"Directory does not exist: {path}")
        try:
            entries = []
            for entry in sorted(path.iterdir(), key=lambda e: (e.is_file(), e.name.lower())):
                entries.append(
                    {"name": entry.name, "is_dir": entry.is_dir(),
                     "size": entry.stat().st_size if entry.is_file() else None}
                )
        except (PermissionError, OSError) as exc:
            return ToolResult.fail(f"Cannot list directory: {exc}")
        return ToolResult.ok(f"{len(entries)} entries in {path}.", entries=entries)


# --------------------------------------------------------------------------- #
# read_text_file
# --------------------------------------------------------------------------- #
class ReadFileArgs(BaseModel):
    path: str = Field(..., description="Path to the text file to read.")


class ReadTextFileTool(BaseTool):
    name = "read_text_file"
    description = "Read the contents of a UTF-8 text file (up to 2 MB)."
    InputModel = ReadFileArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: ReadFileArgs) -> str:
        return f"Read the text file at {args.path}."

    def execute(self, args: ReadFileArgs) -> ToolResult:
        path = _expand(args.path)
        if not path.exists() or not path.is_file():
            return ToolResult.fail(f"File does not exist: {path}")
        if path.stat().st_size > MAX_READ_BYTES:
            return ToolResult.fail(
                f"File is too large to read safely (> {MAX_READ_BYTES} bytes)."
            )
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return ToolResult.fail(f"Read error: {exc}")
        return ToolResult.ok(f"Read {len(content)} characters.", content=content)


# --------------------------------------------------------------------------- #
# open_file
# --------------------------------------------------------------------------- #
class OpenFileArgs(BaseModel):
    path: str = Field(..., description="Path to the file to open with its default app.")


class OpenFileTool(BaseTool):
    name = "open_file"
    description = "Open a file with the operating system's default application."
    InputModel = OpenFileArgs
    risk_level = RiskLevel.LOW

    def preview(self, args: OpenFileArgs) -> str:
        return f"Open {args.path} with its default application."

    def execute(self, args: OpenFileArgs) -> ToolResult:
        import subprocess
        import sys

        path = _expand(args.path)
        if not path.exists():
            return ToolResult.fail(f"File does not exist: {path}")
        try:
            if sys.platform == "win32":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception as exc:  # noqa: BLE001
            return ToolResult.fail(f"Could not open file: {exc}")
        return ToolResult.ok(f"Opened {path}.")


# --------------------------------------------------------------------------- #
# create_file
# --------------------------------------------------------------------------- #
class CreateFileArgs(BaseModel):
    path: str = Field(..., description="Path of the new file to create.")
    content: str = Field(default="", description="Initial text content.")


class CreateFileTool(BaseTool):
    name = "create_file"
    description = "Create a new text file. Fails if the file already exists."
    InputModel = CreateFileArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True

    def preview(self, args: CreateFileArgs) -> str:
        return (
            f"Create a new file at {args.path} "
            f"({len(args.content)} characters of content)."
        )

    def execute(self, args: CreateFileArgs) -> ToolResult:
        path = _expand(args.path)
        if path.exists():
            return ToolResult.fail(
                f"File already exists: {path}. Use write_text_file to overwrite."
            )
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(args.content, encoding="utf-8")
        except OSError as exc:
            return ToolResult.fail(f"Could not create file: {exc}")
        return ToolResult.ok(f"Created {path}.")


# --------------------------------------------------------------------------- #
# write_text_file (dynamic risk: HIGH when overwriting)
# --------------------------------------------------------------------------- #
class WriteFileArgs(BaseModel):
    path: str = Field(..., description="Path of the file to write.")
    content: str = Field(..., description="Full text content to write.")


class WriteTextFileTool(BaseTool):
    name = "write_text_file"
    description = "Write text to a file, creating it or overwriting if it exists."
    InputModel = WriteFileArgs
    risk_level = RiskLevel.MEDIUM
    requires_confirmation = True

    def dynamic_risk(self, args: WriteFileArgs) -> RiskLevel:
        # Overwriting existing data is higher risk than creating new content.
        return RiskLevel.HIGH if _expand(args.path).exists() else RiskLevel.MEDIUM

    def preview(self, args: WriteFileArgs) -> str:
        path = _expand(args.path)
        verb = "OVERWRITE existing file" if path.exists() else "Create file"
        return f"{verb} at {path} with {len(args.content)} characters."

    def execute(self, args: WriteFileArgs) -> ToolResult:
        path = _expand(args.path)
        existed = path.exists()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(args.content, encoding="utf-8")
        except OSError as exc:
            return ToolResult.fail(f"Could not write file: {exc}")
        verb = "Overwrote" if existed else "Wrote"
        return ToolResult.ok(f"{verb} {path}.")


# --------------------------------------------------------------------------- #
# move_file (always confirm)
# --------------------------------------------------------------------------- #
class MoveFileArgs(BaseModel):
    source: str = Field(..., description="Path of the file/folder to move.")
    destination: str = Field(..., description="Destination path.")


class MoveFileTool(BaseTool):
    name = "move_file"
    description = "Move or rename a file or folder."
    InputModel = MoveFileArgs
    risk_level = RiskLevel.HIGH
    requires_confirmation = True

    def preview(self, args: MoveFileArgs) -> str:
        return f"Move {args.source} -> {args.destination}."

    def execute(self, args: MoveFileArgs) -> ToolResult:
        src = _expand(args.source)
        dst = _expand(args.destination)
        if not src.exists():
            return ToolResult.fail(f"Source does not exist: {src}")
        try:
            shutil.move(str(src), str(dst))
        except (OSError, shutil.Error) as exc:
            return ToolResult.fail(f"Could not move: {exc}")
        return ToolResult.ok(f"Moved {src} to {dst}.")


# --------------------------------------------------------------------------- #
# delete_file (ALWAYS confirm, HIGH risk)
# --------------------------------------------------------------------------- #
class DeleteFileArgs(BaseModel):
    path: str = Field(..., description="Path of the file to delete.")


class DeleteFileTool(BaseTool):
    name = "delete_file"
    description = "Delete a single file. Always requires explicit confirmation."
    InputModel = DeleteFileArgs
    risk_level = RiskLevel.HIGH
    requires_confirmation = True
    extreme_risk = True  # only "Allow once" - never "always allow"

    def preview(self, args: DeleteFileArgs) -> str:
        return f"PERMANENTLY DELETE the file at {args.path}."

    def execute(self, args: DeleteFileArgs) -> ToolResult:
        path = _expand(args.path)
        if not path.exists():
            return ToolResult.fail(f"File does not exist: {path}")
        if path.is_dir():
            return ToolResult.fail(
                f"{path} is a directory. This tool only deletes single files."
            )
        try:
            path.unlink()
        except OSError as exc:
            return ToolResult.fail(f"Could not delete: {exc}")
        return ToolResult.ok(f"Deleted {path}.")


def build_file_tools() -> list[BaseTool]:
    return [
        SearchFilesTool(),
        ListDirectoryTool(),
        ReadTextFileTool(),
        OpenFileTool(),
        CreateFileTool(),
        WriteTextFileTool(),
        MoveFileTool(),
        DeleteFileTool(),
    ]
