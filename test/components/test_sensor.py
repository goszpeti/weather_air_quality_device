
import requests
from waqd.components import Server
from waqd.base.component_reg import ComponentRegistry
from waqd.settings.settings import Settings

def testServer(base_fixture):
    settings = Settings(base_fixture.testdata_path / "integration")
    comps = ComponentRegistry(settings)
    #Server(comps, settings)
    url = 'http://localhost:9003/remoteSensor1'
    myobj = {"api_ver": "0.1", 'temp': "25.1", "hum": "80.2"}

    x = requests.post(url, json=myobj)
    print(x)
    pass
