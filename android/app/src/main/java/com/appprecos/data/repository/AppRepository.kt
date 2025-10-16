package com.appprecos.data.repository

import com.appprecos.api.ApiClient
import com.appprecos.data.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class AppRepository {
    private val apiService = ApiClient.apiService
    
    suspend fun extractNFCe(url: String): Result<Any> = withContext(Dispatchers.IO) {
        try {
            val request = NFCeRequest(url = url, save = true)
            val response = apiService.extractNFCe(request)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else if (response.code() == 409) {
                // Duplicate URL - return error details
                val errorBody = response.errorBody()?.string()
                if (errorBody != null) {
                    val gson = com.google.gson.Gson()
                    val errorData = gson.fromJson(errorBody, com.appprecos.data.model.NFCeError::class.java)
                    Result.failure(DuplicateURLException(errorData.message, errorData))
                } else {
                    Result.failure(DuplicateURLException("NFCe already processed", null))
                }
            } else {
                Result.failure(Exception("Error: ${response.code()} - ${response.message()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun getMarkets(): Result<List<Market>> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getMarkets()
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Error: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun getMarketProducts(marketId: String): Result<MarketProductsResponse> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.getMarketProducts(marketId)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Error: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

class DuplicateURLException(
    message: String,
    val errorData: com.appprecos.data.model.NFCeError? = null
) : Exception(message)

