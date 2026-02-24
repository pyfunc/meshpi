# 🚀 MeshPi - Kompletny Przewodnik Wdrożenia

## 📋 **Spis Treści**

1. [🏗️ Architektura Systemu](#-architektura-systemu)
2. [👥 Zarządzanie Grupami Urządzeń](#-zarządzanie-grupami-urządzeń)
3. [🛠️ Profile Sprzętowe](#️-profile-sprzętowe)
4. [📈 Monitoring i Obserwowalność](#-monitoring-i-obserwowalność)
5. [🔄 Proces Wdrożenia](#-proces-wdrożenia)
6. [🎯 Przykłady Zastosowań](#-przykłady-zastosowań)
7. [📚 Referencje Komend](#-referencje-komend)
8. [✅ Najlepsze Praktyki](#-najlepsze-praktyki)

---

## 🏗️ **Architektura Systemu**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GRUPY RPi     │───▶│   PROFILE HW    │───▶│   INSTALACJA    │
│                 │    │                 │    │                 │
│ • office_sensors│    │ • OS + Drivers  │    │ • Pakiety       │
│ • warehouse_auto│    │ • Biblioteki    │    │ • Moduły        │
│ • lab_gpio      │    │ • Konfiguracja  │    │ • Uprawnienia   │
│ • home_automation│   │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LOGIKA        │    │   KONFIGURACJA  │    │   MONITORING    │
│                 │    │                 │    │                 │
│ • Logiczne      │    │ • YAML profiles │    │ • Prometheus    │
│ • Zbiory        │    │ • Kategorie     │    │ • Grafana       │
│ • Przeznaczenie │    │ • Tagi          │    │ • Alerting      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 👥 **Zarządzanie Grupami Urządzeń**

### 🏗️ **Tworzenie grup**

```bash
# Grupa sensorów biurowych
meshpi group create office_sensors \
  --description "Temperature sensors in office"

# Grupa wyświetlaczy magazynowych
meshpi group create warehouse_displays \
  --description "OLED displays in warehouse"

# Grupa sterowników GPIO w laboratorium
meshpi group create lab_gpio \
  --description "GPIO controllers in lab"
```

### 📋 **Dodawanie urządzeń**

```bash
# Dodaj urządzenia SSH do grupy
meshpi group add-device office_sensors pi@192.168.1.100
meshpi group add-device office_sensors pi@192.168.1.101
meshpi group add-device office_sensors pi@192.168.1.102

# Sprawdź zawartość grupy
meshpi group show office_sensors

# Lista wszystkich grup
meshpi group list
```

### 🎯 **Standardowe grupy**

| Nazwa grupy | Przeznaczenie | Typowa liczba RPi | Przykładowe profile |
|-------------|---------------|-------------------|-------------------|
| `office_sensors` | Monitoring biurowy | 3-5 | sensory + wyświetlacze |
| `warehouse_auto` | Automatyka magazynowa | 2-3 | przekaźniki + sensory |
| `lab_gpio` | Laboratorium | 1-2 | sterowniki GPIO |
| `shop_cameras` | Monitoring sklepu | 2-4 | kamery + sieci |
| `home_automation` | Smart home | 3-6 | sensory + audio |

---

## 🛠️ **Profile Sprzętowe**

### 📋 **Struktura profilu**

```yaml
id: "profile_id"
name: "Profile Name"
category: "hardware_type"
description: "Complete hardware setup"

# === KONFIGURACJA OS ===
packages:                    # Pakiety APT
  - "i2c-tools"
  - "python3-pip"
  
kernel_modules:               # Moduły kernela
  - "i2c-dev"
  - "spi-bcm2835"

overlays:                     # Device tree overlays
  - "i2c-arm"

config_txt_lines:             # /boot/config.txt
  - "dtparam=i2c_arm=on"

# === KONFIGURACJA APLIKACJI ===
post_commands:                # Biblioteki, uprawnienia
  - "pip3 install adafruit-circuitpython-bme280"
  - "usermod -a -G i2c $USER"

tags:                         # Tagi wyszukiwania
  - "i2c"
  - "sensor"
```

### 📂 **Katalog profili (20 profile)**

#### 🌡️ **SENSORY (4 profile)**
- **BME280 Weather Station** - stacja pogodowa I2C
- **DS18B20 Temperature Array** - tablica czujników 1-Wire
- **Industrial Sensor Monitor** - monitoring przemysłowy
- **Voice Assistant with LLM** - asystent głosowy z AI

#### 🖥️ **WYŚWIETLACZE (3 profile)**
- **OLED SSD1306 Status Display** - 128x64 OLED I2C
- **Waveshare 4.3" LCD Touchscreen** - SPI + touchscreen
- **7" HDMI Touchscreen Display** - HDMI + pojemnościowy

#### 🚗 **MOTORY (2 profile)**
- **L298N DC Motor Controller** - sterownik silników DC z PWM
- **PCA9685 Servo Motor Controller** - 16-kanałowy PWM servo

#### 🎩 **HATs (5 profile)**
- **Raspberry Pi Sense HAT** - oficjalny HAT z sensorami
- **PiSugar UPS HAT** - zasilanie awaryjne
- **Adafruit Fruit HAT** - sensory + LED matrix
- **Pimoroni Explorer HAT** - sterowniki + ADC
- **Waveshare IoT HAT** - LoRa + GPS + sensory

---

## 📈 **Monitoring i Obserwowalność**

### 🔍 **Audit Logging**

```bash
# Przeglądaj logi audytu
meshpi audit

# Filtruj logi
meshpi audit --device rpi-001
meshpi audit --operation hw-apply
meshpi audit --export audit_20260224.jsonl
```

### 🚨 **Alert Engine**

```bash
# Status alertów
meshpi alerts status

# Lista reguł
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

### 🐳 **Docker Monitoring Stack**

```bash
# Uruchom z monitoringiem
docker compose --profile monitoring up

# Dostęp do usług
open http://localhost:7422/metrics    # Prometheus metrics
open http://localhost:9090            # Prometheus UI
open http://localhost:3000            # Grafana (admin/meshpi)
```

---

## 🔄 **Proces Wdrożenia**

### 📋 **Krok 1: Planowanie**

```bash
# Zdefiniuj grupy urządzeń
meshpi group create office_env --description "Office environmental monitoring"
meshpi group create warehouse_auto --description "Warehouse automation systems"
meshpi group create lab_gpio --description "Laboratory GPIO controllers"
```

### 📋 **Krok 2: Konfiguracja**

```bash
# Dodaj urządzenia do grup
meshpi group add-device office_env pi@192.168.1.100
meshpi group add-device office_env pi@192.168.1.101
meshpi group add-device warehouse_auto pi@192.168.1.200
meshpi group add-device lab_gpio pi@192.168.1.300
```

### 📋 **Krok 3: Wybór profili**

```bash
# Przeglądaj dostępne profile
meshpi hw catalog --category sensor
meshpi hw catalog --category display
meshpi hw catalog --category motor

# Sprawdź szczegóły profilu
meshpi hw show bme280_weather_station
```

### 📋 **Krok 4: Instalacja**

```bash
# Zastosuj profile na grupach
meshpi group hw-apply office_env bme280_weather_station oled_ssd1306_status_display
meshpi group hw-apply warehouse_auto relay_board_8channel industrial_sensor_monitor
meshpi group hw-apply lab_gpio stepper_a4988_controller

# Lub interaktywnie
meshpi group hw-apply office_env --interactive
```

### 📋 **Krok 5: Weryfikacja**

```bash
# Sprawdź status na wszystkich urządzeniach
meshpi group exec office_env "meshpi diag"
meshpi group exec warehouse_auto "meshpi hw list"
meshpi group exec lab_gpio "uptime"
```

### 📋 **Krok 6: Monitoring**

```bash
# Uruchom stack monitoringowy
docker compose --profile monitoring up

# Sprawdź logi i alerty
meshpi audit
meshpi alerts status

# Monitoruj metryki
curl http://localhost:7422/metrics
```

---

## 🎯 **Przykłady Zastosowań**

### 🏢 **Scenariusz 1: Biuro - Monitoring Środowiskowy**

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
# - OS: i2c-tools, python3-smbus
# - Drivers: i2c-dev kernel module
# - Hardware: BME280 sensor + OLED display
# - Aplikacje: biblioteki Python, uprawnienia i2c
```

### 🏭 **Scenariusz 2: Magazyn - Automatyka Przemysłowa**

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

### 🏠 **Scenariusz 3: Smart Home - Kompleksowy System**

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

# === MONITORING ===
docker compose --profile monitoring up
meshpi audit
meshpi alerts status
```

---

## 📚 **Referencje Komend**

### 👥 **Zarządzanie grupami:**
```bash
meshpi group create [name] --description "desc"
meshpi group add-device [group] pi@IP
meshpi group list
meshpi group show [group]
meshpi group exec [group] "command"
```

### 🛠️ **Zarządzanie profilami:**
```bash
meshpi hw catalog --category [type]
meshpi hw list --tag [tag]
meshpi hw show [profile_id]
meshpi hw create --import-file [file.yaml]
meshpi hw apply [profile_id]
```

### 🔄 **Instalacja na grupach:**
```bash
meshpi group hw-apply [group] [profile1] [profile2]
meshpi group hw-apply [group] --interactive
meshpi group exec [group] "meshpi diag"
```

### 📈 **Monitoring:**
```bash
# Audit logging
meshpi audit
meshpi audit --device rpi-001
meshpi audit --export audit_20260224.jsonl

# Alert engine
meshpi alerts status
meshpi alerts list
meshpi alerts test temperature-high
meshpi alerts silence temperature-high --duration 1h

# Metryki
curl http://localhost:7422/metrics

# OTA updates
meshpi ota push --image ./image.img --devices rpi-001,rpi-002
meshpi ota status
meshpi ota rollback --device rpi-001
```

---

## ✅ **Najlepsze Praktyki**

### 🏗️ **Organizacja grup:**
- **Logiczne nazwy:** `office_sensors`, `warehouse_auto`, `lab_gpio`
- **Opisy:** Zawsze dodawaj opisy dla jasności
- **Spójność:** Grupuj urządzenia o podobnym przeznaczeniu
- **Skalowalność:** Planuj przyszłe rozszerzenia

### 🛠️ **Wybór profili:**
- **Testowanie:** Najpierw testuj na jednym urządzeniu
- **Kompatybilność:** Sprawdź kompatybilność sprzętu
- **Zależności:** Uwzględnij zależności między profilami
- **Wersjonowanie:** Trzymaj spis zainstalowanych profili

### 🔄 **Proces instalacji:**
1. **Planowanie:** Zdefiniuj grupy i wybierz profile
2. **Testowanie:** Przetestuj na pojedynczym urządzeniu
3. **Instalacja:** Zastosuj na całej grupie
4. **Weryfikacja:** Sprawdź status i działanie
5. **Monitoring:** Ustaw regularne sprawdzanie, alerty i metryki
6. **Audyt:** Przeglądaj logi operacji i zdarzeń

### 📈 **Konfiguracja monitoringu:**
- **Prometheus:** Zbieraj metryki systemowe i aplikacyjne
- **Grafana:** Twórz dashboardy dla wizualizacji
- **Alerting:** Skonfiguruj reguły alertów dla kluczowych metryk
- **Audit logging:** Włącz logowanie wszystkich operacji
- **OTA updates:** Przygotuj proces aktualizacji firmware

### 🔒 **Bezpieczeństwo:**
- **SSH keys:** Używaj kluczy SSH zamiast haseł
- **Uprawnienia:** Minimalizuj uprawnienia użytkowników
- **Sieć:** Ogranicz dostęp do niezbędnych portów
- **Backup:** Regularnie backupuj konfiguracje i logi

---

## 📝 **Podsumowanie**

MeshPi zapewnia kompletny system zarządzania flotą Raspberry Pi z:

- **👥 Grupami urządzeń** - logiczne zbiory RPi
- **🛠️ Profilami sprzętowymi** - kompletna konfiguracja OS + drivers
- **📈 Monitoringiem** - Prometheus + Grafana + Alerting + Audit
- **🔄 Automatyzacją** - zdalna instalacja i zarządzanie
- **📚 Dokumentacją** - spójne, powtarzalne procedury

Ten standard zapewnia spójność, powtarzalność i łatwość zarządzania dużymi wdrożeniami MeshPi z pełną obserwowalnością.

---

## 🔗 **Dodatkowe zasoby**

- **[Standard Documentation](docs/STANDARD_DOCUMENTATION.md)** - Szczegółowe standardy
- **[Standards Table](docs/STANDARDS_TABLE.md)** - Tabela referencyjna
- **[Hardware Group Management](docs/HARDWARE-GROUP-MANAGEMENT.md)** - Zaawansowane operacje
- **[SSH Hardware Management](docs/SSH-HARDWARE-MANAGEMENT.md)** - Zarządzanie zdalne
- **[Example Profiles](examples/profiles/)** - 20 gotowych profili sprzętowych
- **[Easy Profile Management](examples/profiles/EASY_PROFILE_MANAGEMENT.md)** - Przewodnik krok po kroku
