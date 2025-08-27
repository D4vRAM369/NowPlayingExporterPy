# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**NowPlayingExporterPy** is an Android application that integrates Python scripts to extract "Now Playing" history from Android System Intelligence and exports it as CSV files. The app requires root access to copy the database from protected system directories.

### Key Architecture Components

- **Kotlin/Android**: Main UI and logic (`MainActivity`, `RootHelper`)
- **Python Integration**: Uses Chaquo Python plugin to embed Python scripts
- **Root Access**: Uses libsu library for system-level file operations
- **Database Processing**: SQLite database parsing and CSV export functionality

## Development Commands

### Building and Running
```bash
# Clean build
./gradlew clean

# Build debug APK
./gradlew assembleDebug

# Build release APK  
./gradlew assembleRelease

# Build and run tests
./gradlew build

# Install debug build to connected device
./gradlew installDebug

# Uninstall from device
./gradlew uninstallDebug
```

### Testing and Quality
```bash
# Run unit tests
./gradlew test
./gradlew testDebugUnitTest

# Run instrumentation tests (requires connected device)
./gradlew connectedAndroidTest

# Run lint checks
./gradlew lint

# Fix lint issues automatically
./gradlew lintFix

# Update lint baseline
./gradlew updateLintBaseline
```

### Development Workflow
```bash
# Check dependencies
./gradlew androidDependencies

# View source sets
./gradlew sourceSets

# Check signing configuration
./gradlew signingReport

# Run all checks
./gradlew check
```

## Code Architecture

### Main Components

1. **MainActivity.kt** - Primary UI and orchestration
   - Manages export workflow
   - Handles Python module execution
   - Manages file operations and MediaStore integration
   - Root permission validation

2. **RootHelper.kt** - Root access abstraction
   - Shell command execution via libsu
   - Database file discovery and copying
   - Root permission checking

3. **Python Modules** (`app/src/main/python/`)
   - `np_export.py`: SQLite database parsing and CSV export
   - `np_dedupe.py`: Deduplication logic for exported data

### Data Flow
1. App checks for root access and Now Playing database availability
2. RootHelper copies database from system-protected location to app cache
3. Python export module processes SQLite database and generates CSV
4. Optional deduplication removes entries within 10-minute windows
5. Final CSV is moved to Downloads folder via MediaStore API

### Database Search Paths
The app searches for Now Playing databases in:
- `/data/data/com.google.android.as/databases/history_db`
- `/data/user_de/0/com.google.android.as/databases/history_db`  
- `/data/data/com.google.android.as.oss/databases/history_db`
- `/data/user_de/0/com.google.android.as.oss/databases/history_db`
- `/data/data/com.google.intelligence.sense/databases/history_db`

## Development Requirements

- **Android Studio**: AGP 8.5, Kotlin 1.9
- **Target SDK**: 35 (Android 15)
- **Minimum SDK**: 28 (Android 9)
- **Root Access**: Required for database access
- **Chaquo Python**: 15.0.1 for Python integration
- **libsu**: 5.2.2 for root operations

## Key Dependencies

- `com.chaquo.python` - Python integration
- `com.github.topjohnwu.libsu:core` - Root access
- `com.github.topjohnwu.libsu:service` - Root services
- Standard Android libraries (AppCompat, Material Design)

## Build Configuration Notes

- **ABI Filters**: Limited to `arm64-v8a` and `armeabi-v7a` for Chaquo Python compatibility
- **Proguard**: Enabled for release builds with resource shrinking
- **Java Version**: 17 (both source and target compatibility)
- **Repository**: Includes Chaquo Maven repository for Python plugin

## Testing on Device

The app requires:
1. **Rooted Android device** (Magisk, KernelSU, KSU Next, or aPatch)
2. **Now Playing feature active** on the device
3. **Connected device** for `adb install` via Android Studio or Gradle

Test the root functionality before main features, as the app is useless without root access to system databases.
