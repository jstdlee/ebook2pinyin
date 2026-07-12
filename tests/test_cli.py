from typer.testing import CliRunner

import ebook2pinyin.cli as cli


def test_doctor_reports_external_dependencies(monkeypatch):
    runner = CliRunner()

    monkeypatch.setattr(cli, "_has_module", lambda name: name != "gradio")
    monkeypatch.setattr(cli.shutil, "which", lambda name: "C:/Calibre/" + name if name == "ebook-meta" else None)

    result = runner.invoke(cli.app, ["doctor"])

    assert result.exit_code == 1
    assert "OK      pypinyin         required" in result.output
    assert "MISSING gradio           optional" in result.output
    assert "MISSING ebook-convert    required" in result.output
    assert "OK      ebook-meta       optional" in result.output
    assert "Setup suggestions:" in result.output
    assert "Install Calibre and add its install directory to PATH." in result.output
    assert 'python -m pip install "ebook2pinyin[web]"' in result.output
