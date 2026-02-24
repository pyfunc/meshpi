# 🚀 Łatwe Zarządzanie Profilami i Grupami Urządzeń

Praktyczny przewodnik krok po kroku jak efektywnie zarządzać profilami sprzętowymi i łączyć je z grupami urządzeń w MeshPi.

## 📋 **Krok 1: Zarządzanie Profilami**

### 🔍 **Odkryj dostępne profile**

```bash
# Pełny katalog wszystkich profili
meshpi hw catalog

# Popularne profile (najczęściej używane)
meshpi hw catalog --popular

# Według kategorii
meshpi hw catalog --category sensor      # sensory
meshpi hw catalog --category display     # wyświetlacze
meshpi hw catalog --category gpio         # GPIO
meshpi hw catalog --category camera       # kamery

# Według tagów (technologii)
meshpi hw catalog --tag i2c             # I2C urządzenia
meshpi hw catalog --tag oled            # OLED wyświetlacze
meshpi hw catalog --tag sensor          # sensory
```

### 🎯 **Szybki wybór i instalacja**

```bash
# Interaktywny wybór - najłatwiejszy sposób!
meshpi hw quick-install --interactive

# Wybór z kategorii
meshpi hw quick-install sensor --interactive
meshpi hw quick-install display --interactive

# Wybór popularnych urządzeń
meshpi hw quick-install --popular --interactive
```

### 📝 **Lista i szczegóły profili**

```bash
# Wszystkie profile
meshpi hw list

# Filtrowana lista
meshpi hw list --category sensor
meshpi hw list --tag oled

# Szczegóły konkretnego profilu
meshpi hw show sensor_bme280
meshpi hw show oled_ssd1306_i2c
```

---

## 👥 **Krok 2: Tworzenie Grup Urządzeń**

### 🏗️ **Tworzenie grup**

```bash
# Grupa sensorów w biurze
meshpi group create office_sensors --description "Temperature sensors in office"

# Grupa wyświetlaczy w magazynie
meshpi group create warehouse_displays --description "OLED displays in warehouse"

# Grupa urządzeń GPIO w laboratorium
meshpi group create lab_gpio --description "GPIO controllers in lab"

# Grupa kamer w sklepie
meshpi group create shop_cameras --description "Security cameras"
```

### 📋 **Lista grup**

```bash
# Pokaż wszystkie grupy
meshpi group list

# Szczegóły grupy
meshpi group show office_sensors
meshpi group show warehouse_displays
```

---

## 🔗 **Krok 3: Dodawanie Urządzeń do Grup**

### 📡 **Dodawanie urządzeń SSH**

```bash
# Dodaj pojedyncze urządzenia
meshpi group add-device office_sensors pi@192.168.1.100
meshpi group add-device office_sensors pi@192.168.1.101
meshpi group add-device office_sensors pi@192.168.1.102

# Dodaj wiele urządzeń naraz
meshpi group add-device warehouse_displays pi@192.168.1.200
meshpi group add-device warehouse_displays pi@192.168.1.201
meshpi group add-device warehouse_displays pi@192.168.1.202

# Sprawdź zawartość grupy
meshpi group show office_sensors
```

### 🔍 **Skanowanie i automatyczne dodawanie**

```bash
# Skanuj sieć w poszukiwaniu urządzeń
meshpi ssh scan --network 192.168.1.0/24

# Dodaj znalezione urządzenia do grupy
meshpi group add-device office_sensors pi@192.168.1.100
meshpi group add-device office_sensors pi@192.168.1.101
```

---

## 🛠️ **Krok 4: Łączenie Profili z Grupami**

### 🎯 **Instalacja profili na grupach**

```bash
# Zainstaluj sensory na wszystkich urządzeniach w grupie
meshpi group hw-apply office_sensors sensor_bme280 sensor_ds18b20

# Zainstaluj wyświetlacze w magazynie
meshpi group hw-apply warehouse_displays oled_ssd1306_i2c

# Zainstaluj sterowniki GPIO w laboratorium
meshpi group hw-apply lab_gpio stepper_a4988_controller relay_board_8channel

# Zainstaluj kamery w sklepie
meshpi group hw-apply shop_cameras rpi_camera_vision
```

### 🎮 **Interaktywna instalacja na grupach**

```bash
# Interaktywny wybór dla grupy
meshpi group hw-apply office_sensors --interactive

# Interaktywny wybór z kategorii
meshpi group hw-apply warehouse_displays --interactive --category display
```

---

## 🔄 **Krok 5: Zarządzanie i Monitoring**

### 📊 **Sprawdzanie statusu grup**

```bash
# Wykonaj komendy na całej grupie
meshpi group exec office_sensors "meshpi diag"
meshpi group exec warehouse_displays "meshpi hw list"
meshpi group exec lab_gpio "uptime"

# Sprawdź status instalacji
meshpi group exec office_sensors "meshpi hw list"
```

### 🔧 **Aktualizacje i modyfikacje**

```bash
# Dodaj nowe profile do istniejącej grupy
meshpi group hw-apply office_sensors --additional sensor_dht22

# Usuń profile z grupy (jeśli wspierane)
meshpi group hw-remove office_sensors sensor_ds18b20

# Zaktualizuj wszystkie profile w grupie
meshpi group hw-update office_sensors
```

---

## 🎯 **Praktyczne Scenariusze**

### 🏢 **Scenariusz 1: Biuro - Monitoring Środowiskowy**

```bash
# Krok 1: Stwórz grupę sensorów biurowych
meshpi group create office_env --description "Office environmental monitoring"

# Krok 2: Dodaj urządzenia
meshpi group add-device office_env pi@192.168.1.100
meshpi group add-device office_env pi@192.168.1.101
meshpi group add-device office_env pi@192.168.1.102

# Krok 3: Zainstaluj sensory
meshpi group hw-apply office_env bme280_weather_station ds18b20_temperature_array

# Krok 4: Zainstaluj wyświetlacze statusu
meshpi group hw-apply office_env oled_ssd1306_status_display

# Krok 5: Sprawdź status
meshpi group exec office_env "meshpi diag"
```

### 🏭 **Scenariusz 2: Magazyn - Automatyka Przemysłowa**

```bash
# Krok 1: Grupa urządzeń magazynowych
meshpi group create warehouse_auto --description "Warehouse automation systems"

# Krok 2: Dodaj urządzenia sterujące
meshpi group add-device warehouse_auto pi@192.168.1.200
meshpi group add-device warehouse_auto pi@192.168.1.201

# Krok 3: Zainstaluj sterowniki przekaźników
meshpi group hw-apply warehouse_auto relay_board_8channel

# Krok 4: Zainstaluj sensory
meshpi group hw-apply warehouse_auto industrial_sensor_monitor

# Krok 5: Zainstaluj wyświetlacze statusu
meshpi group hw-apply warehouse_auto oled_ssd1306_status_display
```

### 🏠 **Scenariusz 3: Smart Home - Kompleksowy System**

```bash
# Krok 1: Grupy dla różnych pomieszczeń
meshpi group create home_sensors --description "Home environmental sensors"
meshpi group create home_displays --description "Home status displays"
meshpi group create home_control --description "Home automation controllers"

# Krok 2: Dodaj urządzenia do odpowiednich grup
meshpi group add-device home_sensors pi@192.168.1.10  # salon
meshpi group add-device home_sensors pi@192.168.1.11  # sypialnia
meshpi group add-device home_displays pi@192.168.1.20  # kuchnia
meshpi group add-device home_control pi@192.168.1.30  # centrala

# Krok 3: Zainstaluj odpowiednie profile
meshpi group hw-apply home_sensors bme280_weather_station
meshpi group hw-apply home_displays oled_ssd1306_status_display
meshpi group hw-apply home_control relay_board_8channel

# Krok 4: Połącz systemy
meshpi group exec home_sensors "python3 /home/pi/sensor_monitor.py"
meshpi group exec home_displays "python3 /home/pi/display_status.py"
```

---

## 🎨 **Zaawansowane Techniki**

### 🔄 **Szablony grupowe**

```bash
# Stwórz szablon grupy sensorów
meshpi group create template_sensors --description "Template for sensor groups"

# Skopiuj szablon dla nowych lokalizacji
meshpi group copy template_sensors office_sensors --description "Office sensors"
meshpi group copy template_sensors warehouse_sensors --description "Warehouse sensors"

# Dodaj urządzenia do nowych grup
meshpi group add-device office_sensors pi@192.168.1.100
meshpi group add-device warehouse_sensors pi@192.168.1.200
```

### 📦 **Pakiety profili dla grup**

```bash
# Zdefiniuj zestaw profili dla typowych zastosowań
meshpi group create env_monitoring --description "Environmental monitoring setup"

# Zastosuj zestaw profili
meshpi group hw-apply env_monitoring bme280_weather_station oled_ssd1306_status_display

# Użyj zestawu dla różnych grup
meshpi group hw-apply office_sensors --profile-set env_monitoring
meshpi group hw-apply warehouse_sensors --profile-set env_monitoring
```

### 🔍 **Inteligentne dopasowanie**

```bash
# Wykryj sprzęt i zaproponuj profile
meshpi group auto-detect office_sensors

# Automatycznie zainstaluj pasujące profile
meshpi group auto-install office_sensors

# Weryfikuj instalację
meshpi group verify office_sensors
```

---

## 📝 **Najlepsze Praktyki**

### ✅ **Organizacja grup:**
- **Logiczne nazwy:** `office_sensors`, `warehouse_displays`, `lab_gpio`
- **Opisy:** Zawsze dodawaj opisy dla jasności
- **Spójność:** Grupuj urządzenia o podobnym przeznaczeniu

### ✅ **Zarządzanie profilami:**
- **Testowanie:** Najpierw testuj na jednym urządzeniu
- **Wersjonowanie:** Trzymaj spis zainstalowanych profili
- **Backup:** Kopiuj konfiguracje przed zmianami

### ✅ **Monitoring:**
- **Regularne sprawdzenia:** `meshpi group exec [group] "meshpi diag"`
- **Logowanie:** Trzymaj logi instalacji i problemów
- **Alerting:** Ustaw alerty dla awarii sprzętu

---

## 🚀 **Szybkie Komendy (Cheat Sheet)**

```bash
# 🔍 Odkrywanie profili
meshpi hw catalog --popular
meshpi hw quick-install --interactive

# 👥 Zarządzanie grupami
meshpi group create [name] --description "desc"
meshpi group add-device [group] pi@IP
meshpi group list

# 🛠️ Instalacja na grupach
meshpi group hw-apply [group] [profile1] [profile2]
meshpi group hw-apply [group] --interactive

# 📊 Monitoring
meshpi group exec [group] "meshpi diag"
meshpi group show [group]
```

---

## ✅ **Podsumowanie**

1. **Odkryj profile** → `meshpi hw catalog --popular`
2. **Stwórz grupy** → `meshpi group create [name]`
3. **Dodaj urządzenia** → `meshpi group add-device [group] pi@IP`
4. **Zainstaluj profile** → `meshpi group hw-apply [group] [profile]`
5. **Monitoruj** → `meshpi group exec [group] "meshpi diag"`

**Gotowe! Teraz możesz łatwo zarządzać profilami i grupami urządzeń!** 🎉
