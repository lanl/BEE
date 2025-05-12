import pytest
import jsonpickle
import logging
from beeflow.client import bee_client
from beeflow.common.db import client_db


def test_clienterror():
    """Regression test ClientError."""
    msg = "test_msg"
    with pytest.raises(bee_client.ClientError, match=msg):
        raise bee_client.ClientError(msg)


def test_warn(capsys):
    """Regression test warn."""
    bee_client.warn("foo", "bar")
    cap = capsys.readouterr()
    assert cap.err == "foo bar\n"


def test_db_path(mocker):
    """Regression test db_path."""
    mocker.patch(
        "beeflow.common.config_driver.BeeConfig.get", return_value="/fake/path/"
    )
    path = bee_client.db_path()
    assert path == "/fake/path/client.db"


def test_setup_hostname(mocker):
    """Regression test setup_hostname."""
    db = mocker.Mock()
    test_path = "/fake/path/client.db"
    mocker.patch("beeflow.client.bee_client.db_path", return_value=test_path)
    connect_db = mocker.patch("beeflow.common.db.bdb.connect_db", return_value=db)
    start_hn = "test_hostname"
    bee_client.setup_hostname(start_hn)
    connect_db.assert_called_once_with(client_db, test_path)
    db.info.set_hostname.assert_called_once_with(start_hn)


def test_get_hostname(mocker):
    """Regression test get_hostname."""
    db = mocker.Mock()
    exp_hn = "fake_hostname"
    db.info.get_hostname.return_value = exp_hn
    test_path = "/fake/path/client.db"
    mocker.patch("beeflow.client.bee_client.db_path", return_value=test_path)
    connect_db = mocker.patch("beeflow.common.db.bdb.connect_db", return_value=db)
    curr_hn = bee_client.get_hostname()
    connect_db.assert_called_once_with(client_db, test_path)
    db.info.get_hostname.assert_called_once()
    assert curr_hn == exp_hn


def test_set_backend_statue(mocker):
    """Regression test set_backend_status."""
    db = mocker.Mock()
    test_path = "/fake/path/client.db"
    mocker.patch("beeflow.client.bee_client.db_path", return_value=test_path)
    connect_db = mocker.patch("beeflow.common.db.bdb.connect_db", return_value=db)
    new_status = "test_status"
    bee_client.set_backend_status(new_status)
    connect_db.assert_called_once_with(client_db, test_path)
    db.info.set_backend_status.assert_called_once_with(new_status)


def test_check_backend_statue(mocker):
    """Regression test set_backend_status."""
    db = mocker.Mock()
    exp_status = "test_status"
    db.info.get_backend_status.return_value = exp_status
    test_path = "/fake/path/client.db"
    mocker.patch("beeflow.client.bee_client.db_path", return_value=test_path)
    connect_db = mocker.patch("beeflow.common.db.bdb.connect_db", return_value=db)
    status = bee_client.check_backend_status()
    connect_db.assert_called_once_with(client_db, test_path)
    db.info.get_backend_status.assert_called_once()
    assert status == exp_status


def test_reset_client_db(mocker):
    """Regression test reset_client_db."""
    setup_hostname = mocker.patch("beeflow.client.bee_client.setup_hostname")
    set_backend_status = mocker.patch("beeflow.client.bee_client.set_backend_status")
    bee_client.reset_client_db()
    setup_hostname.assert_called_once_with("")
    set_backend_status.assert_called_once_with("")


@pytest.mark.parametrize(
    "curr_alloc, command, warns, did_exit, did_reset_client_db, did_setup_hostname",
    [
        (
            True,
            True,
            [
                'beeflow was started on "bad_hostname" and you are trying to run a command on "test_hostname".'
            ],
            True,
            False,
            False,
        ),
        (
            True,
            False,
            [
                'beeflow was started on compute node "test_hostname" and it is still running. '
            ],
            True,
            False,
            False,
        ),
        (False, True, ["beeflow has not been started!"], True, False, False),
        (
            False,
            False,
            [
                "beeflow was started on a compute node (no longer owned by user) and not stopped correctly. ",
                "Resetting client database.",
            ],
            False,
            True,
            True,
        ),
    ],
)
def test_check_backend_jobs(
    mocker,
    curr_alloc,
    command,
    warns,
    did_exit,
    did_reset_client_db,
    did_setup_hostname,
):
    start_hn = "test_hostname"
    user_name = "test_user"
    resp = mocker.Mock()
    get_hostname = mocker.patch("beeflow.client.bee_client.get_hostname")
    # command is only true if this is true
    if command:
        get_hostname_return_value = "bad_hostname"
    else:
        get_hostname_return_value = start_hn
    get_hostname.return_value = get_hostname_return_value
    if curr_alloc:
        resp.stdout.splitlines.return_value = get_hostname_return_value
    else:
        resp.stdout.splitlines.return_value = "not_curr_alloc_hostname"
    mocker.patch("getpass.getuser", return_value=user_name)
    sp_run = mocker.patch("subprocess.run", return_value=resp)
    warn = mocker.patch("beeflow.client.bee_client.warn")
    sys_exit = mocker.patch("sys.exit")
    reset_client_db = mocker.patch("beeflow.client.bee_client.reset_client_db")
    setup_hostname = mocker.patch("beeflow.client.bee_client.setup_hostname")
    bee_client.check_backend_jobs(start_hn, command)
    exp_warn_calls = [mocker.call(arg) for arg in warns]
    assert warn.call_args_list == exp_warn_calls
    if did_exit:
        sys_exit.assert_called_once_with(1)
    if did_reset_client_db:
        reset_client_db.assert_called_once_with()
    if did_setup_hostname:
        setup_hostname.assert_called_once_with(start_hn)


@pytest.mark.parametrize(
    "hostname, status, did_warn, did_exit, did_check_backend_jobs",
    [
        ("bad_hostname", "", True, True, False),
        ("bad_hostname", "true", False, False, True),
        # these cases shouldn't do anything
        ("test_hostname", "", False, False, False),
        ("", "", False, False, False),
    ],
)
def test_check_db_flags(
    mocker, hostname, status, did_warn, did_exit, did_check_backend_jobs
):
    """Regression test check_db_flags."""
    start_hn = "test_hostname"
    mocker.patch("beeflow.client.bee_client.get_hostname", return_value=hostname)
    mocker.patch("beeflow.client.bee_client.check_backend_status", return_value=status)
    check_backend_jobs = mocker.patch("beeflow.client.bee_client.check_backend_jobs")
    warn = mocker.patch("beeflow.client.bee_client.warn")
    sys_exit = mocker.patch("sys.exit")
    bee_client.check_db_flags(start_hn)
    if did_warn:
        warn.assert_called_once_with(
            'Error: beeflow is already running on "bad_hostname".'
        )
    if did_exit:
        sys_exit.assert_called_once_with(1)
    if did_check_backend_jobs:
        check_backend_jobs.assert_called_once_with(start_hn)


@pytest.mark.parametrize(
    "hostname, status, this_warn, did_exit, did_check_backend_jobs",
    [
        (
            "bad_hostname",
            "",
            'beeflow was started on "bad_hostname" and you are trying to run a command on "test_hostname".',
            True,
            False,
        ),
        ("bad_hostname", "true", None, False, True),
        ("", "", "beeflow has not been started!", True, False),
        # this case shouldn't do anything
        ("test_hostname", "", None, False, False),
    ],
)
def test_check_hostname(
    mocker, hostname, status, this_warn, did_exit, did_check_backend_jobs
):
    """Regression test check_hostname."""
    curr_hn = "test_hostname"
    mocker.patch("beeflow.client.bee_client.get_hostname", return_value=hostname)
    mocker.patch("beeflow.client.bee_client.check_backend_status", return_value=status)
    check_backend_jobs = mocker.patch("beeflow.client.bee_client.check_backend_jobs")
    warn = mocker.patch("beeflow.client.bee_client.warn")
    sys_exit = mocker.patch("sys.exit")
    bee_client.check_hostname(curr_hn)
    if this_warn is not None:
        warn.assert_called_once_with(this_warn)
    if did_exit:
        sys_exit.assert_called_once_with(1)
    if did_check_backend_jobs:
        check_backend_jobs.assert_called_once_with(curr_hn, command=True)


@pytest.mark.parametrize(
    "input_data",
    [([["checkpoint_test", "8df4418a6d1b42f2bda87c7a07f2c00d", "Archived"]])],
)
def test_get_wf_list(mocker, input_data):
    """Regression test get_wf_list."""
    encoded_data = jsonpickle.encode(input_data)
    fake_resp = mocker.Mock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {"workflow_list": encoded_data}
    mock_conn = mocker.Mock()
    mock_conn.get.return_value = fake_resp
    mocker.patch("beeflow.client.bee_client._wfm_conn", return_value=mock_conn)
    result = bee_client.get_wf_list()
    # this should just decode back to the data we gave it
    assert result == input_data


@pytest.mark.parametrize(
    "mock_in, exp_out",
    [
        (
            [
                [
                    "checkpoint_test",
                    "acd96a4ece434649abee1622c80e39e1",
                    "Archived/Failed",
                ],
                [
                    "checkpoint_test",
                    "c34e865453cf43b1b3759c60c78c43c1",
                    "Archived/Failed",
                ],
                ["checkpoint_test", "8df4418a6d1b42f2bda87c7a07f2c00d", "Archived"],
                ["test", "a5554c4138294427a9eb0a9f89215cee", "Archived/Failed"],
                ["test", "e50d8669595a4b05b841bc7b5336c721", "Archived"],
            ],
            """Name	ID	Status
checkpoint_test	acd96a	Archived/Failed
checkpoint_test	c34e86	Archived/Failed
checkpoint_test	8df441	Archived
test	a5554c	Archived/Failed
test	e50d86	Archived
""",
        ),
        ([], "There are currently no workflows.\n"),
    ],
)
def test_list_workflows(
    capsys,
    caplog,
    mocker,
    mock_in,
    exp_out,
):
    """Regression test list_workflows."""
    mocker.patch("beeflow.client.bee_client.get_wf_list", return_value=mock_in)
    bee_client.list_workflows()
    cap = capsys.readouterr()
    assert cap.out == exp_out
