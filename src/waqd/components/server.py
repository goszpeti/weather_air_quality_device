from bottle import request, run, route, get, post, default_app


from waqd.base.component import Component
from typing import TYPE_CHECKING
from threading import Thread

from waqd.components.sensors import BarometricSensor, CO2Sensor, HumiditySensor, TempSensor
if TYPE_CHECKING:
    from waqd.base.component_reg import ComponentRegistry
    from waqd.settings import Settings


class Server(Component):

    def __init__(self, components: "ComponentRegistry"=None, enabled=True):
        super().__init__(components, enabled=enabled)
        if not enabled:
            return
        self._app = default_app()
        self._run_thread = Thread(
            name="RunServer", target=self._run_server, daemon=True)
        self._run_thread.start()

    def get_remote_ext_values():
        pass

    def _entrypoint(self):
        response = """
        <!DOCTYPE html>
        <html>
        <head>
        <style>
        body { background-color:#7CB9E8}
        h1   { color: white;}
        p    {color: white;}
        </style>
        </head>
        <body>
        <h1>Welcome to the Weather Air Quality Device!</h1>
        <p>&nbsp;</p>
        """
        assert self._comps

        for sensor_name in self._comps.get_names():
            sensor = self._comps.get(sensor_name)
            if not sensor:
                continue
            sensor_class = sensor.__class__
            name = str(sensor_class).replace("'>", "").split(".")

            if issubclass(sensor_class, TempSensor):
                response += f"<p>{name[-1]} temperature: {sensor.get_temperature()}</p>"
            if issubclass(sensor_class, HumiditySensor):
                response += f"<p>{name[-1]} humidity: {sensor.get_humidity()}</p>"
            if issubclass(sensor_class, CO2Sensor):
                response += f"<p>{name[-1]} CO2: {sensor.get_co2()}</p>"
            if issubclass(sensor_class, BarometricSensor):
                response += f"<p>{name[-1]} pressure: {sensor.get_pressure()}</p>"
        response += "</body></html>"
        return response

    def _receive_sensor_values(self):
        from waqd.app import comp_ctrl
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

        if "remoteExtSensor" in request.fullpath:
            comp_ctrl.components.remote_exterior_sensor.read_callback(temp, hum)
        elif "remoteIntSensor" in request.fullpath:
            comp_ctrl.components.remote_interior_sensor.read_callback(temp, hum)

    def _run_server(self):
        route('/remoteExtSensor', 'POST', self._receive_sensor_values)
        route('/remoteIntSensor', 'POST', self._receive_sensor_values)
        # route('/remoteExtSensor', 'GET', self._receive_sensor_values)
        # route('/remoteIntSensor', 'GET', self._receive_sensor_values)
        route('/', 'GET', self._entrypoint)
        # Can't start server rom bottle, because it does not support stopping it without a hack
        from paste import httpserver
        self._server = httpserver.serve(self._app, host='0.0.0.0', port='8080',
                                        daemon_threads=True, start_loop=False)
        self._server.serve_forever()

    def stop(self):
        self._server.server_close()
