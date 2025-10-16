# AppPrecos Android App

Modern Android application for price comparison using NFCe receipt data.

## Features

- QR code scanning for NFCe receipts
- Automatic price extraction via backend API
- Price comparison across multiple markets
- Material Design 3 UI
- Offline support (coming soon)

## Requirements

- Android Studio Hedgehog or later
- JDK 17
- Android SDK 34
- Minimum Android 7.0 (API 24)

## Setup

1. Open this folder (`android/`) in Android Studio
2. Let Gradle sync
3. Update API base URL in `ApiClient.kt`:
   - Emulator: `http://10.0.2.2:5000/api/`
   - Physical device: `http://YOUR_LOCAL_IP:5000/api/`
4. Run on emulator or device

## Project Structure

```
android/
├── app/
│   ├── src/main/
│   │   ├── java/com/appprecos/
│   │   │   ├── MainActivity.kt
│   │   │   ├── api/              # API client & services
│   │   │   ├── data/             # Data models & repository
│   │   │   ├── ui/               # UI components
│   │   │   └── utils/            # Utilities
│   │   ├── res/                  # Resources
│   │   └── AndroidManifest.xml
│   └── build.gradle.kts
├── gradle/
└── build.gradle.kts
```

## Building

### Debug Build
```bash
./gradlew assembleDebug
```

### Release Build
```bash
./gradlew assembleRelease
```

## Dependencies

- AndroidX Core & AppCompat
- Material Design Components 3
- Retrofit (REST API client)
- Kotlin Coroutines
- ViewModel & LiveData
- CameraX (QR scanning)
- ML Kit Barcode Scanning

## Integration with Backend

See `../docs/ANDROID_INTEGRATION.md` for detailed integration guide.

## Configuration

**API Base URL:** Configure in `api/ApiClient.kt`

**Network Security:** See `res/xml/network_security_config.xml`

## Testing

Run unit tests:
```bash
./gradlew test
```

Run instrumented tests:
```bash
./gradlew connectedAndroidTest
```

