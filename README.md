# AppPrecos

A modern Android application built with Kotlin and AndroidX libraries.

## Features

- Clean architecture
- Material Design 3
- ViewBinding for type-safe view access
- Kotlin Coroutines for asynchronous operations
- Lifecycle-aware components
- Modern Android development practices

## Requirements

- Android Studio Hedgehog or later
- JDK 17
- Android SDK 34
- Minimum SDK 24 (Android 7.0)

## Project Structure

```
AppPrecos/
├── app/
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/appprecos/
│   │   │   │   └── MainActivity.kt
│   │   │   ├── res/
│   │   │   │   ├── layout/
│   │   │   │   ├── values/
│   │   │   │   └── xml/
│   │   │   └── AndroidManifest.xml
│   │   └── test/
│   └── build.gradle.kts
├── gradle/
├── build.gradle.kts
├── settings.gradle.kts
└── gradle.properties
```

## Setup

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd AppPrecos
   ```

2. Open the project in Android Studio

3. Let Gradle sync and download dependencies

4. Run the app on an emulator or physical device

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

- **AndroidX Core**: Core functionality and Kotlin extensions
- **AppCompat**: Backward compatibility
- **Material Components**: Material Design components
- **ConstraintLayout**: Flexible layout system
- **Lifecycle Components**: Lifecycle-aware components
- **Coroutines**: Asynchronous programming

## Configuration

- **Application ID**: `com.appprecos`
- **Minimum SDK**: 24 (Android 7.0)
- **Target SDK**: 34 (Android 14)
- **Compile SDK**: 34

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions or support, please open an issue in the GitHub repository.

