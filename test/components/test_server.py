
from time import sleep
import requests
import pytest
from test.conftest import is_ci_job
from waqd.components import Server
from waqd.base.component_reg import ComponentRegistry
from waqd.settings import SERVER_ENABLED
from waqd.settings.settings import Settings
from waqd.ui.web.authentification import DEFAULT_USERNAME, UserAuth, validate_username, validate_password


def test_location_parser():
    name, lon, lat = Server.parse_location("London - England, United Kingdom(51.51ÂºE -0.13ÂºN 25m asl)")
    assert name == "London - England"
    assert lat == "51.51"
    assert lon == "-0.13"


def test_validate_username():
    assert validate_username(DEFAULT_USERNAME)
    assert validate_username("My_Name-With.123456")
    assert validate_username("12345")

    assert not validate_username("MyNameToolong1234567890251")
    assert not validate_username("1234")
    assert not validate_username("12345678$")
    assert not validate_username("$12345678")
    assert not validate_username("John Smith")


def test_validate_password():
    assert validate_password("MyPassword1!")
    assert not validate_password("1234")  # Too short
    assert not validate_password("mypassword1!")  # no uppercase
    assert not validate_password("MyPassword!")  # no number
    assert not validate_password("MyPassword1")  # no special char


def test_server(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(SERVER_ENABLED, True)
    comps = ComponentRegistry(settings)
    server = Server(comps)
    url = 'http://localhost:80/remoteExtSensor'
    myobj = {"api_ver": "0.1", 'temp': "25.1", "hum": "10.2"}

    x = requests.post(url, json=myobj)
    print(x)
    pass


def test_user_file_db(base_fixture):
    pw_db = UserAuth()
    pw_db.write_entry("goszpeti", "MyTestPw123$")
    entry = pw_db.get_entry("goszpeti")
    assert entry.get("pw")
    assert pw_db.check_login("goszpeti", "MyTestPw123$")
    pass


@pytest.mark.skipif(is_ci_job(), reason="Only for local debug")
def test_run_server(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(SERVER_ENABLED, True)
    comps = ComponentRegistry(settings)
    comps.server._user_db.write_entry("goszpeti", "MyTestPw123$")
    server = comps.server

    while server:
        sleep(5)
