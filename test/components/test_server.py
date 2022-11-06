
from time import sleep
import requests
import pytest
from test.conftest import is_ci_job
from waqd.components import Server
from waqd.base.component_reg import ComponentRegistry
from waqd.settings import SERVER_ENABLED
from waqd.settings.settings import Settings
from waqd.base.authentification import UserFileDB

def testServer(base_fixture):
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
    pw_db = UserFileDB()
    pw_db.write_entry("goszpeti", "MyTestPw123$")
    entry = pw_db.get_entry("goszpeti")
    assert entry.get("pw")
    assert pw_db.check_login("goszpeti", "MyTestPw123$")
    pass


@pytest.mark.skipif(is_ci_job(), reason="Only for local debug")
def testRunServer(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    settings.set(SERVER_ENABLED, True)
    comps = ComponentRegistry(settings)
    comps.server._user_db.write_entry("goszpeti", "MyTestPw123$")
    server = comps.server

    while server:
        sleep(5)
