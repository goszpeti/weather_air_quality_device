from bottle import get, post, request, run, route  # or route


from waqd.base.component import Component
from typing import TYPE_CHECKING
from threading import Thread
if TYPE_CHECKING:
    from waqd.base.component_reg import ComponentRegistry
    from waqd.settings import Settings

# @get('/login')  # or @route('/login')
# def login():
#     return '''
#         <form action="/login" method="post">
#             Username: <input name="username" type="text" />
#             Password: <input name="password" type="password" />
#             <input value="Login" type="submit" />
#         </form>
#     '''

# @post('/login')  # or @route('/login', method='POST')
# def do_login():
#     from waqd.config import comp_ctrl
#     comps = comp_ctrl.components
#     username = request.forms.get('username')
#     password = request.forms.get('password')
#     if check_login(username, password):
#         return "<p>Your login information was correct.</p>"
#     else:
#         return "<p>Login failed.</p>"

# def check_login(a, b):
#     return True

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
            self._logger.debug(f"Server: Invalid response for /remoteSensor1: {str(data)}")
        comp_ctrl.components.remote_temp_sensor.read_callback(temp, hum)

    def _run_server(self):
        route('/remoteSensor1', 'POST', self._receive_sensor_values)
        run(host='localhost', port=9003, debug=True)



