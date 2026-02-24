# 📋 Standardy MeshPi - Tabela Referencyjna

## 🏗️ **Architektura Standardowa**

```
GRUPY URZĄDZEŃ ───► PROFILE SPRZĘTOWE ───► INSTALACJA
       │                        │                     │
       ▼                        ▼                     ▼
   Logiczne zbiory      Konfiguracja OS + Drivers   Pakiety + Moduły
   Raspberry Pi         (hardware + software)       (aplikacje)
```

---

## 👥 **GRUPY URZĄDZEŃ (Device Groups)**

| Grupa | Opis | Typowe Urządzenia | Przykładowe Profile |
|-------|------|------------------|-------------------|
| `office_sensors` | Monitoring biurowy | 3-5 RPi | sensory + wyświetlacze |
| `warehouse_auto` | Automatyka magazynowa | 2-3 RPi | przekaźniki + sensory |
| `lab_gpio` | Laboratorium | 1-2 RPi | sterowniki GPIO |
| `shop_cameras` | Monitoring sklepu | 2-4 RPi | kamery + sieci |
| `home_automation` | Smart home | 3-6 RPi | sensory + audio |

### 📋 **Standardowe komendy grup:**
```bash
meshpi group create [name] --description "desc"
meshpi group add-device [group] pi@IP
meshpi group list
meshpi group show [group]
```

---

## 🛠️ **PROFILE SPRZĘTOWE (Hardware Profiles)**

### 📋 **Struktura standardowa profilu:**

```yaml
id: "profile_id"
name: "Profile Name"
category: "hardware_type"
description: "Complete hardware setup"

# === KONFIGURACJA OS ===
packages:                    # Pakiety APT (system operacyjny)
kernel_modules:               # Moduły kernela (sterowniki)
overlays:                     # Device tree overlays (konfiguracja sprzętu)
config_txt_lines:             # /boot/config.txt (konfiguracja boot)

# === KONFIGURACJA APLIKACJI ===
post_commands:                # Komendy post-instalacyjne (biblioteki, uprawnienia)
tags:                         # Tagi wyszukiwania
```

---

## 📂 **Standardowe Profile według Kategorii**

### 🌡️ **SENSORY (4 profile)**
| Profil | OS Pakiety | Kernel Modules | Hardware | Aplikacje |
|--------|------------|-----------------|----------|-----------|
| `bme280_weather_station` | i2c-tools, python3-smbus | i2c-dev | BME280 sensor | adafruit-bme280 |
| `ds18b20_temperature_array` | python3-ow, w1thermsensor | w1-gpio, w1-therm | DS18B20 sensors | w1thermsensor |
| `industrial_sensor_monitor` | nginx, sqlite3 | i2c-dev | Industrial sensors | Flask, Plotly |
| `voice_assistant_llm` | ffmpeg, portaudio19-dev | snd_bcm2835 | Mikrofon + głośnik | OpenAI Whisper, LLM |

### 🖥️ **WYŚWIETLACZE (3 profile)**
| Profil | OS Pakiety | Kernel Modules | Hardware | Aplikacje |
|--------|------------|-----------------|----------|-----------|
| `oled_ssd1306_status_display` | i2c-tools, python3-pil | i2c-dev | OLED 128x64 | adafruit-ssd1306 |
| `waveshare_lcd_43_touchscreen` | xserver-xorg, xinput | fbtft_device | 4.3" LCD SPI | Pygame, OpenCV |
| `lcd_7_touchscreen_hdmi` | xserver-xorg, libinput-tools | (brak) | 7" LCD HDMI | Pygame, Kivy |

### 🚗 **MOTORY (2 profile)**
| Profil | OS Pakiety | Kernel Modules | Hardware | Aplikacje |
|--------|------------|-----------------|----------|-----------|
| `motor_l298n_controller` | python3-gpiozero | (brak) | L298N H-bridge | RPi.GPIO |
| `servo_pca9685_controller` | python3-smbus | i2c-dev | PCA9685 PWM | adafruit-pca9685 |

### 🎩 **HATs (5 profile)**
| Profil | OS Pakiety | Kernel Modules | Hardware | Aplikacje |
|--------|------------|-----------------|----------|-----------|
| `rpi_sense_hat_complete` | sense-hat, python3-numpy | i2c-dev | Sense HAT | sense-hat |
| `pisugar_ups_hat` | i2c-tools, python3-smbus | i2c-dev | PiSugar UPS | pisugar |
| `adafruit_fruit_hat` | python3-numpy | i2c-dev | Adafruit Fruit | adafruit-circuitpython |
| `pimoroni_explorer_hat` | python3-numpy | i2c-dev | Explorer HAT | explorerhat |
| `waveshare_iot_hat` | gpsd, python3-serial | i2c-dev, spi-bcm2835 | IoT HAT | adafruit-lora, gps3 |

---

## 🔄 **Standardowy Przepływ Pracy**

### 📋 **Krok 1: Planowanie**
```bash
# Zdefiniuj grupę urządzeń
meshpi group create office_sensors --description "Office environmental monitoring"
```

### 📋 **Krok 2: Konfiguracja**
```bash
# Dodaj urządzenia do grupy
meshpi group add-device office_sensors pi@192.168.1.100
meshpi group add-device office_sensors pi@192.168.1.101
```

### 📋 **Krok 3: Wybór profili**
```bash
# Przeglądaj dostępne profile
meshpi hw catalog --category sensor
meshpi hw catalog --category display
```

### 📋 **Krok 4: Instalacja**
```bash
# Zastosuj profile na grupie
meshpi group hw-apply office_sensors bme280_weather_station oled_ssd1306_status_display
```

### 📋 **Krok 5: Weryfikacja**
```bash
# Sprawdź status
meshpi group exec office_sensors "meshpi diag"
```

---

## 🎯 **Standardowe Scenariusze**

### 🏢 **Biuro - Monitoring Środowiskowy**
```
GRUPA: office_sensors (3 RPi)
PROFILE: bme280_weather_station + oled_ssd1306_status_display
WYNIK: Każde RPi ma sensor BME280 + wyświetlacz OLED
```

### 🏭 **Magazyn - Automatyka Przemysłowa**
```
GRUPA: warehouse_auto (2 RPi)
PROFILE: relay_board_8channel + industrial_sensor_monitor
WYNIK: Każde RPi ma 8-przekaźnikowy sterownik + sensory przemysłowe
```

### 🏠 **Smart Home - Kompleksowy System**
```
GRUPY: home_sensors, home_displays, home_control, home_ai
PROFILE: sensory + LCD + przekaźniki + voice assistant
WYNIK: Rozproszone systemy z różnymi specjalizacjami
```

---

## 📊 **Standardowe Komendy**

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

- **GRUPY URZĄDZEŃ** = Logiczne zbiory Raspberry Pi
- **PROFILE SPRZĘTOWE** = Kompletna konfiguracja OS + drivers
- **INSTALACJA** = Aplikacja profili na grupach urządzeń
- **DOKUMENTACJA** = Spójne, powtarzalne procedury

Ten standard zapewnia spójność, powtarzalność i łatwość zarządzania dużymi wdrożeniami MeshPi.
