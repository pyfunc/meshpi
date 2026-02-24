# Zdalne zarządzanie urządzeniami HAT przez SSH

MeshPi umożliwia zdalne zarządzanie profilami sprzętowymi na urządzeniach klienckich przez SSH.

## 🔗 Konfiguracja połączenia SSH

```bash
# Dodanie urządzeń do zarządzania
meshpi ssh add pi@192.168.1.100 --name "kitchen-rpi"
meshpi ssh add pi@192.168.1.101 --name "garage-rpi" --tags "garage,sensor"

# Skanowanie sieci w poszukiwaniu urządzeń
meshpi ssh scan --network 192.168.1.0/24

# Lista zarządzanych urządzeń
meshpi ssh list
```

## 🔍 Zdalne wyszukiwanie profili sprzętowych

```bash
# Wyszukiwanie na wszystkich urządzeniach
meshpi ssh hw-search oled --category display

# Wyszukiwanie na konkretnym urządzeniu
meshpi ssh hw-search sensor --target pi@192.168.1.100

# Wyszukiwanie z tagami
meshpi ssh hw-search i2c --tag i2c --parallel
```

## 🛠️ Zdalna instalacja profili sprzętowych

```bash
# Instalacja na wszystkich urządzeniach
meshpi ssh hw-apply oled_ssd1306_i2c sensor_bme280

# Instalacja na konkretnym urządzeniu
meshpi ssh hw-apply hat_sense --target pi@192.168.1.100

# Interaktywna instalacja
meshpi ssh hw-apply --interactive --target pi@192.168.1.100

# Wyszukiwanie i instalacja w jednym kroku
meshpi ssh hw-apply --search oled --interactive

# Tryb testowy (bez instalacji)
meshpi ssh hw-apply --dry-run hat_sense
```

## 🎯 Zdalne tworzenie profili niestandardowych

```bash
# Interaktywne tworzenie profilu na zdalnym urządzeniu
meshpi ssh hw-create --interactive --target pi@192.168.1.100

# Import profilu z pliku
meshpi ssh hw-create --import-file my_profile.yaml --target pi@192.168.1.100

# Szybkie tworzenie z linii komend
meshpi ssh hw-create \
  --name "Custom Sensor" \
  --category sensor \
  --packages "i2c-tools,python3-smbus" \
  --target pi@192.168.1.100
```

## 📋 Zarządzanie profilami niestandardowymi

```bash
# Lista profili niestandardowych na urządzeniach
meshpi ssh hw-custom --parallel

# Lista wszystkich profili sprzętowych
meshpi ssh hw-list --category hat

# Szczegóły profilu
meshpi ssh hw-show hat_sense --target pi@192.168.1.100
```

## 📁 Transfer plików

```bash
# Wysłanie pliku konfiguracyjnego na urządzenie
meshpi ssh transfer config.yaml /tmp/config.yaml --target pi@192.168.1.100

# Pobranie pliku z urządzenia
meshpi ssh transfer local_backup.log /var/log/meshpi.log --download --target pi@192.168.1.100

# Wysłanie pliku na wiele urządzeń
meshpi ssh transfer profile.json /home/pi/.meshpi/profile.json
```

## 🔄 Zarządzanie systemem

```bash
# Instalacja MeshPi na urządzeniach
meshpi ssh install --target pi@192.168.1.100

# Aktualizacja MeshPi
meshpi ssh update --parallel

# Restart usługi
meshpi ssh restart --service meshpi-daemon --target pi@192.168.1.100

# Aktualizacja systemu
meshpi ssh system-upgrade --parallel --safe
```

## 🌐 Przykłady użycia

### Scenariusz 1: Konfiguracja wielu czujników

```bash
# Dodaj urządzenia
meshpi ssh add pi@192.168.1.100 --name "temp-sensor-1"
meshpi ssh add pi@192.168.1.101 --name "temp-sensor-2"

# Zainstaluj profile czujników na wszystkich urządzeniach
meshpi ssh hw-apply sensor_bme280 sensor_ds18b20 --parallel

# Uruchom diagnostykę
meshpi ssh exec "meshpi diag" --parallel
```

### Scenariusz 2: Wdrożenie wyświetlaczy OLED

```bash
# Wyszukaj profile OLED
meshpi ssh hw-search oled --category display

# Zainstaluj interaktywnie
meshpi ssh hw-apply --search oled --interactive

# Sprawdź status
meshpi ssh exec "meshpi hw custom" --parallel
```

### Scenariusz 3: Tworzenie własnych profili

```bash
# Stwórz profil niestandardowy
meshpi ssh hw-create \
  --name "Farm Sensor Array" \
  --category sensor \
  --description "Multiple sensors for farm monitoring" \
  --packages "i2c-tools,python3-smbus" \
  --python-packages "adafruit-circuitpython-bme280" \
  --tags "farm,i2c,sensor" \
  --target pi@192.168.1.100

# Zastosuj profil
meshpi ssh hw-apply farm_sensor_array --target pi@192.168.1.100
```

## 🔐 Bezpieczeństwo

```bash
# Użycie klucza SSH
meshpi ssh add pi@192.168.1.100 --key ~/.ssh/rpi_key

# Użycie hasła (jednorazowo)
meshpi ssh connect pi@192.168.1.100 --password

# Transfer plików z uwierzytelnieniem
meshpi ssh transfer secret.json /tmp/secret.json --target pi@192.168.1.100
```

## 📊 Monitorowanie

```bash
# Sprawdzenie statusu wszystkich urządzeń
meshpi ssh exec "meshpi diag" --parallel

# Monitorowanie usług
meshpi ssh exec "systemctl status meshpi-daemon" --parallel

# Sprawdzenie wersji MeshPi
meshpi ssh exec "meshpi info" --parallel
```

Wszystkie te operacje umożliwiają centralne zarządzanie flotą urządzeń Raspberry Pi z jednego hosta przez SSH!
