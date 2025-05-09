import pytest
from beeflow.client import bee_client


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
