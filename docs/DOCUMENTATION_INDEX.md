# 📚 MeshPi Documentation Index

## 🚀 **Szybki Start**

- **[README.md](../README.md)** - Główna dokumentacja projektu
- **[Cheat Sheet](CHEAT_SHEET.md)** - Szybkie komendy i scenariusze
- **[Complete Deployment Guide](COMPLETE_DEPLOYMENT_GUIDE.md)** - Kompletny przewodnik wdrożenia

---

## 📋 **Standardy i Dokumentacja**

### 🏗️ **Standardy Systemowe**
- **[Standard Documentation](STANDARD_DOCUMENTATION.md)** - Pełny przewodnik standardów
- **[Standards Table](STANDARDS_TABLE.md)** - Tabela referencyjna standardów

### 👥 **Zarządzanie Grupami i Urządzeniami**
- **[Hardware Group Management](HARDWARE-GROUP-MANAGEMENT.md)** - Zarządzanie grupami urządzeń
- **[SSH Hardware Management](SSH-HARDWARE-MANAGEMENT.md)** - Zdalne zarządzanie sprzętem

---

## 🛠️ **Profile Sprzętowe**

### 📂 **Przykładowe Profile**
- **[examples/profiles/README.md](../examples/profiles/README.md)** - 20 przykładowych profili sprzętowych
- **[examples/profiles/EASY_PROFILE_MANAGEMENT.md](../examples/profiles/EASY_PROFILE_MANAGEMENT.md)** - Łatwe zarządzanie profilami

### 📋 **Kategorie Profili**
| Kategoria | Profile | Linki |
|-----------|---------|-------|
| 🌡️ **Sensory** | 4 profile | [BME280](../examples/profiles/bme280_weather_station.yaml), [DS18B20](../examples/profiles/ds18b20_temperature_array.yaml), [Industrial](../examples/profiles/industrial_sensor_monitor.yaml), [Voice AI](../examples/profiles/voice_assistant_llm.yaml) |
| 🖥️ **Wyświetlacze** | 3 profile | [OLED SSD1306](../examples/profiles/oled_ssd1306_status_display.yaml), [4.3" LCD](../examples/profiles/waveshare_lcd_43_touchscreen.yaml), [7" HDMI](../examples/profiles/lcd_7_touchscreen_hdmi.yaml) |
| 🚗 **Motory** | 2 profile | [L298N DC](../examples/profiles/motor_l298n_controller.yaml), [PCA9685 Servo](../examples/profiles/servo_pca9685_controller.yaml) |
| 🎩 **HATs** | 5 profile | [Sense HAT](../examples/profiles/rpi_sense_hat_complete.yaml), [PiSugar UPS](../examples/profiles/pisugar_ups_hat.yaml), [Adafruit Fruit](../examples/profiles/adafruit_fruit_hat.yaml), [Pimoroni Explorer](../examples/profiles/pimoroni_explorer_hat.yaml), [Waveshare IoT](../examples/profiles/waveshare_iot_hat.yaml) |
| 🎛️ **GPIO** | 2 profile | [A4988 Stepper](../examples/profiles/stepper_a4988_controller.yaml), [8-Channel Relay](../examples/profiles/relay_board_8channel.yaml) |
| 🎵 **Audio** | 1 profil | [I2S PCM5102 DAC](../examples/profiles/i2s_pcm5102_audio_dac.yaml) |
| 📷 **Kamery** | 1 profil | [RPi Camera Vision](../examples/profiles/rpi_camera_vision.yaml) |
| 🌐 **Sieć** | 2 profile | [LoRa SX1276](../examples/profiles/lora_sx1276_wireless.yaml), [Multi-Network Router](../examples/profiles/multi_network_router.yaml) |
| 🎮 **Wejścia** | 1 profil | [USB Gamepad](../examples/profiles/usb_gamepad_controller.yaml) |
| 🎮 **Rozrywka** | 1 profil | [Retro Gaming Station](../examples/profiles/retro_gaming_station.yaml) |

---

## 📈 **Monitoring i Obserwowalność**

### 🔍 **Audit i Logging**
- **Audit Logging** - Logowanie wszystkich operacji
- **Alert Engine** - System alertów i powiadomień
- **Prometheus Metrics** - Metryki systemowe i aplikacyjne

### 📊 **Dashboardy i Wizualizacja**
- **Grafana Dashboards** - Pre-built dashboardy
- **Prometheus UI** - Interfejs Prometheus
- **MeshPi Dashboard** - Główny dashboard aplikacji

---

## 🔄 **Procesy i Przepływy Pracy**

### 📋 **Standardowy Przepływ Wdrożenia**
1. **Planowanie** → Definiowanie grup urządzeń
2. **Konfiguracja** → Dodawanie urządzeń do grup
3. **Wybór** → Wybór profili sprzętowych
4. **Instalacja** → Aplikacja profili na grupach
5. **Weryfikacja** → Sprawdzenie statusu i działania
6. **Monitoring** → Konfiguracja monitoringu i alertów

### 🎯 **Przykładowe Scenariusze**
- **🏢 Biuro** - Monitoring środowiskowy
- **🏭 Magazyn** - Automatyka przemysłowa
- **🏠 Smart Home** - Kompleksowy system domowy
- **🔬 Laboratorium** - Sterowanie badawcze
- **🏪 Sklep** - Monitoring i bezpieczeństwo

---

## 🐳 **Docker i Wdrożenie**

### 📋 **Docker Compose**
- **[docker-compose.yml](../docker-compose.yml)** - Główna konfiguracja Docker
- **Monitoring Stack** - Prometheus + Grafana
- **Test Environment** - Środowisko testowe

### 🔧 **Konfiguracja**
- **[.env.example](../.env.example)** - Przykładowa konfiguracja środowiska
- **[pyproject.toml](../pyproject.toml)** - Konfiguracja projektu Python

---

## 🧪 **Testowanie**

### 📋 **Testy**
- **[tests/](../tests/)** - Katalog testów
- **Test Scenarios** - Scenariusze testowe E2E
- **Integration Tests** - Testy integracyjne
- **Unit Tests** - Testy jednostkowe

### 🔍 **Diagnostyka**
- **Doctor Commands** - Komendy diagnostyczne
- **Health Checks** - Sprawdzanie zdrowia systemu
- **Debug Tools** - Narzędzia debugowania

---

## 📝 **Dokumentacja Deweloperska**

### 🔧 **Kod źródłowy**
- **[meshpi/](../meshpi/)** - Główny kod aplikacji
- **API Documentation** - Dokumentacja API
- **Architecture Overview** - Przegląd architektury

### 🔄 **CI/CD**
- **[ci.yml](../.github/workflows/ci.yml)** - Konfiguracja CI
- **[docker-compose.test-rpi.yml](../docker-compose.test-rpi.yml)** - Testy RPi
- **Deployment Scripts** - Skrypty wdrożeniowe

---

## 📚 **Referencje**

### 📋 **Komendy CLI**
- **Group Management** - Zarządzanie grupami
- **Hardware Profiles** - Zarządzanie profilami
- **Monitoring Commands** - Komendy monitoringu
- **SSH Commands** - Komendy zdalne

### 🔗 **API Endpoints**
- **REST API** - Dokumentacja endpointów
- **WebSocket API** - Komunikacja w czasie rzeczywistym
- **Metrics API** - Endpointy metryk

---

## 🆘 **Pomoc i Wsparcie**

### 📋 **Troubleshooting**
- **Common Issues** - Częste problemy i rozwiązania
- **Debug Guide** - Przewodnik debugowania
- **FAQ** - Najczęściej zadawane pytania

### 📞 **Kontakt**
- **Issues** - Zgłaszanie problemów
- **Discussions** - Dyskusje i pytania
- **Contributing** - Współpraca przy projekcie

---

## 📈 **Roadmap**

### 🎯 **Plany rozwoju**
- **Następne wersje** - Planowane funkcje
- **Enhancement Requests** - Prośby o ulepszenia
- **Community Contributions** - Wkład społeczności

---

## 🔍 **Szybkie odniesienia**

### 🎯 **Najczęściej używane komendy**
```bash
meshpi group create [name] --description "desc"
meshpi group add-device [group] pi@IP
meshpi group hw-apply [group] [profile]
meshpi hw catalog --category [type]
meshpi audit
meshpi alerts status
docker compose --profile monitoring up
```

### 🔗 **Przydatne linki**
- **Dashboard**: http://localhost:7422/dashboard
- **API Docs**: http://localhost:7422/docs
- **Metrics**: http://localhost:7422/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/meshpi)

---

## 📝 **Podsumowanie**

Ta dokumentacja zapewnia kompletny zasób wiedzy o MeshPi, obejmujący:

- 🏗️ **Standardy** i najlepsze praktyki
- 🛠️ **Profile sprzętowe** i przykłady
- 📈 **Monitoring** i obserwowalność
- 🔄 **Procesy** wdrożeniowe
- 🐳 **Docker** i konfigurację
- 🧪 **Testowanie** i diagnostykę
- 📚 **Referencje** i API

**Dla szybkiego startu, zobacz [Cheat Sheet](CHEAT_SHEET.md) lub [Complete Deployment Guide](COMPLETE_DEPLOYMENT_GUIDE.md)!** 🚀
