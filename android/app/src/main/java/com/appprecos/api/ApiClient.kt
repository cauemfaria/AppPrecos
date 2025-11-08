package com.appprecos.api

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object ApiClient {
    // Production backend URL (Render)
    // TODO: Replace with your actual Render URL after deployment
    private const val PRODUCTION_URL = "https://appprecos-backend.onrender.com/api/"
    
    // Development URLs
    private const val EMULATOR_URL = "http://10.0.2.2:5000/api/"
    private const val LOCALHOST_URL = "http://YOUR_COMPUTER_IP:5000/api/"
    
    // Switch between development and production
    // Set to true for production, false for local development
    private const val USE_PRODUCTION = true
    
    private val BASE_URL = if (USE_PRODUCTION) PRODUCTION_URL else EMULATOR_URL
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = if (USE_PRODUCTION) {
            HttpLoggingInterceptor.Level.BASIC  // Less verbose in production
        } else {
            HttpLoggingInterceptor.Level.BODY   // Full logging in development
        }
    }
    
    private val client = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .connectTimeout(120, TimeUnit.SECONDS)  // Increased for Playwright operations
        .readTimeout(120, TimeUnit.SECONDS)     // Increased for NFCe extraction
        .writeTimeout(120, TimeUnit.SECONDS)
        .build()
    
    val retrofit: Retrofit = Retrofit.Builder()
        .baseUrl(BASE_URL)
        .client(client)
        .addConverterFactory(GsonConverterFactory.create())
        .build()
    
    val apiService: ApiService = retrofit.create(ApiService::class.java)
}

