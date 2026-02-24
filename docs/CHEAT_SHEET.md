# 🚀 MeshPi Cheat Sheet

## 👥 **GRUPY URZĄDZEŃ**

### Tworzenie grup
```bash
meshpi group create office_sensors --description "Office environmental monitoring"
meshpi group create warehouse_auto --description "Warehouse automation"
meshpi group create lab_gpio --description "Lab GPIO controllers"
```

### Dodawanie urządzeń
```bash
meshpi group add-device office_sensors pi@192.168.1.100
meshpi group add-device office_sensors pi@192.168.1.101
meshpi group add-device warehouse_auto pi@192.168.1.200
```

### Zarządzanie grupami
```bash
meshpi group list                    # Lista grup
meshpi group show office_sensors    # Szczegóły grupy
meshpi group exec office_sensors "meshpi diag"  # Wykonaj na grupie
```

---

## 🛠️ **PROFILE SPRZĘTOWE**

### Przeglądanie profili
```bash
meshpi hw catalog                   # Wszystkie profile
meshpi hw catalog --category sensor # Według kategorii
meshpi hw catalog --tag i2c         # Według tagów
meshpi hw catalog --popular         # Popularne profile
```

### Zarządzanie profilami
```bash
meshpi hw list                      # Lista dostępnych
meshpi hw show bme280_weather_station  # Szczegóły profilu
meshpi hw create --import-file profile.yaml  # Import profilu
meshpi hw apply bme280_weather_station  # Zastosuj profil
```

---

## 🔄 **INSTALACJA NA GRUPACH**

### Szybka instalacja
```bash
# Jedna grupa, jeden profil
meshpi group hw-apply office_sensors bme280_weather_station

# Jedna grupa, wiele profili
meshpi group hw-apply office_sensors bme280_weather_station oled_ssd1306_status_display

# Interaktywnie
meshpi group hw-apply office_sensors --interactive
```

### Szybka instalacja według kategorii
```bash
meshpi hw quick-install sensor --group office_sensors
meshpi hw quick-install display --group warehouse_displays
meshpi hw quick-install gpio --group lab_gpio
```

---

## 📈 **MONITORING**

### Audit Logging
```bash
meshpi audit                                    # Wszystkie logi
meshpi audit --device rpi-001                  # Logi urządzenia
meshpi audit --operation hw-apply               # Logi operacji
meshpi audit --export audit_20260224.jsonl     # Eksport
```

### Alert Engine
```bash
meshpi alerts status                            # Status alertów
meshpi alerts list                              # Lista reguł
meshpi alerts test temperature-high            # Test alertu
meshpi alerts silence temperature-high --duration 1h  # Wycisz
```

### Metryki
```bash
curl http://localhost:7422/metrics             # Wszystkie metryki
curl http://localhost:7422/metrics | grep meshpi_devices  # Filtruj
```

### OTA Updates
```bash
meshpi ota push --image ./image.img --devices rpi-001,rpi-002
meshpi ota status
meshpi ota rollback --device rpi-001
```

---

## 🐳 **DOCKER**

### Podstawowe uruchomienie
```bash
docker compose up --build                    # Wszystkie usługi
docker compose up meshpi-host               # Tylko host
docker compose up meshpi-host meshpi-client # Host + klient
```

### Z monitoringiem
```bash
docker compose --profile monitoring up       # Z Prometheus + Grafana
docker compose --profile monitoring up prometheus grafana  # Tylko monitoring
```

### Testowanie
```bash
docker compose run --rm meshpi-test          # Uruchom testy
docker compose --profile test up             # Profil testowy
```

---

## 🎯 **POPULARNE SCENARIUSZE**

### 🏢 Biuro - Monitoring środowiskowy
```bash
# 1. Stwórz grupę
meshpi group create office_env --description "Office environmental monitoring"

# 2. Dodaj urządzenia
meshpi group add-device office_env pi@192.168.1.100
meshpi group add-device office_env pi@192.168.1.101

# 3. Zainstaluj profile
meshpi group hw-apply office_env bme280_weather_station oled_ssd1306_status_display

# 4. Sprawdź status
meshpi group exec office_env "meshpi diag"
```

### 🏭 Magazyn - Automatyka przemysłowa
```bash
# 1. Grupa automatyki
meshpi group create warehouse_auto --description "Warehouse automation"

# 2. Dodaj sterowniki
meshpi group add-device warehouse_auto pi@192.168.1.200
meshpi group add-device warehouse_auto pi@192.168.1.201

# 3. Zainstaluj profile
meshpi group hw-apply warehouse_auto relay_board_8channel industrial_sensor_monitor

# 4. Uruchom monitoring
docker compose --profile monitoring up
```

### 🏠 Smart Home - Kompletny system
```bash
# 1. Stwórz grupy
meshpi group create home_sensors --description "Home sensors"
meshpi group create home_displays --description "Home displays"
meshpi group create home_control --description "Home automation"
meshpi group create home_ai --description "AI assistants"

# 2. Dodaj urządzenia
meshpi group add-device home_sensors pi@192.168.1.10
meshpi group add-device home_displays pi@192.168.1.20
meshpi group add-device home_control pi@192.168.1.30
meshpi group add-device home_ai pi@192.168.1.40

# 3. Zainstaluj profile
meshpi group hw-apply home_sensors bme280_weather_station
meshpi group hw-apply home_displays waveshare_lcd_43_touchscreen
meshpi group hw-apply home_control relay_board_8channel
meshpi group hw-apply home_ai voice_assistant_llm

# 4. Monitoring
docker compose --profile monitoring up
meshpi audit
meshpi alerts status
```

---

## 📊 **KLUCZOWE METRYKI**

### Systemowe
```bash
meshpi_devices_total              # Liczba urządzeń
meshpi_device_online              # Status online (0/1)
meshpi_cpu_usage                  # Użycie CPU %
meshpi_memory_usage               # Użycie pamięci %
meshpi_temperature_celsius        # Temperatura °C
```

### Profile
```bash
meshpi_hardware_profiles_installed_total  # Liczba profili
meshpi_hardware_profiles_by_category       # Profile według kategorii
meshpi_hardware_profiles_install_duration  # Czas instalacji
meshpi_hardware_profiles_install_success   # Sukcesy/porażki
```

---

## 🔗 **PRZYDATNE LINKI**

### Dashboardy
```bash
http://localhost:7422/dashboard          # MeshPi Dashboard
http://localhost:7422/metrics            # Prometheus Metrics
http://localhost:7422/docs              # API Documentation
http://localhost:9090                    # Prometheus UI
http://localhost:3000                    # Grafana (admin/meshpi)
```

### Dokumentacja
```bash
docs/COMPLETE_DEPLOYMENT_GUIDE.md       # Kompletny przewodnik
docs/STANDARD_DOCUMENTATION.md          # Standardy
docs/STANDARDS_TABLE.md                  # Tabela referencyjna
examples/profiles/                       # 20 przykładowych profili
```

---

## 🚨 **Szybkie diagnozy**

### Sprawdzenie statusu
```bash
meshpi diag                              # Diagnostyka lokalna
meshpi group exec office_sensors "meshpi diag"  # Diagnostyka grupy
meshpi hw list                           # Zainstalowane profile
meshpi alerts status                     # Status alertów
```

### Resetowanie
```bash
meshpi hw remove bme280_weather_station  # Usuń profil
meshpi group remove-device office_sensors pi@192.168.1.100  # Usuń urządzenie
meshpi alerts clear                      # Wyczyść alerty
```

---

## ✅ **CHECKLISTA WDROŻENIA**

- [ ] **Planowanie**: Zdefiniuj grupy i profile
- [ ] **Testowanie**: Przetestuj na jednym urządzeniu
- [ ] **Instalacja**: Zastosuj na grupach
- [ ] **Weryfikacja**: Sprawdź status i działanie
- [ ] **Monitoring**: Uruchom Prometheus + Grafana
- [ ] **Alerting**: Skonfiguruj reguły alertów
- [ ] **Audit**: Włącz logowanie operacji
- [ ] **Backup**: Backup konfiguracji i logów

---

## 🎯 **PRO TIPS**

### Skanowanie sieci
```bash
meshpi ssh scan --network 192.168.1.0/24  # Znajdź RPi w sieci
```

### Import/Export profili
```bash
meshpi hw export bme280_weather_station --format yaml
meshpi hw create --import-file profile.yaml
```

### Automatyczne wykrywanie
```bash
meshpi diag                               # Wykryj sprzęt
meshpi hw quick-install --interactive     # Zainstaluj pasujące profile
```

### Batch operacje
```bash
meshpi group exec all_devices "apt update && apt upgrade -y"
meshpi group exec all_devices "reboot"
```

---

**🚀 Gotowe! Teraz możesz zarządzać flotą Raspberry Pi jak profesjonalista!**
