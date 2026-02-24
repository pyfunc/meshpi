"""
meshpi.hardware.profiles
========================
Hardware profile definitions for Raspberry Pi peripherals.

Each profile is a dict describing:
  - category: gpio | display | camera | sensor | audio | storage | networking | hat
  - apply_fn: callable(config_dict) → list of shell commands to apply
  - config_keys: which .env keys this profile consumes
  - packages: apt packages to install
  - kernel_modules: modules to modprobe/add to /etc/modules
  - overlays: device-tree overlays for /boot/config.txt
  - description: human-readable summary

Usage:
  from meshpi.hardware.profiles import PROFILES, get_profile, list_profiles
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional


@dataclass
class HardwareProfile:
    id: str
    name: str
    category: str
    description: str
    config_keys: list[str] = field(default_factory=list)
    packages: list[str] = field(default_factory=list)
    kernel_modules: list[str] = field(default_factory=list)
    overlays: list[str] = field(default_factory=list)           # /boot/config.txt dtoverlay lines
    config_txt_lines: list[str] = field(default_factory=list)  # raw /boot/config.txt additions
    cmdline_additions: str = ""
    post_commands: list[str] = field(default_factory=list)      # shell commands after package install
    tags: list[str] = field(default_factory=list)


PROFILES: dict[str, HardwareProfile] = {}


def _reg(p: HardwareProfile) -> HardwareProfile:
    PROFILES[p.id] = p
    return p


# ─────────────────────────────────────────────────────────────────────────────
# DISPLAYS — LCD (I2C)
# ─────────────────────────────────────────────────────────────────────────────

_reg(HardwareProfile(
    id="lcd_i2c_16x2",
    name="LCD 16×2 I2C (PCF8574)",
    category="display",
    description="Standard 16×2 character LCD connected via I2C PCF8574 backpack",
    packages=["python3-smbus", "i2c-tools"],
    kernel_modules=["i2c-dev", "i2c-bcm2708"],
    overlays=["dtoverlay=i2c-rtc,ds3231"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    tags=["lcd", "i2c", "character-display"],
))

_reg(HardwareProfile(
    id="lcd_i2c_20x4",
    name="LCD 20×4 I2C",
    category="display",
    description="20×4 character LCD connected via I2C",
    packages=["python3-smbus", "i2c-tools"],
    kernel_modules=["i2c-dev"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    tags=["lcd", "i2c", "character-display"],
))

_reg(HardwareProfile(
    id="oled_ssd1306_i2c",
    name="OLED SSD1306 128×64 I2C",
    category="display",
    description="Monochrome OLED display (SSD1306 driver) via I2C",
    packages=["python3-pip", "python3-pil"],
    kernel_modules=["i2c-dev"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    post_commands=["pip3 install adafruit-circuitpython-ssd1306 luma.oled"],
    tags=["oled", "i2c", "ssd1306"],
))

_reg(HardwareProfile(
    id="oled_sh1106_spi",
    name="OLED SH1106 128×64 SPI",
    category="display",
    description="SH1106 OLED via SPI interface",
    packages=["python3-pip", "python3-pil"],
    kernel_modules=["spi-bcm2835"],
    config_txt_lines=["dtparam=spi=on"],
    post_commands=["pip3 install luma.oled"],
    tags=["oled", "spi", "sh1106"],
))

_reg(HardwareProfile(
    id="tft_ili9341_spi",
    name="TFT ILI9341 2.8\" SPI",
    category="display",
    description="320×240 colour TFT display (ILI9341) via SPI",
    packages=["python3-pip"],
    kernel_modules=["spi-bcm2835"],
    config_txt_lines=[
        "dtparam=spi=on",
        "dtoverlay=piscreen,speed=16000000,rotate=90",
    ],
    post_commands=["pip3 install luma.lcd adafruit-circuitpython-ili9341"],
    tags=["tft", "spi", "ili9341", "colour"],
))

_reg(HardwareProfile(
    id="tft_st7735_spi",
    name="TFT ST7735 1.8\" SPI",
    category="display",
    description="128×160 colour TFT (ST7735) via SPI",
    packages=["python3-pip"],
    kernel_modules=["spi-bcm2835"],
    config_txt_lines=["dtparam=spi=on"],
    post_commands=["pip3 install adafruit-circuitpython-st7735"],
    tags=["tft", "spi", "st7735"],
))

_reg(HardwareProfile(
    id="epaper_waveshare_2in13",
    name="Waveshare e-Paper 2.13\"",
    category="display",
    description="Waveshare 250×122 e-paper display via SPI",
    packages=["python3-pip", "python3-pil"],
    kernel_modules=["spi-bcm2835"],
    config_txt_lines=["dtparam=spi=on"],
    post_commands=["pip3 install waveshare-epaper RPi.GPIO"],
    tags=["epaper", "spi", "waveshare", "e-ink"],
))

_reg(HardwareProfile(
    id="epaper_waveshare_7in5",
    name="Waveshare e-Paper 7.5\"",
    category="display",
    description="Waveshare 800×480 e-paper display via SPI",
    packages=["python3-pip", "python3-pil"],
    kernel_modules=["spi-bcm2835"],
    config_txt_lines=["dtparam=spi=on"],
    post_commands=["pip3 install waveshare-epaper RPi.GPIO"],
    tags=["epaper", "spi", "waveshare", "large"],
))

# ─────────────────────────────────────────────────────────────────────────────
# DISPLAYS — HDMI / DSI
# ─────────────────────────────────────────────────────────────────────────────

_reg(HardwareProfile(
    id="hdmi_1080p",
    name="HDMI 1080p@60Hz",
    category="display",
    description="Standard HDMI output forced to 1920×1080@60Hz",
    config_txt_lines=[
        "hdmi_group=2",
        "hdmi_mode=82",
        "hdmi_force_hotplug=1",
        "hdmi_drive=2",
    ],
    tags=["hdmi", "1080p", "fullhd"],
))

_reg(HardwareProfile(
    id="hdmi_4k",
    name="HDMI 4K@30Hz",
    category="display",
    description="HDMI 4K (3840×2160@30Hz) — RPi 4/5 only",
    config_txt_lines=[
        "hdmi_group=2",
        "hdmi_mode=97",
        "hdmi_force_hotplug=1",
        "hdmi_drive=2",
    ],
    tags=["hdmi", "4k", "uhd"],
))

_reg(HardwareProfile(
    id="hdmi_touchscreen_7in",
    name="Official RPi 7\" DSI Touchscreen",
    category="display",
    description="Official Raspberry Pi 800×480 DSI touchscreen",
    packages=["xinput-calibrator"],
    overlays=["dtoverlay=rpi-ft5406"],
    config_txt_lines=["display_default_lcd=1"],
    tags=["dsi", "touchscreen", "official"],
))

_reg(HardwareProfile(
    id="hdmi_dual",
    name="Dual HDMI (RPi 4/5)",
    category="display",
    description="Enable both HDMI ports on RPi 4/5",
    config_txt_lines=[
        "[hdmi:0]",
        "hdmi_force_hotplug=1",
        "hdmi_group=2",
        "hdmi_mode=82",
        "[hdmi:1]",
        "hdmi_force_hotplug=1",
        "hdmi_group=2",
        "hdmi_mode=82",
    ],
    tags=["hdmi", "dual", "rpi4", "rpi5"],
))

_reg(HardwareProfile(
    id="composite_pal",
    name="Composite Video PAL",
    category="display",
    description="Composite video output (PAL, Europe)",
    config_txt_lines=[
        "sdtv_mode=2",
        "sdtv_aspect=3",
        "enable_tvout=1",
    ],
    tags=["composite", "pal", "analog"],
))

# ─────────────────────────────────────────────────────────────────────────────
# GPIO — Motor drivers & steppers
# ─────────────────────────────────────────────────────────────────────────────

_reg(HardwareProfile(
    id="gpio_stepper_a4988",
    name="Stepper Driver A4988",
    category="gpio",
    description="A4988 / DRV8825 stepper motor driver via GPIO STEP/DIR",
    packages=["python3-pip"],
    config_txt_lines=["dtparam=spi=off"],
    post_commands=["pip3 install RPi.GPIO gpiozero"],
    config_keys=["GPIO_STEPPER_STEP_PIN", "GPIO_STEPPER_DIR_PIN", "GPIO_STEPPER_EN_PIN"],
    tags=["stepper", "motor", "a4988", "drv8825"],
))

_reg(HardwareProfile(
    id="gpio_stepper_arm69ak",
    name="Stepper ARM69AK via GPIO",
    category="gpio",
    description="ARM69AK stepper motor configured for Raspberry Pi GPIO control",
    packages=["python3-pip"],
    post_commands=["pip3 install RPi.GPIO gpiozero pigpio"],
    config_keys=[
        "GPIO_STEPPER_STEP_PIN",
        "GPIO_STEPPER_DIR_PIN",
        "GPIO_STEPPER_EN_PIN",
        "GPIO_STEPPER_STEPS_PER_REV",
        "GPIO_STEPPER_MICROSTEP",
    ],
    config_txt_lines=["dtparam=i2c_arm=on"],
    tags=["stepper", "arm69ak", "motor", "gpio"],
))

_reg(HardwareProfile(
    id="gpio_relay_board",
    name="Relay Board (multi-channel)",
    category="gpio",
    description="4/8-channel relay board controlled via GPIO",
    packages=["python3-pip"],
    post_commands=["pip3 install RPi.GPIO"],
    config_keys=["GPIO_RELAY_PINS", "GPIO_RELAY_ACTIVE_LOW"],
    tags=["relay", "gpio", "output"],
))

_reg(HardwareProfile(
    id="gpio_pwm_servo",
    name="PWM Servo Controller",
    category="gpio",
    description="Hardware PWM servo control via GPIO18/GPIO12",
    packages=["python3-pip"],
    config_txt_lines=["dtoverlay=pwm-2chan,pin=18,func=2,pin2=12,func2=4"],
    post_commands=["pip3 install RPi.GPIO pigpio"],
    config_keys=["GPIO_SERVO_PIN", "GPIO_SERVO_MIN_PULSE", "GPIO_SERVO_MAX_PULSE"],
    tags=["servo", "pwm", "gpio"],
))

_reg(HardwareProfile(
    id="gpio_pca9685",
    name="PCA9685 16-channel PWM/Servo",
    category="gpio",
    description="PCA9685 I2C PWM board for 16 servos/LEDs",
    packages=["python3-pip"],
    kernel_modules=["i2c-dev"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    post_commands=["pip3 install adafruit-circuitpython-pca9685"],
    config_keys=["GPIO_PCA9685_ADDRESS", "GPIO_PCA9685_FREQ_HZ"],
    tags=["servo", "pwm", "pca9685", "i2c"],
))

_reg(HardwareProfile(
    id="gpio_distance_hcsr04",
    name="Distance Sensor HC-SR04",
    category="gpio",
    description="Ultrasonic distance sensor HC-SR04",
    packages=["python3-pip"],
    post_commands=["pip3 install RPi.GPIO gpiozero"],
    config_keys=["GPIO_TRIGGER_PIN", "GPIO_ECHO_PIN"],
    tags=["distance", "ultrasonic", "sensor", "hcsr04"],
))

_reg(HardwareProfile(
    id="gpio_button_led",
    name="GPIO Buttons & LEDs",
    category="gpio",
    description="Basic GPIO buttons and LEDs with debouncing",
    packages=["python3-pip"],
    post_commands=["pip3 install gpiozero RPi.GPIO"],
    config_keys=["GPIO_BUTTON_PINS", "GPIO_LED_PINS"],
    tags=["gpio", "button", "led", "basic"],
))

_reg(HardwareProfile(
    id="gpio_encoder_rotary",
    name="Rotary Encoder",
    category="gpio",
    description="Rotary encoder with push-button via GPIO",
    packages=["python3-pip"],
    post_commands=["pip3 install RPi.GPIO"],
    config_keys=["GPIO_ENCODER_A_PIN", "GPIO_ENCODER_B_PIN", "GPIO_ENCODER_BTN_PIN"],
    tags=["encoder", "gpio", "input"],
))

# ─────────────────────────────────────────────────────────────────────────────
# SENSORS
# ─────────────────────────────────────────────────────────────────────────────

_reg(HardwareProfile(
    id="sensor_dht22",
    name="DHT22 Temperature & Humidity",
    category="sensor",
    description="DHT22 / AM2302 one-wire temperature and humidity sensor",
    packages=["python3-pip"],
    post_commands=["pip3 install adafruit-circuitpython-dht"],
    config_keys=["GPIO_DHT22_PIN"],
    tags=["sensor", "temperature", "humidity", "dht22"],
))

_reg(HardwareProfile(
    id="sensor_ds18b20",
    name="DS18B20 Temperature (1-Wire)",
    category="sensor",
    description="DS18B20 waterproof temperature sensor via 1-Wire bus",
    kernel_modules=["w1-gpio", "w1-therm"],
    config_txt_lines=["dtoverlay=w1-gpio,gpiopin=4"],
    config_keys=["GPIO_1WIRE_PIN"],
    tags=["sensor", "temperature", "1wire", "ds18b20"],
))

_reg(HardwareProfile(
    id="sensor_bme280",
    name="BME280 Temp/Humidity/Pressure I2C",
    category="sensor",
    description="Bosch BME280 environmental sensor via I2C",
    packages=["python3-pip"],
    kernel_modules=["i2c-dev"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    post_commands=["pip3 install adafruit-circuitpython-bme280"],
    config_keys=["SENSOR_BME280_ADDRESS"],
    tags=["sensor", "bme280", "i2c", "pressure"],
))

_reg(HardwareProfile(
    id="sensor_ina219",
    name="INA219 Current/Voltage Sensor",
    category="sensor",
    description="INA219 I2C power monitoring sensor",
    packages=["python3-pip"],
    kernel_modules=["i2c-dev"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    post_commands=["pip3 install adafruit-circuitpython-ina219"],
    config_keys=["SENSOR_INA219_ADDRESS", "SENSOR_INA219_SHUNT_OHM"],
    tags=["sensor", "power", "current", "voltage", "ina219"],
))

_reg(HardwareProfile(
    id="sensor_mpu6050",
    name="MPU-6050 Accelerometer/Gyroscope",
    category="sensor",
    description="MPU-6050 6-axis IMU via I2C",
    packages=["python3-pip"],
    kernel_modules=["i2c-dev"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    post_commands=["pip3 install mpu6050-raspberrypi"],
    config_keys=["SENSOR_MPU6050_ADDRESS"],
    tags=["sensor", "imu", "accelerometer", "gyroscope", "mpu6050"],
))

_reg(HardwareProfile(
    id="sensor_vl53l0x",
    name="VL53L0X Laser Distance I2C",
    category="sensor",
    description="ST VL53L0X ToF laser ranging sensor via I2C",
    packages=["python3-pip"],
    kernel_modules=["i2c-dev"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    post_commands=["pip3 install adafruit-circuitpython-vl53l0x"],
    config_keys=["SENSOR_VL53L0X_ADDRESS"],
    tags=["sensor", "distance", "tof", "laser", "vl53l0x"],
))

_reg(HardwareProfile(
    id="sensor_ads1115",
    name="ADS1115 4-channel ADC I2C",
    category="sensor",
    description="16-bit 4-channel ADC (ADS1115) via I2C for analogue sensors",
    packages=["python3-pip"],
    kernel_modules=["i2c-dev"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    post_commands=["pip3 install adafruit-circuitpython-ads1x15"],
    config_keys=["SENSOR_ADS1115_ADDRESS", "SENSOR_ADS1115_GAIN"],
    tags=["adc", "analogue", "ads1115", "i2c"],
))

# ─────────────────────────────────────────────────────────────────────────────
# CAMERAS
# ─────────────────────────────────────────────────────────────────────────────

_reg(HardwareProfile(
    id="camera_picam_v2",
    name="Raspberry Pi Camera Module v2",
    category="camera",
    description="Official RPi Camera Module 2 (IMX219, 8MP)",
    packages=["python3-picamera2", "libcamera-apps"],
    overlays=["dtoverlay=imx219"],
    config_txt_lines=["start_x=1", "gpu_mem=128"],
    post_commands=["raspi-config nonint do_camera 0"],
    tags=["camera", "picam", "imx219", "official"],
))

_reg(HardwareProfile(
    id="camera_picam_hq",
    name="Raspberry Pi HQ Camera",
    category="camera",
    description="Official RPi HQ Camera (IMX477, 12MP)",
    packages=["python3-picamera2", "libcamera-apps"],
    overlays=["dtoverlay=imx477"],
    config_txt_lines=["start_x=1", "gpu_mem=256"],
    tags=["camera", "hq", "imx477", "official"],
))

_reg(HardwareProfile(
    id="camera_usb_uvc",
    name="USB UVC Webcam",
    category="camera",
    description="Generic USB webcam (UVC-compatible)",
    packages=["v4l-utils", "python3-opencv"],
    kernel_modules=["uvcvideo"],
    tags=["camera", "usb", "webcam", "uvc"],
))

_reg(HardwareProfile(
    id="camera_ir_nightvision",
    name="IR Night Vision Camera",
    category="camera",
    description="IR-sensitive camera for night vision applications",
    packages=["python3-picamera2"],
    overlays=["dtoverlay=imx219"],
    config_txt_lines=["start_x=1", "gpu_mem=128", "disable_camera_led=1"],
    tags=["camera", "ir", "nightvision"],
))

# ─────────────────────────────────────────────────────────────────────────────
# AUDIO
# ─────────────────────────────────────────────────────────────────────────────

_reg(HardwareProfile(
    id="audio_hdmi",
    name="Audio via HDMI",
    category="audio",
    description="Route audio output through HDMI",
    config_txt_lines=["hdmi_drive=2"],
    post_commands=["amixer cset numid=3 2"],
    tags=["audio", "hdmi"],
))

_reg(HardwareProfile(
    id="audio_3.5mm",
    name="Audio via 3.5mm Jack",
    category="audio",
    description="Analogue audio output via 3.5mm jack",
    post_commands=["amixer cset numid=3 1"],
    tags=["audio", "jack", "analogue"],
))

_reg(HardwareProfile(
    id="audio_hifiberry_dacplus",
    name="HiFiBerry DAC+",
    category="audio",
    description="HiFiBerry DAC+ high-quality audio HAT",
    overlays=["dtoverlay=hifiberry-dacplus"],
    config_txt_lines=["dtparam=audio=off"],
    tags=["audio", "hifiberry", "dac", "hat"],
))

_reg(HardwareProfile(
    id="audio_i2s_mic",
    name="I2S MEMS Microphone (INMP441)",
    category="audio",
    description="INMP441 I2S MEMS microphone for voice capture",
    overlays=["dtoverlay=googlevoicehat-soundcard"],
    config_txt_lines=["dtparam=i2s=on"],
    packages=["python3-pip"],
    post_commands=["pip3 install sounddevice"],
    tags=["audio", "microphone", "i2s", "inmp441"],
))

# ─────────────────────────────────────────────────────────────────────────────
# NETWORKING
# ─────────────────────────────────────────────────────────────────────────────

_reg(HardwareProfile(
    id="net_can_mcp2515",
    name="CAN Bus MCP2515 SPI",
    category="networking",
    description="MCP2515 CAN bus controller via SPI",
    packages=["can-utils"],
    kernel_modules=["can", "can-dev", "mcp251x"],
    overlays=["dtoverlay=mcp2515-can0,oscillator=8000000,interrupt=25"],
    config_txt_lines=["dtparam=spi=on"],
    post_commands=["ip link set can0 up type can bitrate 500000"],
    config_keys=["CAN_BITRATE"],
    tags=["can", "mcp2515", "spi", "automotive"],
))

_reg(HardwareProfile(
    id="net_rs485",
    name="RS-485 UART HAT",
    category="networking",
    description="RS-485 serial communication via UART",
    packages=["python3-serial"],
    config_txt_lines=[
        "enable_uart=1",
        "dtoverlay=uart0",
    ],
    config_keys=["UART_PORT", "UART_BAUD", "UART_RS485_DIR_PIN"],
    tags=["rs485", "uart", "serial", "modbus"],
))

_reg(HardwareProfile(
    id="net_lora_sx127x",
    name="LoRa SX1276/SX1278 SPI",
    category="networking",
    description="LoRa radio module (SX127x series) via SPI for long-range comms",
    packages=["python3-pip"],
    kernel_modules=["spi-bcm2835"],
    config_txt_lines=["dtparam=spi=on"],
    post_commands=["pip3 install pyLoRa"],
    config_keys=["LORA_FREQ_MHZ", "LORA_SF", "LORA_BW", "LORA_CS_PIN", "LORA_IRQ_PIN"],
    tags=["lora", "spi", "radio", "iot"],
))

_reg(HardwareProfile(
    id="net_nrf24l01",
    name="nRF24L01 2.4GHz Radio SPI",
    category="networking",
    description="nRF24L01 short-range 2.4GHz radio via SPI",
    packages=["python3-pip"],
    kernel_modules=["spi-bcm2835"],
    config_txt_lines=["dtparam=spi=on"],
    post_commands=["pip3 install pyrf24"],
    config_keys=["NRF24_CE_PIN", "NRF24_CSN_PIN", "NRF24_CHANNEL"],
    tags=["nrf24", "spi", "radio", "2.4ghz"],
))

# ─────────────────────────────────────────────────────────────────────────────
# HATs
# ─────────────────────────────────────────────────────────────────────────────

_reg(HardwareProfile(
    id="hat_sense",
    name="Raspberry Pi Sense HAT",
    category="hat",
    description="Official Sense HAT: LED matrix, IMU, environmental sensors",
    packages=["sense-hat", "python3-pip"],
    overlays=["dtoverlay=rpi-sense"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    post_commands=["pip3 install sense-hat"],
    tags=["hat", "sense", "led-matrix", "imu", "official"],
))

_reg(HardwareProfile(
    id="hat_motor_explorer",
    name="Explorer HAT Pro (Motor)",
    category="hat",
    description="Pimoroni Explorer HAT Pro with motor drivers and ADC",
    packages=["python3-pip"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    post_commands=["pip3 install explorerhat"],
    tags=["hat", "motor", "explorer", "pimoroni"],
))

_reg(HardwareProfile(
    id="hat_unicorn",
    name="Pimoroni Unicorn HAT HD",
    category="hat",
    description="16×16 RGB LED matrix HAT",
    packages=["python3-pip"],
    config_txt_lines=["dtparam=spi=on"],
    post_commands=["pip3 install unicornhathd"],
    tags=["hat", "led", "rgb", "matrix", "pimoroni"],
))

_reg(HardwareProfile(
    id="hat_ups_pisugar",
    name="PiSugar UPS HAT",
    category="hat",
    description="PiSugar battery/UPS HAT for portable RPi operation",
    packages=["python3-pip"],
    post_commands=[
        "pip3 install pisugar-server",
        "curl -s https://cdn.pisugar.com/release/pisugar-power-manager.sh | bash",
    ],
    tags=["hat", "ups", "battery", "pisugar"],
))

_reg(HardwareProfile(
    id="hat_rtc_ds3231",
    name="RTC DS3231 HAT",
    category="hat",
    description="Real-time clock module DS3231 via I2C",
    packages=["python3-smbus"],
    kernel_modules=["rtc-ds1307"],
    overlays=["dtoverlay=i2c-rtc,ds3231"],
    config_txt_lines=["dtparam=i2c_arm=on"],
    post_commands=[
        "hwclock --systohc",
        "sed -i 's/^#dtoverlay/dtoverlay/' /boot/config.txt || true",
    ],
    tags=["rtc", "clock", "ds3231", "i2c", "hat"],
))

_reg(HardwareProfile(
    id="hat_poe",
    name="RPi PoE+ HAT",
    category="hat",
    description="Official Power-over-Ethernet HAT with fan control",
    overlays=["dtoverlay=rpi-poe", "dtoverlay=rpi-poe-plus"],
    config_txt_lines=["dtparam=poe_fan_temp0=40000,poe_fan_temp0_hyst=2000"],
    tags=["hat", "poe", "power", "official"],
))

# ─────────────────────────────────────────────────────────────────────────────
# STORAGE
# ─────────────────────────────────────────────────────────────────────────────

_reg(HardwareProfile(
    id="storage_usb_boot",
    name="USB Boot (RPi 4/5)",
    category="storage",
    description="Boot from USB SSD/HDD (disables SD card priority)",
    post_commands=["raspi-config nonint do_boot_order B2"],
    tags=["storage", "usb", "boot", "ssd"],
))

_reg(HardwareProfile(
    id="storage_nfs",
    name="NFS Network Filesystem",
    category="storage",
    description="Mount NFS shares at boot",
    packages=["nfs-common"],
    config_keys=["NFS_SERVER", "NFS_SHARE", "NFS_MOUNT_POINT", "NFS_OPTIONS"],
    post_commands=["systemctl enable nfs-client.target"],
    tags=["storage", "nfs", "network"],
))

_reg(HardwareProfile(
    id="storage_samba",
    name="Samba File Server",
    category="storage",
    description="Samba SMB file sharing server",
    packages=["samba", "samba-common-bin"],
    config_keys=["SAMBA_SHARE_PATH", "SAMBA_SHARE_NAME", "SAMBA_USER"],
    tags=["storage", "samba", "smb", "share"],
))


# ─────────────────────────────────────────────────────────────────────────────
# API
# ─────────────────────────────────────────────────────────────────────────────

def get_profile(profile_id: str) -> HardwareProfile:
    if profile_id not in PROFILES:
        raise KeyError(f"Unknown hardware profile: '{profile_id}'. Use 'meshpi hw list'.")
    return PROFILES[profile_id]


def list_profiles(category: Optional[str] = None, tag: Optional[str] = None) -> list[HardwareProfile]:
    result = list(PROFILES.values())
    if category:
        result = [p for p in result if p.category == category]
    if tag:
        result = [p for p in result if tag in p.tags]
    return sorted(result, key=lambda p: (p.category, p.name))


def categories() -> list[str]:
    return sorted(set(p.category for p in PROFILES.values()))
