import os
import pytest
import jsonpickle
import logging
from beeflow.client import bee_client
from beeflow.common.db import client_db
from requests.exceptions import ConnectionError


@pytest.fixture(autouse=True)
def reset_short_id_len():
    original = bee_client.short_id_len
    yield
    bee_client.short_id_len = original


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
    "msg, include_caller, exp_err",
    [
        ("test msg", True, "Test_error_exit: test msg"),
        ("test msg", False, "test msg"),
    ],
)
def test_error_exit(mocker, msg, include_caller, exp_err):
    """Regression test error_exit."""
    mocker.patch("beeflow.client.bee_client._INTERACTIVE", False)
    with pytest.raises(bee_client.ClientError, match=exp_err):
        bee_client.error_exit(msg, include_caller)


@pytest.mark.parametrize(
    "msg, include_caller, exp_err",
    [
        ("test msg", True, "Test_error_exit_int: test msg\n"),
        ("test msg", False, "test msg\n"),
    ],
)
def test_error_exit_int(capsys, mocker, msg, include_caller, exp_err):
    """Regression test error_exit for interactive."""
    mocker.patch("beeflow.client.bee_client._INTERACTIVE", True)
    sys_exit = mocker.patch("sys.exit")
    bee_client.error_exit(msg, include_caller)
    cap = capsys.readouterr()
    sys_exit.assert_called_once_with(1)
    assert cap.err == exp_err


@pytest.mark.parametrize(
    "status_code, key, exp_ret, exp_file",
    [
        (200, "", True, ""),
        (500, "some key", True, ""),
        (500, "error", False, "args: -f my_file.p\n"),
    ],
)
def test_error_handler(tmpdir, mocker, status_code, key, exp_ret, exp_file):
    error_exit = mocker.patch("beeflow.client.bee_client.error_exit")
    mocker.patch("time.time", return_value=1)
    mocker.patch("sys.argv", ["-f", "my_file.p"])
    fake_resp = mocker.Mock()
    fake_resp.status_code = status_code
    fake_resp.json.return_value = {key: ""}
    with tmpdir.as_cwd():
        ret = bee_client.error_handler(fake_resp)
        if exp_ret:
            # it just returns the response we gave
            assert ret == fake_resp
        else:
            assert ret == None
        if exp_file:
            assert os.path.isfile("bee-error-1.log")
            with open("bee-error-1.log", "r", encoding="utf-8") as f:
                file_cont = f.read()
            assert file_cont == exp_file


def test_wfm_conn(mocker):
    """Regression test _wfm_conn."""
    Connection = mocker.patch("beeflow.client.bee_client.Connection")
    mocker.patch("beeflow.common.paths.wfm_socket", return_value="/fake/path/")
    bee_client._wfm_conn()
    Connection.assert_called_once_with(
        "/fake/path/", error_handler=bee_client.error_handler
    )


def test_resource():
    """Regression test _resource."""
    ret = bee_client._resource(tag="tag")
    assert ret == "bee_wfm/v1/jobs/tag"


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


def test_get_wf_list_except(mocker):
    """Regression test get_wf_list when ConnectionError"""
    mock_conn = mocker.Mock()
    mock_conn.get.side_effect = ConnectionError()
    mocker.patch("beeflow.client.bee_client.get_hostname", return_value="test_hostname")
    mocker.patch("beeflow.client.bee_client._wfm_conn", return_value=mock_conn)
    with pytest.raises(
        bee_client.ClientError, match="Get_wf_list: Could not reach WF Manager."
    ):
        result = bee_client.get_wf_list()


def test_get_wf_list_except_exit(mocker):
    """Regression test get_wf_list when ConnectionError and no hostname."""
    warn = mocker.patch("beeflow.client.bee_client.warn")
    mock_conn = mocker.Mock()
    mock_conn.get.side_effect = ConnectionError()
    mocker.patch("beeflow.client.bee_client.get_hostname", return_value="")
    mocker.patch("beeflow.client.bee_client._wfm_conn", return_value=mock_conn)
    with pytest.raises(SystemExit):
        bee_client.get_wf_list()
    warn.assert_called_once_with("beeflow has not been started!")


def test_get_wf_list_500(mocker):
    """Regression test get_wf_list with error code."""
    fake_resp = mocker.Mock()
    fake_resp.status_code = 500
    mock_conn = mocker.Mock()
    mock_conn.get.return_value = fake_resp
    mocker.patch("beeflow.client.bee_client._wfm_conn", return_value=mock_conn)
    with pytest.raises(
        bee_client.ClientError,
        match="Get_wf_list: WF Manager did not return workflow list",
    ):
        result = bee_client.get_wf_list()


@pytest.mark.parametrize(
    "id_list, exp_id_len",
    [
        (
            [
                "acd96a4ece434649abee1622c80e39e1",
                "c34e865453cf43b1b3759c60c78c43c1",
                "8df4418a6d1b42f2bda87c7a07f2c00d",
                "a5554c4138294427a9eb0a9f89215cee",
                "e50d8669595a4b05b841bc7b5336c721",
            ],
            6,
        ),
        (
            [
                "123456" + "ece434649abee1622c80e39e1",
                "123456" + "5453cf43b1b3759c60c78c43c1",
                "123456" + "8a6d1b42f2bda87c7a07f2c00d",
                "123456" + "4138294427a9eb0a9f89215cee",
                "123456" + "69595a4b05b841bc7b5336c721",
            ],
            7,
        ),
    ],
)
def test_check_short_id_collision(mocker, id_list, exp_id_len):
    """Regression test check_short_id_collision."""
    workflow_list = [["", this_id] for this_id in id_list]
    mocker.patch("beeflow.client.bee_client.get_wf_list", return_value=workflow_list)
    bee_client.check_short_id_collision()
    assert bee_client.short_id_len == exp_id_len


def test_check_short_id_collision_runtime(mocker):
    workflow_list = [["", "acd96a4ece434649abee1622c80e39e1"] for i in range(3)]
    mocker.patch("beeflow.client.bee_client.get_wf_list", return_value=workflow_list)
    with pytest.raises(
        RuntimeError, match="collision detected between two full workflow IDs"
    ):
        bee_client.check_short_id_collision()


def test_check_short_id_collision_no_jobs(mocker, capsys):
    """Regression test check_short_id_collision when no jobs."""
    mocker.patch("beeflow.client.bee_client.get_wf_list", return_value=[])
    bee_client.check_short_id_collision()
    cap = capsys.readouterr()
    assert cap.out == "There are currently no jobs.\n"


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
