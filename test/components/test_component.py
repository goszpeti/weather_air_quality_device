import logging
import time

from waqd.base.components import (Component, ComponentRegistry,
                                       CyclicComponent)
from waqd.base.system import RuntimeSystem
from waqd.settings import Settings


def testComponent(base_fixture):
    # test default constructor
    TestComponent = Component()
    # check default settings
    assert not TestComponent.is_disabled
    assert not TestComponent.reload_forbidden
    assert isinstance(TestComponent._logger, logging.Logger)
    assert isinstance(TestComponent._runtime_system, RuntimeSystem)
    assert TestComponent._settings is None
    assert TestComponent._comps is None

    settings = Settings(base_fixture.testdata_path / "integration")
    TestComponent = Component(settings=settings)
    assert TestComponent._settings == settings

    components = ComponentRegistry(settings)
    TestComponent = Component(components)
    assert TestComponent._comps == components


def testCyclicComponent(base_fixture):
    # minimalistic implementation
    class TestCycComp(CyclicComponent):
        INIT_WAIT_TIME = 1
        UPDATE_TIME = 1
        STOP_TIMEOUT = 2
        
        def __init__(self):
            super().__init__()
            self._update_value = None
            self._reload_forbidden = True

        def _init(self):
            self._update_value = 0

        def _update(self):
            self._update_value += 1

    # test default constructor
    TestComponent = TestCycComp()
    # check default settings
    assert not TestComponent.is_ready
    assert not TestComponent.is_disabled
    assert TestComponent.reload_forbidden
    assert isinstance(TestComponent._logger, logging.Logger)
    assert isinstance(TestComponent._runtime_system, RuntimeSystem)

    # test init and timing
    TestComponent._start_update_loop(TestComponent._init)
    assert TestComponent.is_alive
    time.sleep(2)
    assert TestComponent._update_value == 0
    assert TestComponent.is_ready

    # test stop
    TestComponent.stop()
    assert not TestComponent.is_alive
    assert TestComponent._update_value == 0

    # test continuous update
    TestComponent = TestCycComp()
    TestComponent.INIT_WAIT_TIME = 0
    TestComponent._update_value = 0
    TestComponent._start_update_loop(update_func=TestComponent._update)
    time.sleep(2)
    update_value = TestComponent._update_value
    assert update_value > 0
    time.sleep(2)
    update_value = TestComponent._update_value
    assert update_value > 1


    # TODO test stop timeout

