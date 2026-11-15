from typer.testing import CliRunner

from harvestradar.cli import app


def test_cli_lists_groups():
    out = CliRunner().invoke(app, ["--help"]).output
    for g in ["data", "regions", "features", "model", "index", "report", "demo", "all"]:
        assert g in out


def test_report_email_help():
    out = CliRunner().invoke(app, ["report", "email", "--help"]).output
    assert "--week" in out
