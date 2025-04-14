from fasthtml.common import FastHTML, Div
import waqd.app as base_app
app = FastHTML()
if base_app.comp_ctrl is None:
    base_app.basic_setup()

def weather_comp(co2_value, temp_value):
    return Div("CO2: " + str(co2_value), id="co2_value",
               ), Div("TEMP: " + str(temp_value), id="temp_value",
               )

@app.get("/")
def home():
    temp_value = base_app.comp_ctrl.components.temp_sensor.get_temperature()
    pres_value = base_app.comp_ctrl.components.pressure_sensor.get_pressure()
    hum_value = base_app.comp_ctrl.components.humidity_sensor.get_humidity()
    tvoc_value = base_app.comp_ctrl.components.tvoc_sensor.get_tvoc()
    co2_value = base_app.comp_ctrl.components.co2_sensor.get_co2()
    # return Div("Generating...", id=f'gen-{id}', 
    #         hx_post=f"/generations/{id}",
    #         hx_trigger='every 1s', hx_swap='outerHTML')
    return Div(weather_comp(co2_value, temp_value), id="weather",
                hx_trigger='every 10s', hx_swap='innerHTML', hx_get="/sensor_values", hx_target="#weather")

@app.get("/sensor_values")
def get_values():
    co2_value = base_app.comp_ctrl.components.co2_sensor.get_co2()
    temp_value = base_app.comp_ctrl.components.temp_sensor.get_temperature()
    return Div(weather_comp(co2_value, temp_value), id="weather",)
