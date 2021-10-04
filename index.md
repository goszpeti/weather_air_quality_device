# <img src="https://github.com/goszpeti/WeatherAirQualityDevice/blob/master/doc/images/loading_screen.jpg?raw=true" width="300">

# Weather and Air Quality Device - based on Raspberry Pi

## Quick Overview

The goal of this project is to create a weather station for indoor use
with the use of commonly used sensors and a touch display.

It also focuses on an easy system setup and assembly with a suited case. 

The project will be written with the usage of Qt in Python.

## Features

# <img src="https://github.com/goszpeti/WeatherAirQualityDevice/blob/master/doc/images/main_gui.jpg?raw=true" width="600">

* Info pane witch clock and date
* Interior with sensor display
* Exterior with online or remote sensor temperature
* 3 day forecast

# <img src="https://github.com/goszpeti/WeatherAirQualityDevice/blob/master//doc/images/options.jpg?raw=true" width="600">

* Options for
  * display settings
  * scaling
  * language
  * online weather settings


## Supported parts

### Raspberry Pi

* theoretically all versions, but a model 2 was never tested
* model 1 runs also, but is very slow

### Case

#### SmartiPi Touch 2
  * recommended because of cable management and supports all RPi Versions up to RPi4.

##### Sensor holding case:

There is a 3D-printable sensor case for holding up to 4 sensors, which is optimized in size to the recommended sensors, see Adapter, Base and Lid in src/assets. It also has slits for air and hole for inserting cables.
You will need 4 M3x30 screws, and they will fit exactly on the back of the SmartiPi Touch 2 case.


# <img src="https://github.com/goszpeti/WeatherAirQualityDevice/blob/master/doc/images/sensor_case.png?raw=true" width="400">

### Touchscreen

* Raspberry Pi original 7" capacitive Touchscreen
* Waveshare 5" resistive touch display

### Sensors

Basic
* BME280 - Temperature/Humidity/Pressure
  * very stable and has all the needed sensors
* BMP280 - Temperature/Pressure
  * same as the BME but without humidity
* DHT22 - Temperature/Humidity
  * instable driver because of pulse based connection

Air quality
* MH-Z19 - CO2
  * NDIR based CO2 sensor - pricy, but the gets very good results! 
* CCS811 - TVOC/CO2
  * measures TVOC (total volatile organic components) and only calculates an equivalent CO2 - very inaccurate readings

Motion sensor:
* PIR501 - standard part, cheap and gets the job done

Sound:
* Passive Speaker - Sound is currently only a gimmick

## Included 3rd-Party Assets

* Weather Icons licensed under [SIL OFL 1.1](http://scripts.sil.org/OFL) from http://weathericons.io)
* Franzo Font under [Apache 2.0](https://www.apache.org/licenses/LICENSE-2.0) from https://fontlibrary.org/en/font/franzo
* Images from Unsplash under [Unsplash license](https://unsplash.com/license) from https://unsplash.com
  * https://unsplash.com/photos/VjMJmwZOs9M from Jesse Borovnica
  * https://unsplash.com/photos/GLf7bAwCdYg from Adrian Infernus
  * https://unsplash.com/photos/pbxwxwfI0B4 from Anandu Vinod
  * https://unsplash.com/photos/dkQGYygMcrQ from Azfan Nugi
  * https://unsplash.com/photos/Z9Ds4w141i4 from Annie Spratt
  * https://unsplash.com/photos/v9bnfMCyKbg from Billy Huynh
  * https://unsplash.com/photos/i8cBWhrajKs from Bobby Stevenson
  * https://unsplash.com/photos/6tfO1M8_gas from  Chris Lawton
  * https://unsplash.com/photos/cs_WcGkz5IM from  Crina Parasca
  * https://unsplash.com/photos/pv2ZlDfstXc from Inge Maria
  * https://unsplash.com/photos/0ZC4VRG2Vhg from Ira Avtukhova
  * https://unsplash.com/photos/cIEpVluspZc from Javier Esteban
  * https://unsplash.com/photos/tCX_vAa7Um8 from Mathieu Bigard
  * https://unsplash.com/photos/ve-R7PCjJDk from Nick Nice
  * https://unsplash.com/photos/NpF9JLGYfeQ from Shot by Cerqueira
  * https://unsplash.com/photos/NkQD-RHhbvY from Sharon McCutcheon
  * https://unsplash.com/photos/bWtd1ZyEy6w from Valentin Muller
  * https://unsplash.com/photos/HxKgk_MpHMM from Zoltan Tasi
  * https://unsplash.com/photos/w8hWTFpGtpY from Chandler Cruttenden
  * https://unsplash.com/photos/_SnPaOUxO2k from Annie Niemaszyk
  * https://unsplash.com/photos/06qZZZNfzD8 from Scott Webb
  * https://unsplash.com/photos/n2poVQijgzo from Zuzana Ruttkay



## Used software

* For Python libs see setup.py
* For system packages see /scripts/installer/start_installer.sh ("Install needed system libraries" section)

## Needed Software

* Raspberry PI OS - 32 bit (Buster) - 64 bit is still missing some libraries.
  * LightDM desktop manager
  * XFCE desktop environment with pcmanfm
  * Plymouth for boot screen customization
  * raspi-config
  * Python 3.7

## Author:

Copyright (c) 2021 Péter Gosztolya and contributors.
