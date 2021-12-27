from bottle import request, run, route


from waqd.base.component import Component
from typing import TYPE_CHECKING
from threading import Thread
if TYPE_CHECKING:
    from waqd.base.component_reg import ComponentRegistry
    from waqd.settings import Settings

class Server(Component):

    def __init__(self, components: "ComponentRegistry" = None, settings: "Settings" = None):
        super().__init__(components=components, settings=settings)
        self._run_thread = Thread(
            name="RunServer", target=self._run_server, daemon=True)
        self._run_thread.start()
        self._reload_forbidden = True  # must be set manually in the child class


    def _receive_sensor_values(self):
        from waqd.config import comp_ctrl
        if not comp_ctrl:
            return
        data = request.json
        temp = 0
        hum = 0
        try:
            api_ver = data.get("api_ver")
            if api_ver == "0.1":
                temp = float(data.get("temp", None))
                hum = float(data.get("hum", None))
        except:
            self._logger.debug(f"Server: Invalid response for /remoteSensor: {str(data)}")

        if request.fullpath == "remoteExtSensor":
            comp_ctrl.components.remote_exterior_sensor.read_callback(temp, hum)
        elif request.fullpath == "remoteIntSensor":
            comp_ctrl.components.remote_interior_sensor.read_callback(temp, hum)


    def _run_server(self):
        route('/remoteExtSensor', 'POST', self._receive_sensor_values)
        route('/remoteIntSensor', 'POST', self._receive_sensor_values)
        run(host='localhost', port=8080, debug=True)



