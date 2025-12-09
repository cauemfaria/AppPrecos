package com.appprecos.data.repository

import com.appprecos.api.ApiClient
import com.appprecos.data.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

class AppRepository {
    private val apiService = ApiClient.apiService
    
    // ========== NFCe Extraction (Sync mode for backward compatibility) ==========
    
    suspend fun extractNFCe(url: String): Result<Any> = withContext(Dispatchers.IO) {
        try {
            val request = NFCeRequest(url = url, save = true)
            val response = apiService.extractNFCe(request)
            
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else if (response.code() == 409) {
                val errorBody = response.errorBody()?.string()
                if (errorBody != null) {
                    val gson = com.google.gson.Gson()
                    val errorData = gson.fromJson(errorBody, NFCeError::class.java)
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
    
    // ========== Markets ==========
    
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
    
    // ========== Product Search ==========
    
    suspend fun searchProducts(query: String): Result<ProductSearchResponse> = withContext(Dispatchers.IO) {
        try {
            val response = apiService.searchProducts(query)
            if (response.isSuccessful && response.body() != null) {
                Result.success(response.body()!!)
            } else {
                Result.failure(Exception("Error: ${response.code()}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    // ========== Product Comparison ==========
    
    suspend fun compareProducts(
        products: List<CompareProduct>,
        marketIds: List<String>
    ): Result<CompareResponse> = withContext(Dispatchers.IO) {
        try {
            val request = CompareRequest(products = products, market_ids = marketIds)
            val response = apiService.compareProducts(request)
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
    val errorData: NFCeError? = null
) : Exception(message)
