import os
import pytest
import jsonpickle
import logging
from beeflow.client import bee_client
from beeflow.common.db import client_db
from requests.exceptions import ConnectionError
from pathlib import Path
import subprocess


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
    """Regression test check_short_id_collision for multiple matches."""
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
    "id_list, wf_id, exp_long_wf_id",
    [
        (
            [
                "acd96a4ece434649abee1622c80e39e1",
                "c34e865453cf43b1b3759c60c78c43c1",
                "8df4418a6d1b42f2bda87c7a07f2c00d",
                "a5554c4138294427a9eb0a9f89215cee",
                "e50d8669595a4b05b841bc7b5336c721",
            ],
            "c34e86",
            "c34e865453cf43b1b3759c60c78c43c1",
        ),
        (
            [
                "123456" + "ece434649abee1622c80e39e1",
                "123456" + "5453cf43b1b3759c60c78c43c1",
                "123456" + "8a6d1b42f2bda87c7a07f2c00d",
                "123456" + "4138294427a9eb0a9f89215cee",
                "123456" + "69595a4b05b841bc7b5336c721",
            ],
            "123456e",
            "123456ece434649abee1622c80e39e1",
        ),
    ],
)
def test_match_short_id(mocker, id_list, wf_id, exp_long_wf_id):
    """Regression test match_short_id."""
    workflow_list = [["", this_id] for this_id in id_list]
    mocker.patch("beeflow.client.bee_client.get_wf_list", return_value=workflow_list)
    long_wf_id = bee_client.match_short_id(wf_id)
    assert long_wf_id == exp_long_wf_id


@pytest.mark.parametrize(
    "id_list, wf_id, exception, match",
    [
        (
            ["acd96a4ece434649abee1622c80e39e1"] * 2,
            "acd96a",
            bee_client.ClientError,
            "provided workflow ID ambiguous",
        ),
        (
            ["acd96a4ece434649abee1622c80e39e1"],
            "abc123",
            bee_client.ClientError,
            "does not match any submitted workflows",
        ),
        (
            [],
            "",
            SystemExit,
            "There are currently no workflows.",
        ),
    ],
)
def test_match_sort_id_errors(mocker, id_list, wf_id, exception, match):
    """Regression match_sort_id errors."""
    workflow_list = [["", this_id] for this_id in id_list]
    mocker.patch("beeflow.client.bee_client.get_wf_list", return_value=workflow_list)
    with pytest.raises(exception, match=match):
        bee_client.match_short_id(wf_id)


@pytest.mark.parametrize(
    "exp_status",
    ["Running", "Archived", "FakeStatus"],
)
def test_get_wf_status(mocker, exp_status):
    """Regression test get_wf_status."""
    fake_resp = mocker.Mock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {"wf_status": exp_status}
    mock_conn = mocker.Mock()
    mock_conn.get.return_value = fake_resp
    mocker.patch("beeflow.client.bee_client._wfm_conn", return_value=mock_conn)
    # the wf_id is not used since we mock the request
    status = bee_client.get_wf_status("123456")
    assert status == exp_status


@pytest.mark.parametrize(
    "status_code, side_effect, exception, match",
    [
        (
            500,
            None,
            bee_client.ClientError,
            "Could not successfully query workflow manager",
        ),
        (200, ConnectionError(), bee_client.ClientError, "Could not reach WF Manager."),
    ],
)
def test_get_wf_status_errors(mocker, status_code, side_effect, exception, match):
    """Regression test get_wf_status errors."""
    fake_resp = mocker.Mock()
    fake_resp.status_code = status_code
    fake_resp.json.return_value = {"wf_status": "FakeStatus"}
    mock_conn = mocker.Mock()
    mock_conn.get.return_value = fake_resp
    mocker.patch(
        "beeflow.client.bee_client._wfm_conn",
        return_value=mock_conn,
        side_effect=side_effect,
    )
    with pytest.raises(exception, match=match):
        bee_client.get_wf_status("123456")


@pytest.mark.parametrize(
    "msg",
    ["msg1", "msg2"],
)
def test_start(mocker, capsys, msg):
    """Regression test start."""
    exp_msg = msg + "\n"
    fake_resp = mocker.Mock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {"msg": msg}
    mock_conn = mocker.Mock()
    mock_conn.post.return_value = fake_resp
    mocker.patch("beeflow.client.bee_client._wfm_conn", return_value=mock_conn)
    # the wf_id is not used since we mock the request
    bee_client.start("123456")
    cap = capsys.readouterr()
    print(cap.out)
    assert cap.out == exp_msg


@pytest.mark.parametrize(
    "status_code, side_effect, exception, match",
    [
        (200, ConnectionError(), bee_client.ClientError, "Could not reach WF Manager."),
        (
            400,
            None,
            bee_client.ClientError,
            "Could not start workflow. It may have already been started",
        ),
        (500, None, bee_client.ClientError, "Starting 123456 failed."),
    ],
)
def test_start_errors(mocker, status_code, side_effect, exception, match):
    """Regression test start errors."""
    fake_resp = mocker.Mock()
    fake_resp.status_code = status_code
    fake_resp.json.return_value = {"msg": ""}
    mock_conn = mocker.Mock()
    mock_conn.post.return_value = fake_resp
    mocker.patch(
        "beeflow.client.bee_client._wfm_conn",
        return_value=mock_conn,
        side_effect=side_effect,
    )
    with pytest.raises(exception, match=match):
        bee_client.start("123456")


def test_package(tmpdir, capsys):
    """Regression test package."""
    exp_out = "Package wf.tgz created successfully\n"
    wf_path = Path(str(tmpdir / "wf"))
    wf_path.mkdir()
    package_dest = Path(str(tmpdir / "dest"))
    package_dest.mkdir()
    exp_path = package_dest / "wf.tgz"
    with tmpdir.as_cwd():
        # make some file in the wf_path so something is tar'd
        open("filename.txt", "w").close()
        package_path = bee_client.package(wf_path, package_dest)
    cap = capsys.readouterr()
    assert cap.out == exp_out
    assert package_path == exp_path


@pytest.mark.parametrize(
    "isdir, return_code, exception, match",
    [
        (False, 0, bee_client.ClientError, "is not a valid directory"),
        (True, 1, bee_client.ClientError, "Package failed"),
    ],
)
def test_package_errors(mocker, tmpdir, isdir, return_code, exception, match):
    """Regression test package errors."""
    wf_path = Path(str(tmpdir / "wf"))
    package_dest = Path(str(tmpdir))
    mocker.patch("os.path.isdir", return_value=isdir)
    sp_run = mocker.patch("subprocess.run")
    sp_run.return_code = return_code
    with tmpdir.as_cwd(), pytest.raises(exception, match=match):
        package_path = bee_client.package(wf_path, package_dest)


@pytest.mark.parametrize(
    "wf_status, input_val, status_code, side_effect, exception, match, exp_out",
    [
        (
            "Cancelled",
            "yes",
            202,
            None,
            SystemExit,
            "",
            """Workflow Status is Cancelled
Workflow removed!
""",
        ),
        (
            "Archived/Failed",
            "n",
            0,
            None,
            SystemExit,
            "Workflow not removed",
            "Workflow Status is Archived/Failed\n",
        ),
        (
            "Paused",
            "y",
            0,
            None,
            bee_client.ClientError,
            "WF Manager could not remove workflow",
            "Workflow Status is Paused\n",
        ),
        (
            "Archived",
            "y",
            202,
            ConnectionError(),
            bee_client.ClientError,
            "Could not reach WF Manager",
            "Workflow Status is Archived\n",
        ),
        (
            "Running",
            "",
            0,
            None,
            SystemExit,
            "",
            """Workflow Status is Running
123456 may still be running.
The workflow must be cancelled before attempting removal.
""",
        ),
    ],
)
def test_remove(
    mocker,
    capsys,
    wf_status,
    input_val,
    status_code,
    side_effect,
    exception,
    match,
    exp_out,
):
    """Regression test remove."""
    mocker.patch("beeflow.client.bee_client.get_wf_status", return_value=wf_status)
    mocker.patch("builtins.input", return_value=input_val)
    fake_resp = mocker.Mock()
    fake_resp.status_code = status_code
    fake_resp.text = "fake text"
    mock_conn = mocker.Mock()
    mock_conn.delete.return_value = fake_resp
    mocker.patch(
        "beeflow.client.bee_client._wfm_conn",
        return_value=mock_conn,
        side_effect=side_effect,
    )
    with pytest.raises(exception, match=match):
        bee_client.remove("123456")
    cap = capsys.readouterr()
    assert cap.out == exp_out


def test_unpackage(tmp_path):
    """Regression test unpackage."""
    # make a dummy tar to use
    wf_name = "my_wf"
    test_dir = tmp_path / wf_name
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("test file")
    package_path = tmp_path / (wf_name + ".tgz")
    subprocess.run(
        ["tar", "czf", str(package_path), "-C", str(tmp_path), wf_name], check=True
    )
    dest_path = tmp_path / "dest"
    dest_path.mkdir()
    exp_path = dest_path / wf_name
    wf_path = bee_client.unpackage(package_path, dest_path)
    assert wf_path == exp_path


@pytest.mark.parametrize(
    "extension, return_code, exception, match",
    [
        (".png", 0, bee_client.ClientError, "Invalid package name"),
        (".tgz", 2, bee_client.ClientError, "Unpackage failed"),
    ],
)
def test_unpackage_errors(tmp_path, mocker, extension, return_code, exception, match):
    """Regression test unpackage errors."""
    wf_name = "my_wf"
    test_dir = tmp_path / wf_name
    test_dir.mkdir()
    (test_dir / "file.txt").write_text("test file")
    package_path = tmp_path / (wf_name + extension)
    dest_path = tmp_path / "dest"
    dest_path.mkdir()
    return_value = mocker.Mock()
    return_value.return_code = return_code
    mocker.patch("subprocess.run", return_value=return_value)
    with pytest.raises(exception, match=match):
        wf_path = bee_client.unpackage(package_path, dest_path)


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


@pytest.mark.parametrize(
    "wf_status, exp_out",
    [
        (
            "Running",
            """Running
cat--Running
grep--Pending
""",
        ),
        (
            "No Start",
            """No Start
cat
grep
""",
        ),
    ],
)
def test_query(mocker, capsys, wf_status, exp_out):
    """Regression test query."""
    fake_resp = mocker.Mock()
    fake_resp.status_code = 200
    fake_resp.json.return_value = {
        "tasks_status": [("", "cat", "Running"), ("", "grep", "Pending")],
        "wf_status": wf_status,
    }
    mock_conn = mocker.Mock()
    mock_conn.get.return_value = fake_resp
    mocker.patch("beeflow.client.bee_client._wfm_conn", return_value=mock_conn)
    bee_client.query(123456)
    cap = capsys.readouterr()
    assert cap.out == exp_out


def test_pause(mocker):
    """Regression test pause."""
    fake_resp = mocker.Mock()
    fake_resp.status_code = 200
    mock_conn = mocker.Mock()
    mock_conn.patch.return_value = fake_resp
    mocker.patch("beeflow.client.bee_client._wfm_conn", return_value=mock_conn)
    bee_client.pause(123456)
    mock_conn.patch.assert_called_once_with(
        bee_client._resource(123456), json={"option": "pause"}, timeout=60
    )


def test_resume(mocker):
    """Regression test resume."""
    fake_resp = mocker.Mock()
    fake_resp.status_code = 200
    mock_conn = mocker.Mock()
    mock_conn.patch.return_value = fake_resp
    mocker.patch("beeflow.client.bee_client._wfm_conn", return_value=mock_conn)
    bee_client.resume(123456)
    mock_conn.patch.assert_called_once_with(
        bee_client._resource(123456),
        json={"wf_id": 123456, "option": "resume"},
        timeout=60,
    )


@pytest.mark.parametrize(
    "wf_status, exp_out",
    [
        ("Running", "Workflow cancelled!\n"),
        ("Paused", "Workflow cancelled!\n"),
        ("No Start", "Workflow cancelled!\n"),
        ("Intializing", "Workflow is Intializing, try cancel later.\n"),
        ("Bad Status", "Workflow is Bad Status cannot cancel.\n"),
    ],
)
def test_cancel(mocker, capsys, wf_status, exp_out):
    """Regression test cancel."""
    fake_resp = mocker.Mock()
    fake_resp.status_code = 202
    mock_conn = mocker.Mock()
    mock_conn.delete.return_value = fake_resp
    mocker.patch("beeflow.client.bee_client._wfm_conn", return_value=mock_conn)
    mocker.patch("beeflow.client.bee_client.get_wf_status", return_value=wf_status)
    bee_client.cancel(123456)
    cap = capsys.readouterr()
    assert cap.out == exp_out


@pytest.mark.parametrize(
    "function, status_code, side_effect, exception, match",
    [
        (
            bee_client.query,
            200,
            ConnectionError(),
            bee_client.ClientError,
            "Could not reach WF Manager",
        ),
        (
            bee_client.pause,
            200,
            ConnectionError(),
            bee_client.ClientError,
            "Could not reach WF Manager",
        ),
        (
            bee_client.resume,
            200,
            ConnectionError(),
            bee_client.ClientError,
            "Could not reach WF Manager",
        ),
        (
            bee_client.cancel,
            200,
            ConnectionError(),
            bee_client.ClientError,
            "Could not reach WF Manager",
        ),
        (
            bee_client.copy,
            200,
            ConnectionError(),
            bee_client.ClientError,
            "Could not reach WF Manager",
        ),
        (
            bee_client.query,
            500,
            None,
            bee_client.ClientError,
            "Could not successfully query workflow manager",
        ),
        (
            bee_client.pause,
            500,
            None,
            bee_client.ClientError,
            "WF Manager could not pause workflow",
        ),
        (
            bee_client.resume,
            500,
            None,
            bee_client.ClientError,
            "WF Manager could not resume workflow",
        ),
        (
            bee_client.cancel,
            500,
            None,
            bee_client.ClientError,
            "WF Manager could not cancel workflow",
        ),
        (
            bee_client.copy,
            500,
            None,
            bee_client.ClientError,
            "WF Manager could not copy workflow",
        ),
    ],
)
def test_simple_req_errors(
    mocker, function, status_code, side_effect, exception, match
):
    """Regression test errors for functions that accept wf_id and error on ConnectionError, bad status code."""
    fake_resp = mocker.Mock()
    fake_resp.status_code = status_code
    mock_conn = mocker.Mock()
    mock_conn.patch.return_value = fake_resp
    mock_conn.delete.return_value = fake_resp
    mocker.patch(
        "beeflow.client.bee_client._wfm_conn",
        return_value=mock_conn,
        side_effect=side_effect,
    )
    mocker.patch("beeflow.client.bee_client.get_wf_status", return_value="Running")
    with pytest.raises(exception, match=match):
        function(123456)
