"""Tests for wf_utils module."""

import pytest
from beeflow.wf_manager.resources import wf_utils

from beeflow.tests.mocks import MockWFI


@pytest.mark.parametrize(
    "which_return, no_dag_flag, expected_dot_avail",
    [
        ("/usr/bin/dot", True, True),
        ("/usr/bin/dot", False, True),
        (None, True, False),
        (None, False, False),
    ],
)
def test_export_dag(mocker, which_return, no_dag_flag, expected_dot_avail):
    """Regression test export_dag based on graphviz availability."""
    wf_id = "abc123"
    output_dir = "/path/to/out"
    graphmls_dir = "/path/to/gmls"
    workflow_dir = "/path/to/wfdir"
    
    mock_wfi = mocker.MagicMock()
    mocker.patch('beeflow.wf_manager.resources.wf_utils.get_workflow_interface', return_value=mock_wfi)
    mocker.patch('beeflow.common.wf_interface.WorkflowInterface.export_graphml')
    mocker.patch('beeflow.wf_manager.resources.wf_utils.shutil.which',
                 return_value=which_return)
    mock_update = mocker.patch('beeflow.wf_manager.resources.wf_utils.update_graphml')
    mock_viz = mocker.patch('beeflow.wf_manager.resources.wf_utils.generate_viz')

    result =  wf_utils.export_dag(
        wf_id,
        output_dir,
        graphmls_dir,
        no_dag_flag,
        workflow_dir
    )

    # always export the GraphML first
    mock_wfi.export_graphml.assert_called_once_with()

    # return value is bool(shutil.which)
    assert result is expected_dot_avail

    if expected_dot_avail:
        mock_update.assert_called_once_with(wf_id, graphmls_dir)
        mock_viz.assert_called_once_with(
            wf_id, output_dir, graphmls_dir, no_dag_flag, workflow_dir
        )
    else:
        mock_update.assert_called_once_with(
            wf_id, graphmls_dir, output_dir, no_dag_flag
        )
        mock_viz.assert_not_called()





