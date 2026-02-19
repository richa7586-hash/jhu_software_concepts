from types import SimpleNamespace
import runpy
import subprocess

import config

import pytest

import clean


@pytest.mark.db
def test_load_data_reads_json(tmp_path):
    # Load a valid JSON file and return parsed data.
    data_path = tmp_path / "data.json"
    data_path.write_text('[{"key": "value"}]', encoding="utf-8")

    data = clean.load_data(str(data_path))

    assert data == [{"key": "value"}]


@pytest.mark.db
def test_load_data_uses_default_path(tmp_path, monkeypatch):
    # Default file path should be taken from config.DATA_FILE.
    data_path = tmp_path / "default.json"
    data_path.write_text('[{"ok": true}]', encoding="utf-8")
    monkeypatch.setattr(config, "DATA_FILE", str(data_path))

    data = clean.load_data()

    assert data == [{"ok": True}]


@pytest.mark.db
def test_load_data_missing_file_returns_empty_list(tmp_path):
    # Missing files should return an empty list.
    missing_path = tmp_path / "missing.json"

    data = clean.load_data(str(missing_path))

    assert data == []


@pytest.mark.db
def test_load_data_invalid_json_returns_empty_list(tmp_path):
    # Invalid JSON should return an empty list.
    data_path = tmp_path / "bad.json"
    data_path.write_text("{", encoding="utf-8")

    data = clean.load_data(str(data_path))

    assert data == []


@pytest.mark.db
def test_clean_data_missing_input_returns_false(tmp_path, monkeypatch):
    # Missing input should short-circuit without invoking subprocess.
    missing_input = tmp_path / "missing.json"
    llm_script = tmp_path / "llm.py"
    llm_script.write_text("# stub", encoding="utf-8")

    def fail_run(*_args, **_kwargs):
        # Guard against unexpected subprocess execution.
        raise AssertionError("subprocess.run should not be called")

    monkeypatch.setattr(clean.subprocess, "run", fail_run)

    result = clean.clean_data(
        input_file=str(missing_input),
        llm_script_path=str(llm_script),
        output_file=str(tmp_path / "out.jsonl"),
    )

    assert result is False


@pytest.mark.db
def test_clean_data_missing_llm_script_returns_false(tmp_path, monkeypatch):
    # Missing LLM script should short-circuit without invoking subprocess.
    input_path = tmp_path / "input.json"
    input_path.write_text("[]", encoding="utf-8")
    missing_script = tmp_path / "missing_llm.py"

    def fail_run(*_args, **_kwargs):
        # Guard against unexpected subprocess execution.
        raise AssertionError("subprocess.run should not be called")

    monkeypatch.setattr(clean.subprocess, "run", fail_run)

    result = clean.clean_data(
        input_file=str(input_path),
        llm_script_path=str(missing_script),
        output_file=str(tmp_path / "out.jsonl"),
    )

    assert result is False


@pytest.mark.db
def test_clean_data_uses_default_paths(tmp_path, monkeypatch):
    # Default input/output paths should come from config.
    input_path = tmp_path / "input.json"
    input_path.write_text("[]", encoding="utf-8")
    output_path = tmp_path / "out.jsonl"
    llm_script = tmp_path / "llm.py"
    llm_script.write_text("# stub", encoding="utf-8")

    monkeypatch.setattr(config, "DATA_FILE", str(input_path))
    monkeypatch.setattr(config, "APPLICANT_DATA_JSON_FILE", str(output_path))

    calls = {}

    def fake_run(args, capture_output, text, check):
        # Capture subprocess arguments without executing the script.
        calls["args"] = args
        return SimpleNamespace(stdout="")

    monkeypatch.setattr(clean.subprocess, "run", fake_run)

    result = clean.clean_data(llm_script_path=str(llm_script))

    assert result is True
    assert calls["args"] == [
        "python",
        str(llm_script),
        "--file",
        str(input_path),
        "--out",
        str(output_path),
    ]


@pytest.mark.db
def test_clean_data_runs_subprocess_success(tmp_path, monkeypatch):
    # Successful subprocess execution should return True.
    input_path = tmp_path / "input.json"
    input_path.write_text("[]", encoding="utf-8")
    llm_script = tmp_path / "llm.py"
    llm_script.write_text("# stub", encoding="utf-8")
    output_path = tmp_path / "out.jsonl"

    calls = {}

    def fake_run(args, capture_output, text, check):
        # Capture subprocess arguments without executing the script.
        calls["args"] = args
        calls["capture_output"] = capture_output
        calls["text"] = text
        calls["check"] = check
        return SimpleNamespace(stdout="ok")

    monkeypatch.setattr(clean.subprocess, "run", fake_run)

    result = clean.clean_data(
        input_file=str(input_path),
        llm_script_path=str(llm_script),
        output_file=str(output_path),
    )

    assert result is True
    assert calls["args"] == [
        "python",
        str(llm_script),
        "--file",
        str(input_path),
        "--out",
        str(output_path),
    ]
    assert calls["capture_output"] is True
    assert calls["text"] is True
    assert calls["check"] is True


@pytest.mark.db
def test_clean_data_subprocess_failure_returns_false(tmp_path, monkeypatch):
    # Subprocess failures should return False.
    input_path = tmp_path / "input.json"
    input_path.write_text("[]", encoding="utf-8")
    llm_script = tmp_path / "llm.py"
    llm_script.write_text("# stub", encoding="utf-8")

    def fail_run(*_args, **_kwargs):
        # Simulate a subprocess failure.
        raise subprocess.CalledProcessError(1, ["python", "llm.py"], stderr="boom")

    monkeypatch.setattr(clean.subprocess, "run", fail_run)

    result = clean.clean_data(
        input_file=str(input_path),
        llm_script_path=str(llm_script),
        output_file=str(tmp_path / "out.jsonl"),
    )

    assert result is False


@pytest.mark.db
def test_clean_data_unexpected_exception_returns_false(tmp_path, monkeypatch):
    # Generic exceptions should return False.
    input_path = tmp_path / "input.json"
    input_path.write_text("[]", encoding="utf-8")
    llm_script = tmp_path / "llm.py"
    llm_script.write_text("# stub", encoding="utf-8")

    def fail_run(*_args, **_kwargs):
        # Simulate an unexpected exception.
        raise RuntimeError("boom")

    monkeypatch.setattr(clean.subprocess, "run", fail_run)

    result = clean.clean_data(
        input_file=str(input_path),
        llm_script_path=str(llm_script),
        output_file=str(tmp_path / "out.jsonl"),
    )

    assert result is False


@pytest.mark.db
def test_clean_module_main_runs(monkeypatch, tmp_path):
    # Execute the __main__ block without running external scripts.
    data_path = tmp_path / "data.json"
    data_path.write_text("[1]", encoding="utf-8")
    monkeypatch.setattr(config, "DATA_FILE", str(data_path))
    monkeypatch.setattr(config, "APPLICANT_DATA_JSON_FILE", str(tmp_path / "out.jsonl"))

    def fake_run(*_args, **_kwargs):
        # Stub subprocess execution during main.
        return SimpleNamespace(stdout="")

    real_exists = clean.os.path.exists

    def fake_exists(path):
        # Pretend the LLM script exists while honoring real file checks.
        if path == "../llm_hosting/app.py":
            return True
        return real_exists(path)

    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(clean.os.path, "exists", fake_exists)

    runpy.run_module("clean", run_name="__main__")
