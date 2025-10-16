# Android Integration Guide

## Overview

This guide shows how to integrate the AppPrecos Android app with the Flask backend.

## Setup Backend Connection

### 1. Create API Client

Create `app/src/main/java/com/appprecos/api/ApiClient.kt`:

```kotlin
package com.appprecos.api

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {
    private const val BASE_URL = "http://10.0.2.2:5000/api/"  // Android emulator
    // For physical device: "http://YOUR_LOCAL_IP:5000/api/"
    // For production: "https://your-backend.com/api/"
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
    
    private val client = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
}
```

### 2. Define Data Models

Create `app/src/main/java/com/appprecos/data/models/`:

```kotlin
// Market.kt
data class Market(
    val id: Int,
    val name: String,
    val address: String,
    val created_at: String
)

// Product.kt
data class Product(
    val number: Int,
    val product: String,
    val ncm: String,
    val quantity: Double? = null,
    val unidade_comercial: String? = null,
    val price: Double? = null
)

// NFCeResponse.kt
data class NFCeResponse(
    val message: String,
    val products: List<Product>,
    val saved_to_market: Int? = null
)

// PriceComparison.kt
data class PriceComparison(
    val market_id: Int,
    val market_name: String,
    val market_address: String,
    val ncm: String,
    val price: Double,
    val unidade_comercial: String,
    val last_updated: String
)
```

### 3. Define API Service

Create `app/src/main/java/com/appprecos/api/ApiService.kt`:

```kotlin
package com.appprecos.api

import com.appprecos.data.models.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    
    // Markets
    @GET("markets")
    suspend fun getMarkets(): Response<List<Market>>
    
    @POST("markets")
    suspend fun createMarket(@Body market: CreateMarketRequest): Response<Market>
    
    // NFCe Extraction
    @POST("nfce/extract")
    suspend fun extractNFCe(@Body request: NFCeRequest): Response<NFCeResponse>
    
    // Price Comparison
    @GET("price-comparison/{ncm}")
    suspend fun comparePrices(@Path("ncm") ncm: String): Response<PriceComparisonResponse>
    
    // Unique Products
    @GET("unique-products")
    suspend fun getUniqueProducts(@Query("market_id") marketId: Int? = null): Response<List<UniqueProduct>>
    
    // Statistics
    @GET("stats")
    suspend fun getStats(): Response<Stats>
}

// Request/Response models
data class CreateMarketRequest(val name: String, val address: String)
data class NFCeRequest(val url: String, val market_id: Int, val save: Boolean)
data class PriceComparisonResponse(
    val ncm: String,
    val markets_count: Int,
    val cheapest_price: Double?,
    val results: List<PriceComparison>
)
```

### 4. Repository Pattern

Create `app/src/main/java/com/appprecos/data/repository/AppRepository.kt`:

```kotlin
package com.appprecos.data.repository

import com.appprecos.api.ApiClient
import com.appprecos.api.ApiService
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class AppRepository {
    private val apiService = ApiClient.retrofit.create(ApiService::class.java)
    
    suspend fun extractNFCe(url: String, marketId: Int, save: Boolean) = withContext(Dispatchers.IO) {
        try {
            val request = NFCeRequest(url, marketId, save)
            val response = apiService.extractNFCe(request)
            if (response.isSuccessful) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Error: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun comparePrices(ncm: String) = withContext(Dispatchers.IO) {
        try {
            val response = apiService.comparePrices(ncm)
            if (response.isSuccessful) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Error: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // Add other methods...
}
```

### 5. ViewModel Usage

Create `app/src/main/java/com/appprecos/ui/viewmodels/MainViewModel.kt`:

```kotlin
package com.appprecos.ui.viewmodels

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.appprecos.data.repository.AppRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.launch

class MainViewModel(
    private val repository: AppRepository = AppRepository()
) : ViewModel() {
    
    private val _nfceState = MutableStateFlow<NFCeState>(NFCeState.Idle)
    val nfceState: StateFlow<NFCeState> = _nfceState
    
    fun extractNFCe(url: String, marketId: Int) {
        viewModelScope.launch {
            _nfceState.value = NFCeState.Loading
            
            repository.extractNFCe(url, marketId, save = true)
                .onSuccess { response ->
                    _nfceState.value = NFCeState.Success(response.products)
                }
                .onFailure { error ->
                    _nfceState.value = NFCeState.Error(error.message ?: "Unknown error")
                }
        }
    }
}

sealed class NFCeState {
    object Idle : NFCeState()
    object Loading : NFCeState()
    data class Success(val products: List<Product>) : NFCeState()
    data class Error(val message: String) : NFCeState()
}
```

---

## QR Code Scanning

### Add Dependencies

In `android/app/build.gradle.kts`:

```kotlin
dependencies {
    // Existing dependencies...
    
    // Network
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    
    // QR Code scanning
    implementation("com.google.mlkit:barcode-scanning:17.2.0")
    implementation("androidx.camera:camera-camera2:1.3.1")
    implementation("androidx.camera:camera-lifecycle:1.3.1")
    implementation("androidx.camera:camera-view:1.3.1")
    
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
}
```

### QR Scanner Implementation

```kotlin
class QRScannerActivity : AppCompatActivity() {
    
    private fun startCamera() {
        val cameraProviderFuture = ProcessCameraProvider.getInstance(this)
        
        cameraProviderFuture.addListener({
            val cameraProvider = cameraProviderFuture.get()
            
            val imageAnalysis = ImageAnalysis.Builder()
                .build()
                .also {
                    it.setAnalyzer(cameraExecutor, QRCodeAnalyzer { qrCode ->
                        // Extract NFCe URL from QR code
                        handleQRCode(qrCode)
                    })
                }
            
            // Bind to lifecycle
            cameraProvider.bindToLifecycle(
                this, cameraSelector, imageAnalysis
            )
        }, ContextCompat.getMainExecutor(this))
    }
    
    private fun handleQRCode(qrCode: String) {
        // QR code contains NFCe URL
        if (qrCode.contains("nfce.fazenda")) {
            viewModel.extractNFCe(qrCode, selectedMarketId)
        }
    }
}
```

---

## Testing

### Backend Testing

```bash
cd backend

# Run with test database
export FLASK_ENV=testing
python -m pytest tests/

# Manual API testing
curl http://localhost:5000/api/markets
```

### Android Testing

```kotlin
// Unit test example
@Test
fun testApiClient() {
    runBlocking {
        val response = repository.getMarkets()
        assertTrue(response.isSuccess)
    }
}
```

---

## Network Configuration

### Allow HTTP in Android (Development Only)

Add to `android/app/src/main/res/xml/network_security_config.xml`:

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <domain-config cleartextTrafficPermitted="true">
        <domain includeSubdomains="true">10.0.2.2</domain>
        <domain includeSubdomains="true">localhost</domain>
        <domain includeSubdomains="true">192.168.1.x</domain>
    </domain-config>
</network-security-config>
```

Add to `AndroidManifest.xml`:
```xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
```

---

## Performance Tips

### Backend
- Use Gunicorn with 4 workers
- Enable response caching
- Add database indexes
- Use connection pooling

### Android
- Cache API responses locally
- Use WorkManager for background sync
- Implement offline mode
- Add loading indicators (NFCe extraction takes 10-15s)

---

## Security Checklist

- [ ] Use HTTPS in production
- [ ] Add API authentication (JWT)
- [ ] Validate all inputs
- [ ] Rate limit NFCe extraction
- [ ] Sanitize user data
- [ ] Secure database credentials
- [ ] Use ProGuard for Android release
- [ ] Implement certificate pinning

