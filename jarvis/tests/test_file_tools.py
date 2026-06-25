"""Tests for the working file tools."""
from __future__ import annotations

from jarvis.tools.file_tools import (
    CreateFileTool,
    DeleteFileTool,
    ListDirectoryTool,
    MoveFileTool,
    ReadTextFileTool,
    SearchFilesTool,
    WriteTextFileTool,
)


def test_create_read_roundtrip(tmp_path):
    path = tmp_path / "note.txt"
    create = CreateFileTool()
    res = create.execute(create.validate_args({"path": str(path), "content": "hello"}))
    assert res.success
    assert path.read_text() == "hello"

    read = ReadTextFileTool()
    rres = read.execute(read.validate_args({"path": str(path)}))
    assert rres.success
    assert rres.data["content"] == "hello"


def test_create_fails_if_exists(tmp_path):
    path = tmp_path / "x.txt"
    path.write_text("a")
    create = CreateFileTool()
    res = create.execute(create.validate_args({"path": str(path), "content": "b"}))
    assert not res.success


def test_write_overwrites(tmp_path):
    path = tmp_path / "w.txt"
    path.write_text("old")
    write = WriteTextFileTool()
    res = write.execute(write.validate_args({"path": str(path), "content": "new"}))
    assert res.success
    assert path.read_text() == "new"


def test_write_tool_requires_confirmation_flag():
    assert WriteTextFileTool().requires_confirmation is True


def test_delete_always_requires_confirmation():
    tool = DeleteFileTool()
    assert tool.requires_confirmation is True
    assert tool.extreme_risk is True


def test_delete_removes_file(tmp_path):
    path = tmp_path / "del.txt"
    path.write_text("bye")
    tool = DeleteFileTool()
    res = tool.execute(tool.validate_args({"path": str(path)}))
    assert res.success
    assert not path.exists()


def test_delete_refuses_directory(tmp_path):
    tool = DeleteFileTool()
    res = tool.execute(tool.validate_args({"path": str(tmp_path)}))
    assert not res.success


def test_move_file(tmp_path):
    src = tmp_path / "a.txt"
    src.write_text("data")
    dst = tmp_path / "b.txt"
    tool = MoveFileTool()
    res = tool.execute(tool.validate_args({"source": str(src), "destination": str(dst)}))
    assert res.success
    assert dst.exists() and not src.exists()


def test_list_directory(tmp_path):
    (tmp_path / "one.txt").write_text("1")
    (tmp_path / "two.txt").write_text("2")
    tool = ListDirectoryTool()
    res = tool.execute(tool.validate_args({"path": str(tmp_path)}))
    assert res.success
    names = {e["name"] for e in res.data["entries"]}
    assert {"one.txt", "two.txt"} <= names


def test_search_files(tmp_path):
    (tmp_path / "report_2024.txt").write_text("x")
    (tmp_path / "other.md").write_text("y")
    tool = SearchFilesTool()
    res = tool.execute(tool.validate_args({"query": "report", "folder": str(tmp_path)}))
    assert res.success
    assert any("report_2024.txt" in m for m in res.data["matches"])
