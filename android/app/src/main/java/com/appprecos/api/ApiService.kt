package com.appprecos.api

import com.appprecos.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    
    // ========== NFCe Extraction ==========
    
    @POST("nfce/extract")
    suspend fun extractNFCe(@Body request: NFCeRequest): Response<NFCeResponse>
    
    @POST("nfce/extract")
    suspend fun extractNFCeAsync(@Body request: NFCeAsyncRequest): Response<NFCeAsyncResponse>
    
    @GET("nfce/status/{record_id}")
    suspend fun getNfceStatus(@Path("record_id") recordId: Int): Response<NFCeStatusResponse>
    
    // ========== Markets ==========
    
    @GET("markets")
    suspend fun getMarkets(): Response<List<Market>>
    
    @GET("markets/{market_id}/products")
    suspend fun getMarketProducts(@Path("market_id") marketId: String): Response<MarketProductsResponse>
    
    // ========== Product Search & Compare ==========
    
    @GET("products/search")
    suspend fun searchProducts(
        @Query("name") name: String,
        @Query("limit") limit: Int = 50
    ): Response<ProductSearchResponse>
    
    @POST("products/compare")
    suspend fun compareProducts(@Body request: CompareRequest): Response<CompareResponse>
}
