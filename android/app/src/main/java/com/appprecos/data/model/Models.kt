package com.appprecos.data.model

data class NFCeRequest(
    val url: String,
    val save: Boolean = true
)

data class NFCeResponse(
    val message: String,
    val market: MarketInfo,
    val products: List<Product>,
    val statistics: Statistics
)

data class NFCeError(
    val error: String,
    val message: String,
    val processed_at: String,
    val market_id: String,
    val products_count: Int
)

data class MarketInfo(
    val id: Int,
    val market_id: String,
    val name: String,
    val address: String,
    val action: String
)

data class Product(
    val number: Int,
    val product: String,
    val ncm: String,
    val quantity: Double,
    val unidade_comercial: String,
    val price: Double
)

data class Statistics(
    val products_saved_to_main: Int,
    val unique_products_created: Int,
    val unique_products_updated: Int,
    val market_action: String
)

data class Market(
    val id: Int,
    val market_id: String,
    val name: String,
    val address: String,
    val created_at: String
)

data class MarketProductsResponse(
    val market: Market,
    val products: List<ProductDetail>,
    val total: Int
)

data class ProductDetail(
    val id: Int,
    val ncm: String,
    val quantity: Double,
    val unidade_comercial: String,
    val price: Double,
    val nfce_url: String?,
    val purchase_date: String,
    val created_at: String,
    val last_updated: String? = null
)

data class Stats(
    val total_markets: Int,
    val total_products_across_all_markets: Int,
    val architecture: String
)

