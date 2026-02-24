# 📋 Standardowa Dokumentacja MeshPi

## 🏗️ **Architektura Systemu**

### 📊 **Hierarchia zarządzania:**

```
GRUPY URZĄDZEŃ ───► PROFILE SPRZĘTOWE ───► INSTALACJA
       │                        │                     │
       ▼                        ▼                     ▼
   Grupy RPi         Konfiguracja OS + Drivers   Pakiety + Moduły
```

---

## 👥 **GRUPY URZĄDZEŃ (Device Groups)**

Grupy urządzeń to **logiczne zbiory Raspberry Pi** o podobnym przeznaczeniu lub lokalizacji.

### 🏗️ **Tworzenie grup:**

```bash
# Grupa sensorów biurowych
meshpi group create office_sensors --description "Temperature sensors in office"

# Grupa wyświetlaczy magazynowych  
meshpi group create warehouse_displays --description "OLED displays in warehouse"

# Grupa sterowników GPIO w laboratorium
meshpi group create lab_gpio --description "GPIO controllers in lab"
```

### 📋 **Dodawanie urządzeń do grup:**

```bash
# Dodaj urządzenia SSH do grupy
meshpi group add-device office_sensors pi@192.168.1.100
meshpi group add-device office_sensors pi@192.168.1.101
meshpi group add-device office_sensors pi@192.168.1.102

# Sprawdź zawartość grupy
meshpi group show office_sensors
```

### 🎯 **Typowe grupy:**

| Grupa | Urządzenia | Przeznaczenie | Profile |
|-------|------------|---------------|----------|
| `office_sensors` | 3-5 RPi | Monitoring biurowy | sensory + wyświetlacze |
| `warehouse_auto` | 2-3 RPi | Automatyka magazynowa | przekaźniki + sensory |
| `lab_gpio` | 1-2 RPi | Laboratorium | sterowniki GPIO |
| `shop_cameras` | 2-4 RPi | Monitoring sklepu | kamery + sieci |
| `home_automation` | 3-6 RPi | Smart home | sensory + audio |

---

## 🛠️ **PROFILE SPRZĘTOWE (Hardware Profiles)**

Profile sprzętowe to **kompletne konfiguracje OS + drivers** dla konkretnego sprzętu.

### 📋 **Struktura profilu:**

```yaml
id: "profile_id"
name: "Profile Name"
category: "hardware_type"
description: "Complete hardware setup"

# === KONFIGURACJA OS ===
packages:                    # Pakiety APT (system operacyjny)
  - "i2c-tools"
  - "python3-pip"
  
kernel_modules:               # Moduły kernela (sterowniki)
  - "i2c-dev"
  - "spi-bcm2835"

overlays:                     # Device tree overlays (konfiguracja sprzętu)
  - "i2c-arm"

config_txt_lines:             # /boot/config.txt (konfiguracja boot)
  - "dtparam=i2c_arm=on"

# === KONFIGURACJA APLIKACJI ===
post_commands:                # Komendy post-instalacyjne (biblioteki, uprawnienia)
  - "pip3 install adafruit-circuitpython-bme280"
  - "usermod -a -G i2c $USER"

tags:                         # Tagi wyszukiwania
  - "i2c"
  - "sensor"
```

---

## 📂 **Katalog Profili Sprzętowych**

### 🌡️ **SENSORY (OS + Drivers)**

#### **BME280 Weather Station**
- **OS Pakiety:** `i2c-tools`, `python3-smbus`, `python3-dev`
- **Kernel Modules:** `i2c-dev`, `i2c-bcm2708`
- **Device Tree:** `i2c-arm`
- **Boot Config:** `dtparam=i2c_arm=on`
- **Aplikacje:** `adafruit-circuitpython-bme280`, `matplotlib`, `pandas`
- **Uprawnienia:** `i2c` group

#### **DS18B20 Temperature Array**
- **OS Pakiety:** `python3-ow`, `ow-shell`, `w1thermsensor`
- **Kernel Modules:** `w1-gpio`, `w1-therm`
- **Device Tree:** `w1-gpio`, `w1-gpio-pullup`
- **Boot Config:** `dtoverlay=w1-gpio`
- **Aplikacje:** `w1thermsensor`, `matplotlib`

#### **Voice Assistant with LLM**
- **OS Pakiety:** `portaudio19-dev`, `ffmpeg`, `alsa-utils`
- **Kernel Modules:** `snd_bcm2835`, `snd_pcm_oss`
- **Device Tree:** `audio`
- **Boot Config:** `dtparam=audio=on`
- **Aplikacje:** `openai-whisper`, `pyttsx3`, `litellm`
- **Uprawnienia:** `audio` group

---

### 🖥️ **WYŚWIETLACZE (OS + Drivers)**

#### **OLED SSD1306 Status Display**
- **OS Pakiety:** `i2c-tools`, `python3-pil`, `libjpeg-dev`
- **Kernel Modules:** `i2c-dev`, `i2c-bcm2708`
- **Device Tree:** `i2c-arm`
- **Boot Config:** `dtparam=i2c_arm=on`
- **Aplikacje:** `adafruit-circuitpython-ssd1306`, `pillow`, `luma-oled`

#### **Waveshare 4.3" LCD Touchscreen**
- **OS Pakiety:** `xserver-xorg`, `xinput`, `x11-xserver-utils`
- **Kernel Modules:** `fbtft_device`, `fbtft`
- **Device Tree:** `spi0-cs`, `waveshare43`
- **Boot Config:** `dtparam=spi=on`, `dtoverlay=waveshare43`
- **Aplikacje:** `pygame`, `pillow`, `opencv-python`

#### **7" HDMI Touchscreen Display**
- **OS Pakiety:** `xserver-xorg`, `libinput-tools`, `xcalib`
- **Kernel Modules:** (brak - HDMI)
- **Device Tree:** (brak - HDMI)
- **Boot Config:** `hdmi_force_hotplug=1`, `hdmi_group=2`
- **Aplikacje:** `pygame`, `kivy`, `opencv-python`

---

### 🚗 **MOTORY (OS + Drivers)**

#### **L298N DC Motor Controller**
- **OS Pakiety:** `python3-gpiozero`, `python3-numpy`
- **Kernel Modules:** (brak - GPIO)
- **Device Tree:** (brak - GPIO)
- **Boot Config:** `gpio=24,25,23,22=a0`
- **Aplikacje:** `RPi.GPIO`, `gpiozero`, `numpy`
- **Uprawnienia:** `gpio` group

#### **PCA9685 Servo Motor Controller**
- **OS Pakiety:** `python3-smbus`, `i2c-tools`
- **Kernel Modules:** `i2c-dev`, `i2c-bcm2708`
- **Device Tree:** `i2c-arm`
- **Boot Config:** `dtparam=i2c_arm=on`
- **Aplikacje:** `adafruit-circuitpython-pca9685`, `servokit`
- **Uprawnienia:** `i2c`, `gpio` groups

---

### 🎩 **HATs (OS + Drivers)**

#### **Raspberry Pi Sense HAT**
- **OS Pakiety:** `sense-hat`, `python3-sense-emu`, `python3-numpy`
- **Kernel Modules:** `i2c-dev`, `i2c-bcm2708`
- **Device Tree:** `i2c-arm`
- **Boot Config:** `dtparam=i2c_arm=on`
- **Aplikacje:** `sense-hat`, `matplotlib`, `pillow`

#### **PiSugar UPS HAT**
- **OS Pakiety:** `i2c-tools`, `python3-smbus`, `git`
- **Kernel Modules:** `i2c-dev`, `i2c-bcm2708`
- **Device Tree:** `i2c-arm`
- **Boot Config:** `dtparam=i2c_arm=on`
- **Aplikacje:** `pisugar`, `adafruit-circuitpython-ads1115`
- **Serwisy:** `pisugar-server`

#### **Waveshare IoT HAT**
- **OS Pakiety:** `gpsd`, `gpsd-clients`, `python3-serial`
- **Kernel Modules:** `i2c-dev`, `spi-bcm2835`, `spidev`
- **Device Tree:** `i2c-arm`, `spi0-cs`
- **Boot Config:** `dtparam=i2c_arm=on`, `dtparam=spi=on`
- **Aplikacje:** `adafruit-circuitpython-lora`, `gps3`, `spidev`
- **Serwisy:** `gpsd`

---

## 🔄 **Przepływ Pracy: Grupy → Profile → Instalacja**

### 📋 **Krok 1: Zdefiniuj grupę urządzeń**

```bash
# Stwórz grupę dla stacji pogodowej
meshpi group create weather_stations --description "Environmental monitoring stations"
```

### 📋 **Krok 2: Dodaj urządzenia do grupy**

```bash
# Dodaj Raspberry Pi do grupy
meshpi group add-device weather_stations pi@192.168.1.100
meshpi group add-device weather_stations pi@192.168.1.101
meshpi group add-device weather_stations pi@192.168.1.102
```

### 📋 **Krok 3: Wybierz profile sprzętowe**

```bash
# Przeglądaj dostępne profile
meshpi hw catalog --category sensor
meshpi hw catalog --category display

# Wybierz profile dla stacji pogodowej
# - sensory: bme280_weather_station
# - wyświetlacze: oled_ssd1306_status_display
```

### 📋 **Krok 4: Zastosuj profile na grupie**

```bash
# Zainstaluj profile na wszystkich urządzeniach w grupie
meshpi group hw-apply weather_stations bme280_weather_station oled_ssd1306_status_display

# Lub interaktywnie
meshpi group hw-apply weather_stations --interactive
```

### 📋 **Krok 5: Zweryfikuj instalację**

```bash
# Sprawdź status na wszystkich urządzeniach
meshpi group exec weather_stations "meshpi diag"

# Sprawdź zainstalowane profile
meshpi group exec weather_stations "meshpi hw list"
```

### 📋 **Krok 6: Skonfiguruj monitoring**

```bash
# Uruchom stack monitoringowy
docker compose --profile monitoring up

# Sprawdź audit log
meshpi audit

# Sprawdź status alertów
meshpi alerts status

# Monitoruj metryki
curl http://localhost:7422/metrics

# Dostęp do dashboardów
open http://localhost:7422/metrics    # Prometheus metrics
open http://localhost:9090            # Prometheus UI
open http://localhost:3000            # Grafana (admin/meshpi)
```

---

## 📈 **Monitoring i Obserwowalność**

MeshPi zawiera wbudowany system monitoringu z metrykami Prometheus, alertowaniem i logowaniem audytu.

### 🔍 **Audit Logging**

```bash
# Przeglądaj logi audytu
meshpi audit

# Filtruj logi po urządzeniu
meshpi audit --device rpi-001

# Filtruj po operacji
meshpi audit --operation hw-apply

# Eksportuj logi
meshpi audit --export audit_$(date +%Y%m%d).jsonl
```

### 🚨 **Alert Engine**

```bash
# Sprawdź status alertów
meshpi alerts status

# Lista reguł alertów
meshpi alerts list

# Testuj alert
meshpi alerts test temperature-high

# Wycisz alert
meshpi alerts silence temperature-high --duration 1h
```

### 📊 **Metryki Prometheus**

```bash
# Pobierz metryki
curl http://localhost:7422/metrics

# Kluczowe metryki:
# - meshpi_devices_total - liczba urządzeń
# - meshpi_device_online - status urządzeń (0/1)
# - meshpi_cpu_usage - użycie CPU
# - meshpi_memory_usage - użycie pamięci
# - meshpi_temperature_celsius - temperatura
# - meshpi_hardware_profiles_installed - zainstalowane profile
```

### 🔄 **OTA Updates**

```bash
# Wypchnij aktualizację
meshpi ota push --image ./image.img --devices rpi-001,rpi-002

# Sprawdź status aktualizacji
meshpi ota status

# Przywróć poprzednią wersję
meshpi ota rollback --device rpi-001
```

### 🐳 **Docker Monitoring Stack**

```bash
# Uruchom z monitoringiem
docker compose --profile monitoring up

# Dostęp do usług
open http://localhost:7422/metrics    # Prometheus metrics
open http://localhost:9090            # Prometheus UI
open http://localhost:3000            # Grafana (admin/meshpi)

# Tylko monitoring
docker compose --profile monitoring up prometheus grafana
```

### 📉 **Grafana Dashboards**

Pre-built dashboardy dla:
- **MeshPi Overview** - status floty, metryki systemowe
- **Device Details** - szczegóły pojedynczego urządzenia
- **Hardware Profiles** - status zainstalowanych profili
- **Alert History** - historia alertów i zdarzeń

---

## 🎯 **Przykłady Konfiguracji**

### 🏢 **Scenariusz: Biuro - Monitoring Środowiskowy**

```bash
# === GRUPA ===
meshpi group create office_env --description "Office environmental monitoring"

# === URZĄDZENIA ===
meshpi group add-device office_env pi@192.168.1.100  # Salon
meshpi group add-device office_env pi@192.168.1.101  # Sypialnia
meshpi group add-device office_env pi@192.168.1.102  # Kuchnia

# === PROFILE ===
meshpi group hw-apply office_env bme280_weather_station oled_ssd1306_status_display

# === WYNIK ===
# Każde RPi w grupie ma:
# - OS: pakiety i2c-tools, python3-smbus
# - Drivers: i2c-dev kernel module
# - Hardware: BME280 sensor + OLED display
# - Aplikacje: biblioteki Python, uprawnienia i2c
```

### 🏭 **Scenariusz: Magazyn - Automatyka Przemysłowa**

```bash
# === GRUPA ===
meshpi group create warehouse_auto --description "Warehouse automation systems"

# === URZĄDZENIA ===
meshpi group add-device warehouse_auto pi@192.168.1.200  # Sterownik 1
meshpi group add-device warehouse_auto pi@192.168.1.201  # Sterownik 2

# === PROFILE ===
meshpi group hw-apply warehouse_auto relay_board_8channel industrial_sensor_monitor

# === WYNIK ===
# Każde RPi w grupie ma:
# - OS: nginx, sqlite3, python3-pip
# - Drivers: i2c-dev kernel module
# - Hardware: 8-channel relay + industrial sensors
# - Aplikacje: Flask dashboard, monitoring, alerty
```

### 🏠 **Scenariusz: Smart Home - Kompleksowy System**

```bash
# === GRUPY ===
meshpi group create home_sensors --description "Home environmental sensors"
meshpi group create home_displays --description "Home status displays"
meshpi group create home_control --description "Home automation controllers"
meshpi group create home_ai --description "AI voice assistants"

# === URZĄDZENIA ===
meshpi group add-device home_sensors pi@192.168.1.10   # Salon sensor
meshpi group add-device home_displays pi@192.168.1.20   # Kuchnia display
meshpi group add-device home_control pi@192.168.1.30   # Centrala sterowania
meshpi group add-device home_ai pi@192.168.1.40        # Asystent głosowy

# === PROFILE ===
meshpi group hw-apply home_sensors bme280_weather_station
meshpi group hw-apply home_displays waveshare_lcd_43_touchscreen
meshpi group hw-apply home_control relay_board_8channel
meshpi group hw-apply home_ai voice_assistant_llm

# === WYNIK ===
# Każda grupa ma specjalizowane profile:
# - Sensors: BME280 z monitoringiem środowiskowym
# - Displays: 4.3" LCD z interfejsem dotykowym
# - Control: 8-channel relay z automatyką
# - AI: Voice assistant z LLM integration
```

---

## 📊 **Standardowe Kategorie Profili**

| Kategoria | Profile | OS Komponenty | Hardware | Zastosowanie |
|-----------|---------|---------------|----------|--------------|
| **sensor** | 4 profile | i2c-tools, python3-smbus | Sensory I2C/1-Wire | Monitoring środowiskowy |
| **display** | 3 profile | xserver-xorg, pygame | Wyświetlacze LCD/OLED | Dashboardy, interfejsy |
| **motor** | 2 profile | python3-gpiozero | Silniki DC/Servo | Robotyka, automatyka |
| **gpio** | 2 profile | python3-gpiozero | Przekaźniki, sterowniki | Sterowanie przemysłowe |
| **hat** | 5 profile | sense-hat, gpsd | Kompletne HATs | Wszechstronne zastosowania |
| **camera** | 1 profil | python3-picamera | Kamery CSI | Computer vision |
| **audio** | 1 profil | alsa-utils, portaudio | Audio I2S/USB | Systemy audio |
| **networking** | 2 profile | dnsmasq, hostapd | Sieć, LoRa | Routing, IoT |
| **input** | 1 profil | joystick, python3-evdev | USB gamepads | Gry, sterowanie |
| **ai** | 1 profil | ffmpeg, portaudio19-dev | Mikrofon, głośnik | Voice assistants |

---

## 🔧 **Standardowe Komendy**

### 👥 **Zarządzanie grupami:**
```bash
meshpi group create [name] --description "desc"
meshpi group add-device [group] pi@IP
meshpi group list
meshpi group show [group]
```

### 🛠️ **Zarządzanie profilami:**
```bash
meshpi hw catalog --category [type]
meshpi hw list --tag [tag]
meshpi hw show [profile_id]
meshpi hw create --import-file [file.yaml]
```

### 🔄 **Instalacja na grupach:**
```bash
meshpi group hw-apply [group] [profile1] [profile2]
meshpi group hw-apply [group] --interactive
meshpi group exec [group] "meshpi diag"
```

---

## ✅ **Standardowe Dobrze Praktyki**

### 🏗️ **Organizacja grup:**
- **Logiczne nazwy:** `office_sensors`, `warehouse_auto`, `lab_gpio`
- **Opisy:** Zawsze dodawaj opisy dla jasności
- **Spójność:** Grupuj urządzenia o podobnym przeznaczeniu

### 🛠️ **Wybór profili:**
- **Testowanie:** Najpierw testuj na jednym urządzeniu
- **Kompatybilność:** Sprawdź kompatybilność sprzętu
- **Zależności:** Uwzględnij zależności między profilami

### 🔄 **Proces instalacji:**
1. **Planowanie:** Zdefiniuj grupy i wybierz profile
2. **Testowanie:** Przetestuj na pojedynczym urządzeniu
3. **Instalacja:** Zastosuj na całej grupie
4. **Weryfikacja:** Sprawdź status i działanie
5. **Monitoring:** Ustaw regularne sprawdzanie

---

## 📝 **Podsumowanie Standardów**

**GRUPY URZĄDZEŃ** = Logiczne zbiory Raspberry Pi  
**PROFILE SPRZĘTOWE** = Kompletna konfiguracja OS + drivers  
**INSTALACJA** = Aplikacja profili na grupach urządzeń

Ten standard zapewnia spójność, powtarzalność i łatwość zarządzania dużymi wdrożeniami MeshPi.
