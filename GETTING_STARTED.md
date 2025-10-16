# Getting Started with AppPrecos

Quick guide to get up and running with AppPrecos development.

## Prerequisites

### Required Software

- **Python 3.8+** - [Download](https://www.python.org/downloads/)
- **Android Studio** - [Download](https://developer.android.com/studio)
- **Git** - [Download](https://git-scm.com/)
- **JDK 17** - Usually bundled with Android Studio

### Verify Installation

```bash
python --version        # Should be 3.8+
java -version          # Should be 17+
git --version          # Any recent version
```

---

## Setup (Windows)

### Automated Setup

```bash
# Run the setup script
scripts\setup_dev.bat
```

This will:
- Create Python virtual environment
- Install all backend dependencies
- Install Playwright browser
- Initialize database
- Prompt you to open Android Studio

### Manual Setup

#### 1. Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright Chromium
playwright install chromium

# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

#### 2. Android Setup

```bash
# Open Android Studio
# File → Open → Select AppPrecos/android/ folder
# Wait for Gradle sync
# Build → Make Project
```

---

## Running the Application

### Step 1: Start Backend Server

**Option A: Using script**
```bash
scripts\run_backend.bat
```

**Option B: Manual**
```bash
cd backend
venv\Scripts\activate  # If not already activated
python app.py
```

**Verify:** Open browser to `http://localhost:5000` - should see API info

### Step 2: Configure Android App

1. Open `android/app/src/main/java/com/appprecos/api/ApiClient.kt`
2. Update `BASE_URL`:
   ```kotlin
   // For emulator
   private const val BASE_URL = "http://10.0.2.2:5000/api/"
   
   // For physical device (replace with your computer's IP)
   private const val BASE_URL = "http://192.168.1.XXX:5000/api/"
   ```

### Step 3: Run Android App

1. Open Android Studio
2. Select device/emulator
3. Click Run (or Shift+F10)

---

## First Test

### Test the NFCe Crawler

```bash
# Run standalone crawler test
scripts\test_crawler.bat
```

This will:
- Open a browser
- Navigate to sample NFCe receipt
- Extract all 17 products with NCM codes
- Save to Excel file `ncm_codes.xlsx`

**Expected result:** Excel file with product data in ~15 seconds

### Test the Backend API

With backend running, open another terminal:

```bash
# Test API is responding
curl http://localhost:5000/

# Create a market
curl -X POST http://localhost:5000/api/markets ^
  -H "Content-Type: application/json" ^
  -d "{\"name\":\"Test Market\",\"address\":\"Test Address\"}"

# Get all markets
curl http://localhost:5000/api/markets
```

### Test from Android

1. Ensure backend is running
2. Run Android app
3. Check logcat for network requests
4. Verify connection to API

---

## Common Issues & Solutions

### Backend Issues

**Error: "ModuleNotFoundError"**
```bash
# Make sure virtual environment is activated
cd backend
venv\Scripts\activate
pip install -r requirements.txt
```

**Error: "Playwright not installed"**
```bash
playwright install chromium
```

**Error: "Port 5000 already in use"**
```bash
# Kill process on port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Or change port in app.py
```

### Android Issues

**Error: "Unable to resolve dependency"**
```
- File → Invalidate Caches → Restart
- Sync Project with Gradle Files
```

**Error: "SDK location not found"**
```
Create local.properties in android/ folder:
sdk.dir=C:\\Users\\YourName\\AppData\\Local\\Android\\Sdk
```

**Error: "Cannot connect to backend"**
```
- Verify backend is running
- Check firewall settings
- Verify API URL (10.0.2.2 for emulator)
- For physical device, use computer's local IP
```

### Network Issues

**Android can't reach backend:**

1. **Emulator:** Use `10.0.2.2` (emulator's localhost)
2. **Physical Device:** 
   - Find your computer's IP: `ipconfig`
   - Use that IP in ApiClient.kt
   - Ensure both devices on same WiFi

3. **Add network security config** (see `docs/ANDROID_INTEGRATION.md`)

---

## Development Workflow

### Typical Development Session

```bash
# Terminal 1: Backend
cd backend
venv\Scripts\activate
python app.py

# Terminal 2: Android Studio
# Open android/ folder
# Make changes
# Run app

# Terminal 3: Git
git status
git add .
git commit -m "Add feature X"
git push
```

---

## Project Structure Overview

```
AppPrecos/
│
├── android/           → Open THIS in Android Studio
├── backend/           → Start backend from HERE
├── docs/              → Read documentation HERE
├── scripts/           → Run helper scripts HERE
│
├── README.md          → Main project README
└── GETTING_STARTED.md → This file
```

---

## Next Steps

### For Backend Development
1. ✅ Backend is ready!
2. Add more API endpoints as needed
3. Optimize crawler performance
4. Add error handling for edge cases

### For Android Development
1. Implement QR code scanner
2. Create API client (see `docs/ANDROID_INTEGRATION.md`)
3. Build UI screens:
   - Home screen
   - QR scanner
   - Product list
   - Price comparison
   - Market management

### For Testing
1. Test NFCe extraction with different receipts
2. Test API endpoints
3. Test Android UI components
4. Integration testing (Android → Backend)

---

## Learning Resources

### Flask
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/en/tutorial/)

### Android
- [Android Kotlin Docs](https://developer.android.com/kotlin)
- [Material Design 3](https://m3.material.io/)
- [Retrofit Guide](https://square.github.io/retrofit/)

### Playwright
- [Playwright Python](https://playwright.dev/python/docs/intro)

---

## Support

- **Documentation:** See `docs/` folder
- **Issues:** Open GitHub issue
- **Questions:** Check docs first, then ask

---

## Quick Reference

### Start Backend
```bash
scripts\run_backend.bat
```

### Test Crawler
```bash
scripts\test_crawler.bat
```

### Open Android
```
Android Studio → Open → AppPrecos/android/
```

### View API Docs
```
http://localhost:5000/  (with backend running)
```

---

**You're all set! Start developing! 🚀**

