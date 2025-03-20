# import testfixtures

from pykeepass.pykeepass import PyKeePass
from sterces.constants import ADD, VERSION


def test_db_version(db: PyKeePass):
    assert db.version == VERSION


def test_group_add(db: PyKeePass, capsys):
    """Test group add."""
    db.group("/internet/email/gmail/qs5779/", ADD, quiet=False)
    out, err = capsys.readouterr()
    assert (
        '[Group: "", Group: "internet", Group: "internet/email", Group: "internet/email/gmail", Group: "internet/email/gmail/qs5779"]'
        in out
    )


# def test_group_remove(cli_runner, gdbx: str, ppfn: str):
#     """Test group remove."""
#     fruit = cli_runner.invoke(
#         cli.cli,
#         [
#             "--db",
#             gdbx,
#             "--passphrase-file",
#             ppfn,
#             "--no-warn",
#             "group",
#             "remove",
#             "--path",
#             "/internet",
#         ],
#     )
#     assert fruit.exit_code == 0
#     assert not fruit.exception
#     assert '[Group: ""]' in fruit.output


# def test_entry_group_help(cli_runner) -> None:
#     test_result = cli_runner.invoke(
#         cli.cli, ["entry", "-h"]
#     )  # verifies the short context
#     assert test_result.exit_code == 0
#     assert not test_result.exception
#     testfixtures.compare(EG_HELP, test_result.output)


# def test_entry_add(cli_runner, sdbx: str, ppfn: str, expiry: str):
#     """Test group add."""
#     cmd_args = base_args_path(sdbx, ppfn, "add", ENTRY_TEST_UNO)
#     cmd_args.extend(["-p", "passw0rd", "--expires", expiry])
#     fruit = cli_runner.invoke(cli.cli, cmd_args)
#     assert fruit.exit_code == 0
#     assert not fruit.exception
#     dt = str_to_date(expiry).astimezone(timezone.utc)  # type: ignore [union-attr]
#     md = dt.strftime("%Y-%m-%d %H:%M:%S")
#     match: str = (
#         "'path': ['test', 'test1'], 'title': 'test1', 'username': 'undef', 'password': '********', 'expiry': '{0}'".format(
#             md
#         )
#     )
#     assert match in fruit.output


# def test_entry_add_dup(cli_runner, sdbx: str, ppfn: str, expiry: str):
#     """Test group add."""
#     cmd_args = base_args_path(sdbx, ppfn, "add", ENTRY_TEST_UNO)
#     cmd_args.extend(["-p", "passw0rd", "--expires", expiry])
#     fruit = cli_runner.invoke(cli.cli, cmd_args)
#     assert fruit.exit_code != 0
#     assert "Entry /test/test1 already exists" in fruit.output


# def test_entry_update_username(cli_runner, sdbx: str, ppfn: str, expiry: str):
#     """Test group add."""
#     cmd_args = base_args_path(sdbx, ppfn, "update", ENTRY_TEST_UNO)
#     cmd_args.extend(["-a", "username", "-u", "joeblow"])
#     fruit = cli_runner.invoke(cli.cli, cmd_args)
#     assert fruit.exit_code == 0
#     assert not fruit.exception
#     dt = str_to_date(expiry).astimezone(timezone.utc)  # type: ignore [union-attr]
#     md = dt.strftime("%Y-%m-%d %H:%M:%S")
#     match: str = (
#         "'path': ['test', 'test1'], 'title': 'test1', 'username': 'joeblow', 'password': '********', 'expiry': '{0}'".format(
#             md
#         )
#     )
#     assert match in fruit.output


# def test_entry_show_one(cli_runner, sdbx: str, ppfn: str, expiry: str):
#     """Test group add."""
#     cmd_args = base_args(sdbx, ppfn, "show")
#     fruit = cli_runner.invoke(cli.cli, cmd_args)
#     assert fruit.exit_code == 0
#     assert not fruit.exception
#     dt = str_to_date(expiry).astimezone(timezone.utc)  # type: ignore [union-attr]
#     md = dt.strftime("%Y-%m-%d %H:%M:%S")
#     match: str = (
#         "'path': ['test', 'test1'], 'title': 'test1', 'username': 'joeblow', 'password': '********', 'expiry': '{0}'".format(
#             md
#         )
#     )
#     assert match in fruit.output


# def test_entry_remove(cli_runner, sdbx: str, ppfn: str):
#     """Test group add."""
#     cmd_args = base_args_path(sdbx, ppfn, "remove", ENTRY_TEST_UNO)
#     fruit = cli_runner.invoke(cli.cli, cmd_args)
#     assert fruit.exit_code == 0
#     assert not fruit.exception
#     match = "Entry {0} has been removed".format(ENTRY_TEST_UNO)
#     assert match in fruit.output


# def test_entry_show_none(cli_runner, sdbx: str, ppfn: str, expiry: str):
#     """Test group add."""
#     cmd_args = base_args(sdbx, ppfn, "show")
#     fruit = cli_runner.invoke(cli.cli, cmd_args)
#     assert fruit.exit_code == 0
#     assert not fruit.exception
#     assert "No entries found" in fruit.output
