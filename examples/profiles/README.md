# 🛠️ Przykładowe Profile Sprzętowe MeshPi

Ta kolekcja zawiera **20 przykładowych profili sprzętowych** gotowych do użycia z MeshPi. Każdy profil jest w pełni skonfigurowany z wszystkimi wymaganymi pakietami, modułami kernela i komendami post-instalacyjnymi.

## 📋 Lista Profili

### 🌡️ **Sensory (4 profile)**

#### [BME280 Weather Station](bme280_weather_station.yaml)
- **Kategoria:** `sensor`
- **Interfejs:** I2C
- **Zastosowanie:** Stacje pogodowe, monitoring środowiskowy
- **Funkcje:** Temperatura, wilgoć, ciśnienie
- **Biblioteki:** adafruit-circuitpython-bme280, matplotlib, pandas

#### [DS18B20 Temperature Array](ds18b20_temperature_array.yaml)
- **Kategoria:** `sensor`
- **Interfejs:** 1-Wire
- **Zastosowanie:** Monitorowanie temperatury w wielu pomieszczeniach
- **Funkcje:** Cyfrowe sensory temperatury
- **Biblioteki:** w1thermsensor, matplotlib, pandas

#### [Industrial Sensor Monitor](industrial_sensor_monitor.yaml)
- **Kategoria:** `sensor`
- **Interfejs:** I2C + Multiple
- **Zastosowanie:** Monitoring przemysłowy, automatyka procesowa
- **Funkcje:** Dashboard web, logging, alerty
- **Biblioteki:** Flask, Plotly, Pandas, Schedule

#### [Voice Assistant with LLM](voice_assistant_llm.yaml)
- **Kategoria:** `ai`
- **Interfejs:** Audio
- **Zastosowanie:** Asystent głosowy z AI, smart home
- **Funkcje:** Rozpoznawanie mowy, LLM, syntezator mowy
- **Biblioteki:** OpenAI Whisper, pyttsx3, LiteLLM

---

### 🖥️ **Wyświetlacze (3 profile)**

#### [OLED SSD1306 Status Display](oled_ssd1306_status_display.yaml)
- **Kategoria:** `display`
- **Interfejs:** I2C
- **Zastosowanie:** Wyświetlacze statusu, monitoring wizualny
- **Funkcje:** 128x64 OLED, grafika, tekst
- **Biblioteki:** adafruit-circuitpython-ssd1306, Pillow, Luma.OLED

#### [Waveshare 4.3" LCD Touchscreen](waveshare_lcd_43_touchscreen.yaml)
- **Kategoria:** `display`
- **Interfejs:** SPI
- **Zastosowanie:** Panele kontrolne, interfejsy dotykowe
- **Funkcje:** 4.3" LCD, touchscreen, X11
- **Biblioteki:** Pygame, Pillow, OpenCV

#### [7" HDMI Touchscreen Display](lcd_7_touchscreen_hdmi.yaml)
- **Kategoria:** `display`
- **Interfejs:** HDMI
- **Zastosowanie:** Tablety, dashboardy, duże interfejsy
- **Funkcje:** 7" LCD, pojemnościowy touchscreen
- **Biblioteki:** Pygame, Kivy, OpenCV

---

### 📷 **Kamery**

#### [Raspberry Pi Camera Vision](rpi_camera_vision.yaml)
- **Kategoria:** `camera`
- **Interfejs:** CSI
- **Zastosowanie:** Computer vision, monitoring, fotografia
- **Funkcje:** Wideo wysokiej rozdzielczości, OpenCV
- **Biblioteki:** OpenCV, Picamera, Matplotlib

---

### 🚗 **Motory (2 profile)**

#### [L298N DC Motor Controller](motor_l298n_controller.yaml)
- **Kategoria:** `motor`
- **Interfejs:** GPIO
- **Zastosowanie:** Robotyka, samochody, łodzie
- **Funkcje:** Kontrola prędkości PWM, zmiana kierunku
- **Biblioteki:** RPi.GPIO, GPIOZero, NumPy

#### [PCA9685 Servo Motor Controller](servo_pca9685_controller.yaml)
- **Kategoria:** `motor`
- **Interfejs:** I2C
- **Zastosowanie:** Robotyka, gimbaly, animatronika
- **Funkcje:** 16-kanałowy PWM, precyzyjne pozycjonowanie
- **Biblioteki:** adafruit-circuitpython-pca9685, ServoKit

---

### 🎛️ **GPIO i Sterowanie (2 profile)**

#### [A4988 Stepper Motor Controller](stepper_a4988_controller.yaml)
- **Kategoria:** `gpio`
- **Interfejs:** GPIO
- **Zastosowanie:** Robotyka, druk 3D, CNC, pozycjonowanie
- **Funkcje:** Precyzyjny sterownik silnika krokowego
- **Biblioteki:** RPi.GPIO, GPIOZero

#### [8-Channel Relay Board](relay_board_8channel.yaml)
- **Kategoria:** `gpio`
- **Interfejs:** GPIO
- **Zastosowanie:** Automatyka domowa, sterowanie mocą
- **Funkcje:** 8-kanałowy sterownik przekaźników
- **Biblioteki:** GPIOZero, Flask, Schedule

---

### 🎵 **Audio**

#### [I2S PCM5102 Audio DAC](i2s_pcm5102_audio_dac.yaml)
- **Kategoria:** `audio`
- **Interfejs:** I2S
- **Zastosowanie:** Audio wysokiej jakości, muzyka
- **Funkcje:** Konwerter cyfrowo-analogowy, ALSA
- **Biblioteki:** PyAudio, SoundDevice, NumPy

---

### 🌐 **Sieć i Komunikacja**

#### [LoRa SX1276 Wireless](lora_sx1276_wireless.yaml)
- **Kategoria:** `networking`
- **Interfejs:** SPI
- **Zastosowanie:** IoT, sieci bezprzewodowe dalekiego zasięgu
- **Funkcje:** Moduł LoRa, komunikacja długodystansowa
- **Biblioteki:** SPIdev, PySerial, Adafruit LoRa

#### [Multi-Network Router](multi_network_router.yaml)
- **Kategoria:** `networking`
- **Interfejs:** Multiple Ethernet
- **Zastosowanie:** Routery, bramy sieciowe, access points
- **Funkcje:** DHCP, firewall, NAT, routing
- **Biblioteki:** Netifaces, PSUtil

---

### 🎮 **Wejścia i Rozrywka**

#### [USB Gamepad Controller](usb_gamepad_controller.yaml)
- **Kategoria:** `input`
- **Interfejs:** USB
- **Zastosowanie:** Gry, robotyka, sterowanie
- **Funkcje:** Kontrolery gier, joysticki
- **Biblioteki:** Pygame, Inputs, Evdev

#### [Retro Gaming Station](retro_gaming_station.yaml)
- **Kategoria:** `entertainment`
- **Interfejs:** Multiple
- **Zastosowanie:** Retro gaming, emulacja
- **Funkcje:** RetroPie, multiple emulatory
- **Biblioteki:** Pygame, RetroArch

---

### 🎩 **HATs (5 profile)**

#### [Raspberry Pi Sense HAT](rpi_sense_hat_complete.yaml)
- **Kategoria:** `hat`
- **Interfejs:** I2C
- **Zastosowanie:** Wszechstrony zestaw sensorów
- **Funkcje:** LED matrix, joystick, multiple sensory
- **Biblioteki:** Sense HAT, Matplotlib, Pillow

#### [PiSugar UPS HAT](pisugar_ups_hat.yaml)
- **Kategoria:** `hat`
- **Interfejs:** I2C
- **Zastosowanie:** Zasilanie awaryjne, przenośne projekty
- **Funkcje:** Monitorowanie baterii, bezpieczne wyłączanie
- **Biblioteki:** PiSugar, ADS1115

#### [Adafruit Fruit HAT](adafruit_fruit_hat.yaml)
- **Kategoria:** `hat`
- **Interfejs:** I2C
- **Zastosowanie:** Interaktywne sensory, wyświetlacze
- **Funkcje:** LED matrix, sensory, dotyk pojemnościowy
- **Biblioteki:** Adafruit CircuitPython, BME280

#### [Pimoroni Explorer HAT](pimoroni_explorer_hat.yaml)
- **Kategoria:** `hat`
- **Interfejs:** I2C + GPIO
- **Zastosowanie:** Robotyka, ekspansja, automatyka
- **Funkcje:** Sterowniki silników, ADC, I/O
- **Biblioteki:** ExplorerHAT, NumPy

#### [Waveshare IoT HAT](waveshare_iot_hat.yaml)
- **Kategoria:** `hat`
- **Interfejs:** I2C + SPI + Serial
- **Zastosowanie:** IoT, tracking, monitoring zdalny
- **Funkcje:** LoRa, GPS, sensory środowiskowe
- **Biblioteki:** Adafruit LoRa, GPS3, SPIdev

---

## 📚 **Standard Documentation**

For complete standardized documentation on device groups and hardware profiles, see:
- **[Standard Documentation](../../docs/STANDARD_DOCUMENTATION.md)** - Groups (devices) ↔ Profiles (OS/drivers)
- **[Easy Profile Management](EASY_PROFILE_MANAGEMENT.md)** - Step-by-step guide
- **[Hardware Group Management](../../docs/HARDWARE-GROUP-MANAGEMENT.md)** - Advanced operations

---

## 📈 **Monitoring Profili**

### 🔍 **Audit Logging**

```bash
# Sprawdź logi instalacji profili
meshpi audit --operation hw-apply

# Filtruj po konkretnym profilu
meshpi audit --filter profile=bme280_weather_station

# Eksportuj logi
meshpi audit --export profile_installation_$(date +%Y%m%d).jsonl
```

### 📊 **Metryki Prometheus**

```bash
# Sprawdź metryki zainstalowanych profili
curl http://localhost:7422/metrics | grep meshpi_hardware_profiles

# Kluczowe metryki profili:
# - meshpi_hardware_profiles_installed_total - liczba zainstalowanych profili
# - meshpi_hardware_profiles_by_category - profile według kategorii
# - meshpi_hardware_profiles_install_duration - czas instalacji
# - meshpi_hardware_profiles_install_success - sukcesy/porażki
```

### 🚨 **Alerting**

```bash
# Sprawdź alerty związane z profilami
meshpi alerts list --category hardware

# Testuj alert instalacji
meshpi alerts test profile-install-failed

# Wycisz alert
meshpi alerts silence profile-install-failed --duration 2h
```

### 📉 **Grafana Dashboards**

Pre-built dashboardy dla monitoringu profili:
- **Hardware Profiles Overview** - status wszystkich profili
- **Profile Installation Metrics** - czasy instalacji, sukcesy
- **Profile Categories** - rozkład profili według kategorii
- **Device Profile Mapping** - które urządzenia mają które profile

---

## 🚀 **Szybki Start**

### 1️⃣ **Wybierz profil:**

```bash
# Przeglądaj profile według kategorii
meshpi hw catalog --category sensor
meshpi hw catalog --category display
meshpi hw catalog --category gpio
```

### 2️⃣ **Importuj profil:**

```bash
# Importuj pojedynczy profil
meshpi hw create --import-file examples/profiles/bme280_weather_station.yaml

# Lub skopiuj do swojego folderu
cp examples/profiles/bme280_weather_station.yaml ~/.meshpi/profiles/my_sensors.yaml
meshpi hw create --import-file ~/.meshpi/profiles/my_sensors.yaml
```

### 3️⃣ **Zastosuj profil:**

```bash
# Zainstaluj profil
meshpi hw apply bme280_weather_station

# Lub zdalnie przez SSH
meshpi ssh hw-apply bme280_weather_station --target pi@192.168.1.100
```

### 4️⃣ **Skonfiguruj monitoring:**

```bash
# Uruchom stack monitoringowy
docker compose --profile monitoring up

# Sprawdź metryki profilu
curl http://localhost:7422/metrics | grep meshpi_hardware_profiles

# Sprawdź logi instalacji
meshpi audit --operation hw-apply

# Monitoruj status urządzeń
meshpi alerts status
```

---

## 📂 **Struktura Profili**

Każdy profil zawiera:

### 🔧 **Wymagane pola:**
- `id` - Unikalny identyfikator
- `name` - Nazwa profilu
- `category` - Kategoria sprzętowa
- `description` - Szczegółowy opis

### 🎯 **Opcjonalne pola:**
- `packages` - Pakiety APT do instalacji
- `kernel_modules` - Moduły kernela do załadowania
- `overlays` - Device tree overlays
- `config_txt_lines` - Linie do `/boot/config.txt`
- `post_commands` - Komendy post-instalacyjne
- `tags` - Tagi do wyszukiwania

---

## 🎨 **Tworzenie Własnych Profili**

### 📝 **Skopiuj i modyfikuj:**

```bash
# Skopiuj istniejący profil jako szablon
cp examples/profiles/bme280_weather_station.yaml my_custom_sensor.yaml

# Edytuj plik
nano my_custom_sensor.yaml

# Importuj i przetestuj
meshpi hw create --import-file my_custom_sensor.yaml
meshpi hw apply my_custom_sensor
```

### 🔧 **Kategorie dostępne:**
- `sensor` - Sensory i czujniki
- `display` - Wyświetlacze
- `gpio` - Układy GPIO
- `camera` - Kamery
- `audio` - Audio
- `networking` - Sieć
- `input` - Urządzenia wejściowe
- `hat` - Raspberry Pi HATs
- `storage` - Pamięć masowa
- `entertainment` - Rozrywka
- `custom` - Własne zastosowania

---

## 🏷️ **Tagi Wyszukiwania**

Popularne tagi do łatwego znajdowania profili:

### 🔍 **Po interfejsie:**
- `i2c`, `spi`, `gpio`, `usb`, `1-wire`, `csi`

### 🔍 **Po zastosowaniu:**
- `sensor`, `display`, `motor`, `camera`, `audio`, `networking`

### 🔍 **Po typie:**
- `temperature`, `humidity`, `pressure`, `stepper`, `relay`, `oled`

---

## 📞 **Wsparcie**

### 🐛 **Problemy:**
```bash
# Sprawdź status instalacji
meshpi hw list-custom

# Diagnostyka sprzętu
meshpi diag

# Testowanie połączenia
i2cdetect -y 1  # dla I2C
ls /dev/spidev*  # dla SPI
```

### 📚 **Dokumentacja:**
- [MeshPi README](../README.md)
- [Hardware Group Management](../docs/HARDWARE-GROUP-MANAGEMENT.md)
- [SSH Hardware Management](../docs/SSH-HARDWARE-MANAGEMENT.md)

---

## ✅ **Podsumowanie**

Te profile pokazują pełną moc MeshPi w zarządzaniu sprzętem Raspberry Pi. Od prostych sensorów po złożone systemy przemysłowe - wszystko gotowe do użycia w kilku komendach!

**Gotowy do użycia? Wybierz profil i zacznij działać! 🚀**
