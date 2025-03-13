from sterces import cli
from sterces.constants import VERSION


def test_cli_help(cli_runner):
    """Test help."""
    fruit = cli_runner.invoke(cli.cli)
    assert fruit.exit_code == 0
    assert not fruit.exception
    assert "Command interface for a KeePass database." in fruit.output


def test_cli_version(cli_runner):
    """Test help."""
    fruit = cli_runner.invoke(cli.cli, ["--version"])
    assert fruit.exit_code == 0
    assert not fruit.exception
    assert fruit.output.strip() == "cli, version {0}".format(VERSION)
