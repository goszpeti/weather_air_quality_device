### Login in Wifi

### Enable ports in raspi-config


OR

sudo systemctl enable ssh
sudo systemctl start ssh

/boot/firmware/config.txt
dtparam=i2c_arm=on
dtparam=spi=on
[all]
enable_uart=1

### Alternative Wifi connect things

    sudo apt-get install network-manager
    # kill dhcpd to get access to wlan
    sudo dhcpcd -x
    /etc/init.d/network-manager restart
    nmcli device wifi list
    nmcli device wifi connect <SSID> password <PW>>
    pip install nmcli

bash <(curl -L https://github.com/balena-io/wifi-connect/raw/master/scripts/raspbian-install.sh)

### Activate gpu hw acceleration

https://lemariva.com/blog/2020/08/raspberry-pi-4-video-acceleration-decode-chromium
sudo apt-get install libgles2-mesa libgles2-mesa-dev xorg-dev

### BME280 wiring

to correctly work, if SDO is wired to VDD, otherwise the device ID will be 76 and not 77


### Test I2C sensor:

    sudo i2cdetect -y 1

### CCS811
Slowdown baud rate with sudo nano /boot/firmware/config.txt

    dtparam=i2c_baudrate=10000

### Set up Waveshare display
https://www.waveshare.com/wiki/5inch_HDMI_LCD

    mkdir driver
    cd ./driver
    git clone https://github.com/waveshare/LCD-show.git
    cd LCD-show/
    chmod +x LCD5-show
    ./LCD5-show

### Rotate touchscreen
https://www.instructables.com/id/Rotate-Raspberry-Pi-Display-and-Touchscreen/

### Backlight for RpiTD
https://forum-raspberrypi.de/forum/thread/33548-steuerung-des-offiziellen-7-touch-lcd-mit-rpi-backlight/

SUBSYSTEM=="backlight",RUN+="/bin/chmod 666 /sys/class/backlight/%k/brightness /sys/class/backlight/%k/bl_power"

## Speech

Uses google tts.

SOX:
    sudo apt-get install sox libsox-fmt-mp3


### Set backlight on Waveshare b display

    gpio -g pwm 18 1024
    gpio -g mode 18 pwm #set the pin as PWM
    gpio pwmc 1000
    gpio -g pwm 18 X #change the brightness, X ranges 0~1024

In Python it causes screen flickering, presumably because performance.

### Use 433 MHz receiver

uses rpi-rf
scripts/433MHz.py

Configure Linux
---------------

### Full update

sudo apt full-upgrade rather then  sudo apt-get upgrade

### Disable Screen auto turnoff

    sudo apt-get install xscreensaver

open settings and disable screensaver

### SplashScreen

Remove Rainbow Screen
Open “/boot/firmware/config.txt” as root.

sudo nano /boot/firmware/config.txt
Then add below line at the end of the file.

disable_splash=1

https://scribles.net/customizing-boot-up-screen-on-raspberry-pi/

consoleblank=1 logo.nologo quiet loglevel=1 vt.global_cursor_default=0 plymouth.ignore-serial-consoles splash fastboot noatime nodiratime noram

# Uninstall uneeded programs

sudo apt-get purge -y geany thonny debian-reference-en dillo chromium-browser rpi-chromium-mods
sudo apt-get autoremove


# /boot/cmdline.txt

console=serial0,115200 console=tty1 root=PARTUUID=334dade7-02 rootfstype=ext4 elevator=deadline fsck.repair=yes rootwait quiet init=/usr/lib/raspi-config/init_resize.sh splash plymouth.ignore-serial-consoles systemd.run=/boot/firstrun.sh systemd.run_success_action=reboot systemd.unit=kernel-command-line.target

### Set language

    #export DEBIAN_FRONTEND=noninteractive DEBCONF_NONINTERACTIVE_SEEN=true
    sudo dpkg-reconfigure locales de_DE.UTF-8 hu_HU.UTF-8 -f noninteractive

    or sudo nano  /etc/locale.gen ; sudo locale-gen


### Add to autostart

    sudo nano /home/pi/.config/lxsession/LXDE-pi/autostart

Add this to the bottom of that file

    @lxpanel --profile LXDE-pi
    @pcmanfm --desktop --profile LXDE-pi
    @xscreensaver -no-splash
    @lxterminal -e python3 /path/to/your/script.py
    @unclutter -display :0 -idle 3 -root -noevents


### Add right click for touch
or use twofinger wirh https://www.raspberrypi.org/forums/viewtopic.php?t=138575

    sudo nano /etc/X11/xorg.conf

    Section "InputClass"
    Identifier "calibration"
    Driver "evdev"
    MatchProduct "FT5406 memory based driver"

    Option "EmulateThirdButton" "1"
    Option "EmulateThirdButtonTimeout" "750"
    Option "EmulateThirdButtonMoveThreshold" "30"

### Hide mouse cursor

#edit this file:
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

or

sudo apt-get install unclutter

### Restart wifi

sudo systemctl restart dhcpcd
wpa_cli -i wlan0 reconfigure
hostname -I

### get RPi Model

$ cat /proc/device-tree/model
Raspberry Pi 4 Model B Rev 1.1

### Key Shortcuts
 nano ~/.config/openbox/lxde-pi-rc.xml

 Under the keyboard tag add:

<keybind key="Super_L">
    <action name="Execute">
        <command>lxpanelctl menu</command>
    </action>
</keybind>
 or to make F4 open a terminal:

<keybind key="F4">
    <action name="Execute">
        <execute>lxterminal</execute>
    </action>
</keybind>

### Set default audio device

https://www.raspberrypi-spy.co.uk/2019/06/using-a-usb-audio-device-with-the-raspberry-pi/


