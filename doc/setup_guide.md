# WAQD Assembly and Software Setup Guide

## Assembly

### Example guide for recommended variant

#### Parts list

* Raspberry Pi 4 B 2GB
* Micro SD-Card - at least 4 GB
* Raspberry Pi original 7" Touchscreen
* BME280 - Temperature/Humidity/Pressure
* MH-Z19 - CO2
* PIR501 - Motion
* 8x ~10cm jumper cable
* USB-C power adapter (at least 15W)
* SmartiPi Touch 2 chassis

#### Wiring diagram

# <img src="https://www.element14.com/community/servlet/JiveServlet/downloadImage/2-130408-208876/j8header-large.png" width="400">


##### Wiring tables:

* HC-SR501 PIR motion sensor
  * VCC - pin 2 (5V)
  * OUT - pin (GPIO 23) - arbitrary
  * GND - pin 6

* DHT22 (AM2302)
  * VCC - pin 1 (3.3V) or pin 2 (5V)
  * DATA on pin 8 - arbitrary
  * not connected
  * GND

* CCS811
  * VCC - pin 1 (3.3V) or pin 2 (5V)
  * 3v3 out - unused
  * GND
  * SDA - GPIO 2 (0x5a or 0x5b)
  * SCL - GPIO 3
  * Wake - GND
  * RST - Reset - unused
  * INT - Interrupt, when new reading is available  - unused

* MH-Z19
  * 4 Pin side
    * VCC - pin 2 (5V)
    * GND
    * unused
    * PWM (not recommended)
  * 5 pin side
    * Hd - unused
    * unused
    * UART RX - GPIO 14 (TX)
    * UASRT TX - GPIO 15 (RX)
    * Vo - unused

* BMP-280 and BME-280
  * VCC - pin 1 (3.3V)
  * GND
  * SCL - GPIO 3 (0x76)
  * SDA - GPIO 2
  * CSB - I2C or SPI mode selection - unconnected (I2C)
  * SDC - Serial data out/ I2C address selection (Alt. address (0x77) when connected to 3.3V) - unconnected

* BH1750
  * VCC - pin 1 (3.3V)
  * GND
  * SCL - GPIO 3 (0x23)
  * SDA - GPIO 2
  * ADDR - Alt. address (0x5c)

* GP2Y1010AU0F
  * via ADC (TODO)


## Software setup

### Flash Image to SD-Card

* Download and install Raspberry Pi Imager from https://www.raspberrypi.org/software/ for your PC.
* Start Raspberry Pi Imager and select the default Raspberry Pi OS (64bit)
* Press CTRL + SHIFT + X for advanced panel
  * Set "Enable SSH" and change the default password
  * If you want to connect via WiFi: Enable "Configure wifi" and enter your Wifi information.
* Select your SD-Card, then click "Write"

### Manual setup of Raspberry Pi OS

Needed tools:
* USB keyboard
* (optional, but more convenient) a PC connected to the same network as the weather station


#### First Start Wizard

* Connect the USB keyboard
* Select your country and timezone - choose "Use English language", if you don't want the whole OS in your locale
* You can change the default password, if you did not in the Raspberry Imager.
* Continue, until you can connect to your WiFi. Please verify the password, the keyboard uses an english layout! (see config below). If you entered you WiFi information in the Raspberry Imager, this step is skipped.
* You can install the updates, otherwise it will be done later.

#### Change keyboard layout

* Taskbar Menu -> Preferences -> Raspberry Pi Configuration -> Localisation -> Set Keyboard -> Layout

#### Set up a Remote Connection

On the Raspberry:
* Get IP from Raspberry while hovering over the WiFi tray icon
* Enable VNC in Configuration:
  * Taskbar Menu -> Preferences -> Raspberry Pi Configuration -> Interfaces -> Enable VNC -> Exit and reboot

On your PC:
* Install VNC Viewer (https://www.realvnc.com/en/connect/download/viewer/)
* New connection -> Host Name: IP User: pi Password: raspberry (default)


#### Enable required connections (now included in installer)

* Got to Taskbar Menu -> Preferences -> Raspberry Pi Configuration -> Interfaces
* Enable I2C, SPI and Serial Port -> disable serial console!
* Exit and reboot

#### Rotate touchscreen (if needed for case)

https://www.instructables.com/id/Rotate-Raspberry-Pi-Display-and-Touchscreen/

#### Install supported languages (now included in installer)

* Start a terminal (ctrl + alt + t)
* Enter command the following commands: 
    sudo dpkg-reconfigure locales

#### Disable auto display shutdown (now included in installer)

    sudo apt install xscreensaver

and disable in settings

    @xscreensaver -no-splash

### Hide mouse cursor (now included in installer)

edit this file:
  /usr/share/lightdm/lightdm.conf.d/01_debian.conf

...below are the contents of the '01_debian.conf' file, where I've added xserver-command=X -nocursor to the end

    # Debian specific defaults
    #
    # - use lightdm-greeter session greeter, points to the etc-alternatives managed
    # greeter
    # - hide users list by default, we don't want to expose them
    # - use Debian specific session wrapper, to gain support for
    # /etc/X11/Xsession.d scripts

    [Seat:*]
    greeter-session=lightdm-greeter
    greeter-hide-users=true
    session-wrapper=/etc/X11/Xsession
    xserver-command=X -nocursor


#### Install WAQD

WeatherAirQualityDevice

* Start a terminal (ctrl + alt + t)
* Enter command he following commands: 
    git clone https://github.com/goszpeti/WeatherAirQualityDevice.git
    cd ./WeatherAirQualityDevice/script/installer
    chmod +x ./start_installer.sh
    ./start_installer.sh

From here everything should work automatically and the Raspberry will restart and load WAQD. This can take up to 5 minutes. You can track the progress by pressing ALT + TAB to get back to the terminal window.

#### Setup WAQD

There are few settings, which are not yet available in the GUI and must be setup manually:

##### Get OpenWeatherMap API key

To be able to use OpenWeatherMap for weather forecasts, you will need to register (free) on their site.

* On your PC, go to https://home.openweathermap.org/users/sign_up and sign up
* After signing in, click on "API keys"
* On the right side, give the key a name (e.g. WAQD) and then click generate
* You will need to enter this key into the settings

* On your RPi enter the following on a terminal:
    nano ~/.waqd/config.ini

Find the following setting: "open_weather_api_key = " and paste the generated APi key.
Save the file.

##### Set forecast location for OpenWeatherMap

* Go to https://openweathermap.org/ and enter your location in the search bar on the top.
* If, there are multiple hits, select your city
* Now, look at the URL-bar: you will need the part after the last slash: e.g. 2643743 in https://openweathermap.org/city/2643743. This is your city id.

Now enter it in the config file:

* On your RPi enter the following on a terminal:
    nano ~/.waqd/config.ini
Look for the section [Forecast].

You can add multiple cities following the following scheme: ow_city_id_<number> = <CityName>,<CityID>

So for your first city, this would be: ow_city_id_1 = London,2643743

At last, go to the options menu in the WAQD application and press apply.


#### Add scheduled events

TODO

