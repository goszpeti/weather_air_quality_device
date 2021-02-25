import os
import sys
from pathlib import Path
import piweather.base.logger
from piweather import config
import pytest


class PathSetup():
    def __init__(self):
        self.test_path = Path(os.path.dirname(__file__))
        self.base_path = self.test_path.parent
        self.testdata_path = self.test_path / "testdata"


@pytest.fixture
def target_mockup_fixture():
    paths = PathSetup()
    mockup_path = paths.test_path / "mock"
    sys.path.append(str(mockup_path))


@pytest.fixture
def base_fixture(request):
    # yield "base_fixture"  # return after setup
    paths = PathSetup()
    config.resource_path = paths.base_path / "resources"

    def teardown():
        # reset singletons
        piweather.base.logger.Logger._instance = None
        piweather.base.system.RuntimeSystem._instance = None

    request.addfinalizer(teardown)

    return paths


def mock_run_on_target(mocker):
    mock_model = mocker.Mock()
    mock_model.return_value = 'Model B'
    mocker.patch('getrpimodel.model', mock_model)
    mock_plaftorm = mocker.Mock()
    mock_plaftorm.return_value = 'Linux'
    mocker.patch('platform.system', mock_plaftorm)
    return mock_model
