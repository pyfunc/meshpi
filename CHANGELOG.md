## [0.1.34] - 2026-02-24

### Summary

docs(docs): deep code analysis engine with 4 supporting modules

### Docs

- docs: update README
- docs: update CHEAT_SHEET.md
- docs: update COMPLETE_DEPLOYMENT_GUIDE.md
- docs: update DOCUMENTATION_INDEX.md


## [0.1.33] - 2026-02-24

### Summary

docs(docs): deep code analysis engine

### Docs

- docs: update STANDARDS_TABLE.md
- docs: update STANDARD_DOCUMENTATION.md
- docs: update README


## [0.1.32] - 2026-02-24

### Summary

feat(docs): configuration management system

### Docs

- docs: update README
- docs: update STANDARD_DOCUMENTATION.md

### Test

- update tests/test_e2e.py

### Other

- update deploy/grafana/provisioning/dashboards/json/meshpi-overview.json
- update project.functions.toon


## [0.1.31] - 2026-02-24

### Summary

feat(docs): configuration management system

### Test

- update tests/test_e2e.py

### Other

- update Dockerfile.client
- config: update dashboards.yml
- update deploy/grafana/provisioning/dashboards/json/meshpi-overview.json
- config: update datasources.yml
- config: update prometheus.yml
- update meshpi/image/__init__.py


## [0.1.30] - 2026-02-24

### Summary

feat(meshpi): configuration management system

### Other

- update meshpi/host.py


## [0.1.29] - 2026-02-24

### Summary

feat(config): configuration management system

### Test

- update tests/test_monitoring.py

### Build

- update pyproject.toml

### Other

- update meshpi/alerts/__init__.py
- update meshpi/api/__init__.py
- update meshpi/api/monitoring.py
- update meshpi/audit.py
- update meshpi/metrics/__init__.py
- update meshpi/ota/__init__.py


## [0.1.28] - 2026-02-24

### Summary

refactor(meshpi): core module improvements

### Other

- update meshpi/audit.py


## [0.1.27] - 2026-02-24

### Summary

feat(docs): configuration management system

### Docs

- docs: update CONTRIBUTING.md
- docs: update README
- docs: update STANDARDS_TABLE.md
- docs: update STANDARD_DOCUMENTATION.md
- docs: update README

### Test

- update tests/test_doctor.py

### Ci

- config: update ci.yml

### Other

- update project.functions.toon
- scripts: update project.sh
- update project.toon-schema.json


## [0.1.26] - 2026-02-24

### Summary

feat(examples): CLI interface improvements

### Docs

- docs: update CONTRIBUTING.md
- docs: update EASY_PROFILE_MANAGEMENT.md

### Other

- config: update adafruit_fruit_hat.yaml
- config: update lcd_7_touchscreen_hdmi.yaml
- config: update motor_l298n_controller.yaml
- config: update pimoroni_explorer_hat.yaml
- config: update pisugar_ups_hat.yaml
- config: update servo_pca9685_controller.yaml
- config: update voice_assistant_llm.yaml
- config: update waveshare_iot_hat.yaml
- config: update waveshare_lcd_43_touchscreen.yaml
- update meshpi/cli.py


## [0.1.25] - 2026-02-24

### Summary

feat(examples): deep code analysis engine with 5 supporting modules

### Docs

- docs: update README
- docs: update README

### Other

- update .env.example
- config: update bme280_weather_station.yaml
- config: update ds18b20_temperature_array.yaml
- config: update i2s_pcm5102_audio_dac.yaml
- config: update industrial_sensor_monitor.yaml
- config: update lora_sx1276_wireless.yaml
- config: update multi_network_router.yaml
- config: update oled_ssd1306_status_display.yaml
- config: update relay_board_8channel.yaml
- config: update retro_gaming_station.yaml
- ... and 4 more


## [0.1.24] - 2026-02-24

### Summary

docs(docs): CLI interface with 3 supporting modules

### Docs

- docs: update README
- docs: update TODO.md


## [0.1.25] - 2026-02-24

### Summary

feat(hardware): advanced hardware management with groups and SSH remote control

### Features

- **Hardware Catalog**: New `meshpi hw catalog` command with advanced filtering
  - Filter by category, tags, popularity
  - Multiple output formats (table, JSON, list)
  - Categorized browsing with examples

- **Quick Install Wizard**: Interactive hardware installation with `meshpi hw quick-install`
  - Category-based selection interface
  - Support for device groups and remote targets
  - Popular hardware filtering
  - Multi-profile selection with confirmation

- **Device Groups**: Complete group management system
  - `meshpi group create` - Create device groups
  - `meshpi group add-device` - Add devices to groups
  - `meshpi group list/show` - Browse groups
  - `meshpi group exec` - Execute commands on groups
  - `meshpi group hw-apply` - Install hardware on groups

- **SSH Remote Hardware Management**: Full remote control capabilities
  - `meshpi ssh hw-search` - Search profiles on remote devices
  - `meshpi ssh hw-apply` - Install profiles remotely
  - `meshpi ssh hw-create` - Create custom profiles remotely
  - `meshpi ssh hw-custom` - List custom profiles remotely
  - `meshpi ssh hw-list` - Browse hardware on remote devices

- **Enhanced Hardware Profiles**: Extended profile system
  - Custom profile creation wizard
  - Import/export from YAML/JSON
  - Profile management with delete functionality
  - Integration with SSH and group systems

### Commands Added

```bash
# Hardware Management
meshpi hw catalog [--category] [--tag] [--popular] [--format]
meshpi hw quick-install [--target] [--group] [--interactive]

# Device Groups  
meshpi group create <name>
meshpi group add-device <group> <target>
meshpi group list
meshpi group show <group>
meshpi group exec <group> <command>
meshpi group hw-apply <group> [profiles...]

# SSH Remote Hardware
meshpi ssh hw-search [query] [--category] [--tag]
meshpi ssh hw-apply [profiles...] [--target] [--interactive]
meshpi ssh hw-create [--target] [--interactive]
meshpi ssh hw-custom [--target]
meshpi ssh hw-list [--category] [--tag]
```

### Docs

- **HARDWARE-GROUP-MANAGEMENT.md**: Comprehensive guide for hardware and group management
- **SSH-HARDWARE-MANAGEMENT.md**: Complete SSH remote control documentation
- **README.md**: Updated with new hardware management features
- Updated examples and usage patterns throughout documentation

### Breaking Changes

- Enhanced `meshpi hw list` with better filtering (backward compatible)
- Extended hardware profile system with custom profiles (backward compatible)

### Other

- Improved error handling for group operations
- Better progress reporting for batch installations
- Enhanced SSH connection management
- Optimized parallel execution for device groups

## [0.1.24] - 2026-02-24

### Summary

refactor(repo): repository organization and script migration

### Refactor

- **Repository Structure**: Reorganized scripts into dedicated directories
  - `test/` - All test-related scripts moved from root
  - `scripts/` - Tooling and utility scripts moved from root
- **Script Migration**: Moved 8 test scripts and 7 tooling scripts
- **Python Conversion**: Converted shell scripts to Python for better maintainability
  - `project.sh` → `scripts/project.py` (code analysis tool)
  - `monitor-repair.sh` → `scripts/monitor-repair.py` (real-time status monitoring)
  - `show-repair-status.sh` → `scripts/show-repair-status.py` (visual status display)

### Docs

- **README.md**: Added repository organization section with complete file structure
- **README.md**: Added comprehensive environment variables section
- **RPI-TESTING-README.md**: Updated all script references to new locations
- **CHANGELOG.md**: Updated script path references
- **.env.example**: Complete rewrite with all environment variables organized by category
- **docker-compose.yml**: Added LLM agent environment variables

### Test

- Updated all script references in documentation
- Made Python scripts executable
- Verified script functionality after migration

### Other

- **Breaking Change**: Script paths have changed - update documentation and workflows
- **Improved Maintainability**: Python scripts offer better error handling and extensibility

## [0.1.23] - 2026-02-24

### Summary

refactor(tests): configuration management system

### Test

- update tests/test_configuration_e2e.py
- update tests/test_edge_cases_errors.py
- update tests/test_hardware_profiles_e2e.py
- update tests/test_pendrive_e2e.py
- update tests/test_performance_stress.py
- update tests/test_ssh_management_e2e.py

### Other

- update meshpi/hardware/applier.py


## [0.1.23] - 2026-02-24

### Summary

fix(config): CLI interface improvements

### Docs

- docs: update RPI-TESTING-README.md
- docs: update HARDWARE-GROUP-MANAGEMENT.md

### Test

- scripts: update batch-rpi-test.sh
- scripts: update run-rpi-tests.sh
- scripts: update test-doctor.sh
- scripts: update test-enhanced-cli.sh
- scripts: update test-list.sh
- scripts: update test-restart.sh
- scripts: update test-ssh-host.sh
- scripts: update test-ssh-scan-identify.sh

### Other

- update <MagicMock name='_config_txt_path()' id='140086943225840'>
- update <MagicMock name='_config_txt_path()' id='140086943227184'>
- update <MagicMock name='_config_txt_path()' id='140086943227856'>
- update <MagicMock name='_config_txt_path()' id='140086943228192'>
- update <MagicMock name='_config_txt_path()' id='140086943231552'>
- update <MagicMock name='_config_txt_path()' id='140086943233232'>
- update <MagicMock name='_config_txt_path()' id='140086945398864'>
- update <MagicMock name='_config_txt_path()' id='140086945399200'>
- update <MagicMock name='_config_txt_path()' id='140086945402224'>
- update <MagicMock name='_config_txt_path()' id='140086957155264'>
- ... and 12 more


## [0.1.22] - 2026-02-24

### Summary

feat(goal): CLI interface improvements

### Other

- update meshpi/cli.py


## [0.1.21] - 2026-02-24

### Summary

feat(goal): CLI interface improvements

### Other

- update meshpi/cli.py


## [0.1.20] - 2026-02-24

### Summary

feat(tests): CLI interface improvements

### Docs

- docs: update RPI-TESTING-README.md

### Test

- scripts: update test-ssh-host.sh

### Build

- update pyproject.toml

### Other

- update =5.9
- update meshpi/cli.py
- update meshpi/registry.py


## [0.1.19] - 2026-02-24

### Summary

feat(goal): CLI interface improvements

### Other

- update meshpi/cli.py


## [0.1.18] - 2026-02-24

### Summary

feat(docs): CLI interface improvements

### Docs

- docs: update RPI-TESTING-README.md

### Other

- update meshpi/cli.py
- update meshpi/ssh_manager.py
- scripts: update rpi-service-manager.sh


## [0.1.17] - 2026-02-24

### Summary

fix(docs): CLI interface improvements

### Docs

- docs: update RPI-TESTING-README.md
- docs: update RPI-REPAIR-MONITORING.md

### Test

- scripts: update test-doctor.sh
- scripts: update test-list.sh
- scripts: update test-restart.sh

### Other

- scripts: update diagnose-rpi.sh
- scripts: update fix-rpi-meshpi.sh
- update meshpi/cli.py
- update meshpi/doctor.py
- scripts: update monitor-repair.sh
- scripts: update show-repair-status.sh


## [0.1.16] - 2026-02-24

### Summary

feat(tests): code quality metrics with 5 supporting modules

### Docs

- docs: update RPI-TESTING-README.md

### Other

- scripts: update test/batch-rpi-test.sh


## [0.1.15] - 2026-02-24

### Summary

feat(tests): configuration management system

### Docs

- docs: update README
- docs: update RPI-TESTING-README.md
- docs: update RPI-TEST-RESULTS.md
- docs: update RPI-TESTING.md

### Ci

- config: update test-rpi-arch.yml

### Other

- config: update docker-compose.test-rpi.yml
- docker: update Dockerfile
- update docker/test-rpi/aggregate-results.py
- update docker/test-rpi/test-installation.py
- update docker/test-rpi/test-utils.py
- scripts: update remote-rpi-test.sh
- scripts: update run-rpi-tests.sh


## [0.1.14] - 2026-02-24

### Summary

feat(meshpi): configuration management system

### Other

- update meshpi/host.py


## [0.1.13] - 2026-02-24

### Summary

feat(config): configuration management system

### Other

- update meshpi/applier.py
- update meshpi/config.py


## [0.1.12] - 2026-02-24

### Summary

feat(docs): deep code analysis engine with 6 supporting modules

### Docs

- docs: update README

### Build

- update pyproject.toml

### Other

- update meshpi/py.typed


## [0.1.11] - 2026-02-24

### Summary

feat(docs): code quality metrics with 5 supporting modules

### Docs

- docs: update README

### Build

- update pyproject.toml


## [0.1.10] - 2026-02-24

### Summary

refactor(build): deep code analysis engine with 6 supporting modules

### Docs

- docs: update TODO.md

### Other

- build: update Makefile
- update TICKET


## [0.1.9] - 2026-02-24

### Summary

refactor(build): core module improvements

### Other

- build: update Makefile


## [0.1.8] - 2026-02-24

### Summary

feat(examples): code relationship mapping with 2 supporting modules

### Config

- config: update goal.yaml

### Other

- update .env.example


## [0.1.7] - 2026-02-24

### Summary

refactor(build): configuration management system

### Test

- docker: update Dockerfile
- update tests/test_integration.py
- update tests/test_meshpi.py

### Build

- update pyproject.toml

### Other

- build: update Makefile
- config: update ci.yml
- docker: update Dockerfile
- scripts: update entrypoint.sh
- update fake_applier.py
- update meshpi/__init__.py
- update meshpi/systemd.py


## [0.1.6] - 2026-02-24

### Summary

refactor(docs): docs module improvements

### Docs

- docs: update README

### Build

- update pyproject.toml

### Other

- update meshpi/systemd.py


## [0.1.5] - 2026-02-24

### Summary

chore(config): config module improvements

### Build

- update pyproject.toml


## [0.1.4] - 2026-02-24

### Summary

feat(docs): CLI interface improvements

### Docs

- docs: update README

### Test

- update tests/test_meshpi.py

### Build

- update pyproject.toml

### Other

- update meshpi/__init__.py
- update meshpi/cli.py
- update meshpi/dashboard/__init__.py
- update meshpi/diagnostics.py
- update meshpi/host.py
- update meshpi/registry.py
- update meshpi/systemd.py


## [0.1.3] - 2026-02-24

### Summary

refactor(goal): CLI interface improvements

### Build

- update pyproject.toml

### Config

- config: update goal.yaml

### Other

- update meshpi/__init__.py
- update meshpi/cli.py
- update meshpi/client.py
- update meshpi/diagnostics.py
- update meshpi/hardware/__init__.py
- update meshpi/hardware/applier.py
- update meshpi/hardware/profiles.py
- update meshpi/host.py
- update meshpi/llm_agent.py
- update meshpi/registry.py


## [0.1.2] - 2026-02-24

### Summary

feat(goal): CLI interface improvements

### Config

- config: update goal.yaml

### Other

- update meshpi/applier.py
- update meshpi/cli.py
- update meshpi/client.py
- update meshpi/config.py
- update meshpi/crypto.py
- update meshpi/host.py
- update meshpi/pendrive.py


## [0.1.1] - 2026-02-24

### Summary

feat(goal): CLI interface improvements

### Docs

- docs: update README

### Test

- update tests/test_meshpi.py

### Build

- update pyproject.toml

### Config

- config: update goal.yaml

### Other

- update applier.py
- update cli.py
- update client.py
- update config.py
- update crypto.py
- update host.py
- update pendrive.py
- scripts: update project.sh


