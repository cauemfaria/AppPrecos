package com.appprecos.api

import com.appprecos.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    
    @POST("nfce/extract")
    suspend fun extractNFCe(@Body request: NFCeRequest): Response<NFCeResponse>
    
    @GET("markets")
    suspend fun getMarkets(): Response<List<Market>>
    
    @GET("markets/{market_id}/products")
    suspend fun getMarketProducts(@Path("market_id") marketId: String): Response<MarketProductsResponse>
}

