# TODO

## ✅ Completed Tasks (2026-02-24)

### Advanced Hardware Management System
- [x] **Hardware Catalog System**: 
  - Implemented `meshpi hw catalog` with advanced filtering
  - Added category, tag, and popularity filters
  - Multiple output formats (table, JSON, list)
  - Categorized browsing with examples
- [x] **Quick Install Wizard**:
  - Interactive hardware installation with `meshpi hw quick-install`
  - Category-based selection interface
  - Support for device groups and remote targets
  - Multi-profile selection with confirmation
- [x] **Device Groups Management**:
  - Complete group management system with `meshpi group` commands
  - Group creation, device addition, listing, and execution
  - Batch hardware installation on groups
  - Group-based command execution
- [x] **SSH Remote Hardware Control**:
  - Full remote hardware management via SSH
  - Remote profile search, installation, and creation
  - Custom profile management on remote devices
  - Integration with existing SSH management system
- [x] **Enhanced Profile System**:
  - Custom profile creation wizard
  - Import/export functionality (YAML/JSON)
  - Profile deletion and management
  - Integration with SSH and group systems

### Repository Organization
- [x] **Repository Structure Reorganization**: 
  - Created `test/` directory for test scripts
  - Created `scripts/` directory for tooling scripts
  - Moved 8 test scripts from root to `test/`
  - Moved 7 tooling scripts from root to `scripts/`
- [x] **Script Migration**: Updated all documentation references
- [x] **Python Conversion**: Converted 3 shell scripts to Python:
  - `project.sh` → `scripts/project.py`
  - `monitor-repair.sh` → `scripts/monitor-repair.py`
  - `show-repair-status.sh` → `scripts/show-repair-status.py`
- [x] **Documentation Updates**:
  - Updated README.md with repository organization section
  - Updated CHANGELOG.md with v0.1.24 entry
  - Updated all script references in documentation
  - Added HARDWARE-GROUP-MANAGEMENT.md and SSH-HARDWARE-MANAGEMENT.md

## 🎯 Current Tasks

### High Priority
- [ ] **Hardware Profile Validation**: Add validation for custom profiles before installation
- [ ] **Group Synchronization**: Implement group state synchronization across multiple hosts
- [ ] **SSH Connection Pooling**: Optimize SSH connections for better performance with large groups

### Medium Priority
- [ ] **Hardware Dependency Resolution**: Automatic dependency detection and resolution for profiles
- [ ] **Group Templates**: Create reusable group templates for common deployments
- [ ] **Profile Versioning**: Add version control for hardware profiles with rollback capability

### Low Priority
- [ ] **Web UI for Group Management**: Browser-based interface for device group management
- [ ] **Hardware Testing Framework**: Automated testing for hardware profile compatibility
- [ ] **Profile Marketplace**: Community-driven profile sharing platform

## 🐛 Issues Found

<!-- Issues will be automatically added here when using goal -t -->

## 📝 Notes

- This TODO list is managed by Goal
- Use `goal -t` to add detected issues automatically
- Use `goal doctor --todo` to diagnose and track issues

Last updated: 2026-02-24