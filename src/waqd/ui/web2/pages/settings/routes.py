from pathlib import Path
from typing import Annotated
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form
from fastapi.responses import HTMLResponse
from requests import get
from pydantic import BaseModel

import waqd.app as app
from .....components.weather.base_types import Location
from .....components.weather.open_meteo import OpenMeteo
from waqd.settings import (
    AUTO_UPDATER_ENABLED,
    BME_280_ENABLED,
    BMP_280_ENABLED,
    CCS811_ENABLED,
    DHT_22_PIN,
    LOCATION_ALTITUDE_M,
    LOCATION_COUNTRY_CODE,
    LOCATION_LATITUDE,
    LOCATION_LONGITUDE,
    LOCATION_NAME,
    LOCATION_STATE,
    MH_Z19_ENABLED,
    MOTION_SENSOR_ENABLED,
    MOTION_SENSOR_PIN,
    STARTUP_JINGLE,
    SOUND_ENABLED,
    UPDATER_USER_BETA_CHANNEL,
)
from waqd.ui.web2.authentication import User, get_current_user_with_redirect
from waqd.ui.web2.templates import render_main, sub_template

rt = APIRouter()

current_path = Path(__file__).parent.resolve()


@rt.get("/", response_class=HTMLResponse)
async def settings(current_user: Annotated[User, Depends(get_current_user_with_redirect)]):
    settings = app.settings.get_all()

    content = sub_template(
        "settings.html",
        settings,
        #{
            
            # rework this with pydantic settings
            # "location_name": app.settings.get(LOCATION_NAME),
            # "location_longitude": app.settings.get(LOCATION_LONGITUDE),
            # "location_latitude": app.settings.get(LOCATION_LATITUDE),
            # "location_country_code": app.settings.get(LOCATION_COUNTRY_CODE),
            # "location_state": app.settings.get(LOCATION_STATE),
            # "sound": {
            #     "name": SOUND_ENABLED,
            #     "value": app.settings.get(SOUND_ENABLED),
            # },
            # "intro_jingle": {
            #     "name": STARTUP_JINGLE,
            #     "value": app.settings.get(STARTUP_JINGLE),
            # },
            # "auto_update": {
            #     "name": AUTO_UPDATER_ENABLED,
            #     "value": app.settings.get(AUTO_UPDATER_ENABLED),
            # },
            # "beta_update": {
            #     "name": UPDATER_USER_BETA_CHANNEL,
            #     "value": app.settings.get(UPDATER_USER_BETA_CHANNEL),
            # },
            # "bme_280": {
            #     "name": BME_280_ENABLED,
            #     "value": app.settings.get(BME_280_ENABLED),
            # },
            # "bmp_280": {
            #     "name": BMP_280_ENABLED,
            #     "value": app.settings.get(BMP_280_ENABLED),
            # },
            # "dht_22": {
            #     "name": DHT_22_PIN,
            #     "value": app.settings.get(DHT_22_PIN),
            # },
            # "mh_z19": {
            #     "name": MH_Z19_ENABLED,
            #     "value": app.settings.get(MH_Z19_ENABLED),
            # },
            # "ccs811": {
            #     "name": CCS811_ENABLED,
            #     "value": app.settings.get(CCS811_ENABLED),
            # },
            # "motion_sensor": {
            #     "name": MOTION_SENSOR_ENABLED,
            #     "value": app.settings.get(MOTION_SENSOR_ENABLED),
            # },
            # "motion_sensor_pin": {
            #     "name": MOTION_SENSOR_PIN,
            #     "value": app.settings.get(MOTION_SENSOR_PIN),
            # },
            # "brightness": {
            #     "name": MOTION_SENSOR_PIN,
            #     "value": app.settings.get(MOTION_SENSOR_PIN),
            # },
        #},
        current_path,
    )
    return render_main(content, current_user)


@rt.get("/location_search_result", response_class=HTMLResponse)
async def location_search_result(query: str):
    # request to the Open-Meteo Geocoding API
    location_data = OpenMeteo().find_location_candidates(query, lang="en")
    if not location_data:
        return HTMLResponse("No location found")
    return sub_template(
        "snippets/location_result.html",
        {"location_data": location_data},
        current_path,  #
        component=True,
    )


@rt.post("/set", response_class=HTMLResponse)
async def set_setting(name: str = Form(), value=Form()):
    try:
        app.settings.set(name, value)
        return HTMLResponse("Set ☑")
    except Exception as e:
        return HTMLResponse(f"Error: {e}", status_code=500)


@rt.post("/set/location", response_class=HTMLResponse)
async def set_location(
    location: Location
):
    try:
        app.settings.set(LOCATION_NAME, location.name)
        app.settings.set(LOCATION_LATITUDE, location.latitude)
        app.settings.set(LOCATION_LONGITUDE, location.longitude)
        app.settings.set(LOCATION_COUNTRY_CODE, location.country_code)
        app.settings.set(LOCATION_ALTITUDE_M, location.altitude)
        app.settings.set(LOCATION_STATE, location.state)

        return HTMLResponse("Set ☑")
    except Exception as e:
        return HTMLResponse(f"Error: {e}", status_code=500)
