import re

from typer.testing import CliRunner

from harvestradar.cli import app

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _help(*args: str) -> str:
    """Plain help text: CI terminals get coloured, boxed output, so colour codes are removed before checking."""
    out = CliRunner().invoke(app, [*args, "--help"], env={"NO_COLOR": "1", "TERM": "dumb", "COLUMNS": "200"}).output
    return ANSI.sub("", out)


def test_cli_lists_groups():
    out = _help()
    for g in ["data", "regions", "features", "model", "index", "report", "demo", "all", "update"]:
        assert g in out


def test_report_email_help():
    assert "--week" in _help("report", "email")


def test_update_help():
    out = _help("update")
    assert "--date" in out and "--deterministic" in out  # long option names are cut at narrow widths
