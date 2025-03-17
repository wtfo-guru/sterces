import testfixtures

from sterces import cli

HELP = """Usage: cli store [OPTIONS]

  Add or update an entry.

Options:
  -e, --expires TEXT   specify expire date/time
  -n, --notes TEXT     specify notes
  -o, --otp TEXT       specify notes
  -p, --password TEXT  specify password
  -P, --path TEXT      specify path of entry
  -T, --tags TEXT      specify tags
  -u, --username TEXT  specify username
  --url TEXT           specify url
  -h, --help           Show this message and exit.
"""

def test_store_help(cli_runner) -> None:
    test_result = cli_runner.invoke(cli.cli, ["store", "-h"])  # verifies the short context
    assert test_result.exit_code == 0
    assert not test_result.exception
    testfixtures.compare(HELP, test_result.output)
