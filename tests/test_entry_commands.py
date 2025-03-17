import testfixtures

from sterces import cli

EG_HELP = """Usage: cli entry [OPTIONS] COMMAND [ARGS]...

  Action group for entries.

Options:
  -h, --help  Show this message and exit.

Commands:
  add     Add or update an entry.
  dump    Dump specified entry or all entries if path not specified.
  remove  Remove specified entry.
  show    Show specified entry or all entries if path not specified.
  update  Update specified attributes of entry.
"""

ADD_HELP = """Usage: cli entry add [OPTIONS]

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


def test_entry_group_help(cli_runner) -> None:
    test_result = cli_runner.invoke(
        cli.cli, ["entry", "-h"]
    )  # verifies the short context
    assert test_result.exit_code == 0
    assert not test_result.exception
    testfixtures.compare(EG_HELP, test_result.output)
