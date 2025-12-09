package com.appprecos.data.model

// ========== NFCe Extraction ==========

data class NFCeRequest(
    val url: String,
    val save: Boolean = true
)

data class NFCeAsyncRequest(
    val url: String,
    val save: Boolean = true,
    val async: Boolean = true
)

data class NFCeResponse(
    val message: String,
    val record_id: Int? = null,
    val market: MarketInfo,
    val products: List<Product>,
    val statistics: Statistics
)

data class NFCeAsyncResponse(
    val message: String,
    val status: String,
    val record_id: Int
)

data class NFCeStatusResponse(
    val record_id: Int,
    val status: String,
    val market_id: String?,
    val market_name: String?,
    val products_count: Int,
    val error_message: String?,
    val processed_at: String
)

data class NFCeError(
    val error: String,
    val message: String,
    val processed_at: String,
    val market_id: String,
    val products_count: Int
)

// ========== Market & Products ==========

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
    val product_name: String? = null,
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
    val ean: String? = null,
    val product_name: String? = null,
    val quantity: Double,
    val unidade_comercial: String,
    val price: Double,
    val nfce_url: String?,
    val purchase_date: String,
    val created_at: String,
    val last_updated: String? = null
)

// ========== Product Search ==========

data class ProductSearchResponse(
    val query: String,
    val results: List<ProductSearchResult>,
    val total: Int
)

data class ProductSearchResult(
    val product_name: String,
    val ean: String?,
    val ncm: String,
    val unidade_comercial: String,
    val markets_count: Int,
    val min_price: Double,
    val max_price: Double
)

// ========== Product Comparison ==========

data class CompareRequest(
    val products: List<CompareProduct>,
    val market_ids: List<String>
)

data class CompareProduct(
    val product_name: String,
    val ean: String?,
    val ncm: String
)

data class CompareResponse(
    val markets: Map<String, String>, // market_id -> market_name
    val comparison: List<ComparisonRow>
)

data class ComparisonRow(
    val product_name: String,
    val ean: String?,
    val ncm: String,
    val prices: Map<String, Any?>, // market_id -> price (null if not found, Double otherwise)
    val min_price: Double?,
    val max_price: Double?,
    val all_equal: Boolean
) {
    /**
     * Get price for a market, handling Gson's type conversion
     */
    fun getPriceForMarket(marketId: String): Double? {
        val value = prices[marketId] ?: return null
        return when (value) {
            is Number -> value.toDouble()
            else -> null
        }
    }
}
