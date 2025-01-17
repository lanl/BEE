"""Charliecloud driver tests."""
import pytest
from beeflow.common.crt.charliecloud_driver import CharliecloudDriver as crt_driver
from beeflow.common.wf_data import Task, Requirement


@pytest.mark.parametrize(
    "use_container, pre_commands_exp, main_command_exp, post_commands_exp",
    [
        ("cont.sqfs", "", "ch-run cont.sqfs env --cd  -b : -- default", ""),
        (
            "cont.tar.gz",
            "mkdir -p env one-per-node ch-convert -i tar -o dir cont.tar.gz env/cont one-per-node",
            "ch-run env/cont env --cd  -b : -- default",
            "rm -rf env/cont one-per-node",
        ),
    ],
)
def test_run_text_use_container(
    mocker, tmpdir, use_container, pre_commands_exp, main_command_exp, post_commands_exp
):
    """Test run_text with different useContainer DockerRequirements."""
    tmpdir_str = str(tmpdir)
    mocker.patch("beeflow.common.config_driver.BeeConfig.get", return_value="env")
    mocker.patch(
        "beeflow.common.config_driver.BeeConfig.resolve_path", return_value=tmpdir_str
    )
    mocker.patch("os.getenv", return_value=str(tmpdir))
    requirements = [
        Requirement(
            "DockerRequirement",
            {
                "beeflow:containerName": None,
                "beeflow:bindMounts": None,
                "beeflow:copyContainer": None,
                "dockerPull": None,
                "beeflow:useContainer": use_container,
            },
        )
    ]
    task = Task(
        name="",
        base_command="",
        hints=[],
        requirements=requirements,
        inputs=[],
        outputs=[],
        stdout="",
        stderr="",
        workflow_id="",
        workdir=tmpdir,
    )
    driver = crt_driver()
    res = driver.run_text(task)
    assert res.env_code.count(tmpdir_str) == 1
    # simplify results for easier comparison
    env_code = res.env_code.replace(tmpdir_str, "").replace("\n", " ")
    pre_commands = " ".join(
        [f'{" ".join(com.args)} {com.type}' for com in res.pre_commands]
    ).replace(tmpdir_str, "")
    main_command = f'{" ".join(res.main_command.args)} {res.main_command.type}'
    assert main_command.count(tmpdir_str) == 3
    main_command = main_command.replace(tmpdir_str, "")
    post_commands = " ".join(
        [f'{" ".join(com.args)} {com.type}' for com in res.post_commands]
    )
    assert env_code == "env cd  "
    assert pre_commands == pre_commands_exp
    assert main_command == main_command_exp
    assert post_commands == post_commands_exp
