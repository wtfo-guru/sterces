from sterces import cli


def test_group_add(cli_runner, gdbx: str, ppfn: str):
    """Test group add."""
    fruit = cli_runner.invoke(
        cli.cli,
        [
            "--db",
            gdbx,
            "--passphrase-file",
            ppfn,
            "group",
            "--add",
            "--path",
            "internet/email/gmail/qs5779",
        ],
    )
    assert fruit.exit_code == 0
    assert not fruit.exception
    assert (
        '[Group: "", Group: "internet", Group: "internet/email", Group: "internet/email/gmail", Group: "internet/email/gmail/qs5779"]'
        in fruit.output
    )
