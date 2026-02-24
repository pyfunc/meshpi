# 🛠️ Zarządzanie sprzętem i grupami urządzeń

MeshPi oferiera zaawansowane możliwości zarządzania sprzętem na pojedynczych urządzeniach oraz grupach urządzeń.

## 📋 Lista sprzętu i katalog

### Przeglądanie dostępnych profili

```bash
# Pełny katalog sprzętu
meshpi hw catalog

# Katalog popularnych urządzeń
meshpi hw catalog --popular

# Katalog z filtrowaniem
meshpi hw catalog --category display
meshpi hw catalog --tag i2c

# Różne formaty wyjściowe
meshpi hw catalog --format json
meshpi hw catalog --format list
```

### Lista profili sprzętowych

```bash
# Wszystkie dostępne profile
meshpi hw list

# Filtrowanie po kategorii
meshpi hw list --category sensor
meshpi hw list --category hat

# Filtrowanie po tagach
meshpi hw list --tag oled
meshpi hw list --tag i2c
```

## 🚀 Szybka instalacja sprzętu

### Interaktywny instalator

```bash
# Pełny interaktywny instalator
meshpi hw quick-install --interactive

# Szybka instalacja z kategorii
meshpi hw quick-install display --interactive

# Instalacja popularnych urządzeń
meshpi hw quick-install --popular --interactive
```

### Instalacja na konkretnych urządzeniach

```bash
# Na pojedynczym urządzeniu zdalnym
meshpi hw quick-install sensor --target pi@192.168.1.100

# Na grupie urządzeń
meshpi hw quick-install display --group office_sensors

# Lokalna instalacja
meshpi hw quick-install oled --interactive
```

## 👥 Zarządzanie grupami urządzeń

### Tworzenie grup

```bash
# Tworzenie grupy
meshpi group create sensors --description "All sensor devices"
meshpi group create office --description "Office equipment"
meshpi group create lab --description "Laboratory equipment"
```

### Dodawanie urządzeń do grup

```bash
# Dodawanie pojedynczych urządzeń
meshpi group add-device sensors pi@192.168.1.100
meshpi group add-device sensors pi@192.168.1.101
meshpi group add-device office pi@192.168.1.200

# Lista grup
meshpi group list

# Szczegóły grupy
meshpi group show sensors
```

### Operacje na grupach

```bash
# Wykonywanie komend na grupie
meshpi group exec sensors "meshpi diag"
meshpi group exec office "uptime"

# Instalacja sprzętu na grupie
meshpi group hw-apply sensors sensor_bme280 sensor_ds18b20
meshpi group hw-apply office oled_ssd1306_i2c

# Interaktywna instalacja na grupie
meshpi group hw-apply sensors --interactive
```

## 🎯 Przykłady użycia

### Scenariusz 1: Konfiguracja czujników w biurze

```bash
# 1. Utwórz grupę czujników
meshpi group create office_sensors --description "Office temperature sensors"

# 2. Dodaj urządzenia
meshpi group add-device office_sensors pi@192.168.1.100
meshpi group add-device office_sensors pi@192.168.1.101
meshpi group add-device office_sensors pi@192.168.1.102

# 3. Zainstaluj czujniki
meshpi group hw-apply office_sensors sensor_bme280 sensor_ds18b20

# 4. Sprawdź status
meshpi group exec office_sensors "meshpi diag"
```

### Scenariusz 2: Wyświetlacze OLED w magazynie

```bash
# 1. Szybka instalacja wyświetlaczy
meshpi hw quick-install display --group warehouse --interactive

# 2. Lub bezpośrednio
meshpi group hw-apply warehouse oled_ssd1306_i2c

# 3. Test wyświetlaczy
meshpi group exec warehouse "meshpi hw list"
```

### Scenariusz 3: HATs w laboratorium

```bash
# 1. Przeglądaj dostępne HATs
meshpi hw catalog --category hat

# 2. Wybierz i zainstaluj
meshpi hw quick-install hat --interactive --group lab

# 3. Konfiguracja specyficzna
meshpi group hw-apply lab hat_sense hat_rtc_ds3231
```

## 📊 Monitorowanie grup

```bash
# Status wszystkich urządzeń w grupie
meshpi group exec sensors "meshpi diag"

# Informacje o systemie
meshpi group exec office "uname -a && free -h"

# Status usług MeshPi
meshpi group exec lab "systemctl status meshpi-daemon"
```

## 🔧 Zaawansowane filtrowanie

```bash
# Katalog z wieloma filtrami
meshpi hw catalog --category sensor --tag i2c --popular

# Lista z konkretnymi tagami
meshpi hw list --tag temperature --tag humidity

# Szybka instalacja popularnych sensorów
meshpi hw quick-install sensor --popular --interactive
```

## 📁 Struktura grup

Grupy są zapisywane w `~/.meshpi/groups.json`:

```json
{
  "sensors": {
    "name": "sensors",
    "description": "All sensor devices",
    "devices": [
      "pi@192.168.1.100:22",
      "pi@192.168.1.101:22"
    ],
    "created_at": 1640995200.0
  }
}
```

## 🌐 Integracja z SSH

Wszystkie operacje grupowe integrują się z zarządzaniem SSH:

```bash
# Skanuj i dodaj do grupy
meshpi ssh scan --add
meshpi group add-device new_devices pi@192.168.1.150

# Zdalna instalacja na grupie
meshpi ssh hw-apply --target-group sensors hat_sense
```

To daje pełną kontrolę nad flotą urządzeń Raspberry Pi z jednego miejsca!
