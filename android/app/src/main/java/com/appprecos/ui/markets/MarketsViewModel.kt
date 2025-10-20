package com.appprecos.ui.markets

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.appprecos.data.model.Market
import com.appprecos.data.model.MarketProductsResponse
import com.appprecos.data.repository.AppRepository
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class MarketsViewModel(
    private val repository: AppRepository = AppRepository()
) : ViewModel() {
    
    private val _marketsState = MutableStateFlow<MarketsState>(MarketsState.Loading)
    val marketsState: StateFlow<MarketsState> = _marketsState.asStateFlow()
    
    private val _selectedMarketProducts = MutableStateFlow<MarketProductsResponse?>(null)
    val selectedMarketProducts: StateFlow<MarketProductsResponse?> = _selectedMarketProducts.asStateFlow()
    
    private val _searchQuery = MutableStateFlow("")
    val searchQuery: StateFlow<String> = _searchQuery.asStateFlow()
    
    private var allMarkets: List<Market> = emptyList()
    
    fun loadMarkets() {
        viewModelScope.launch {
            _marketsState.value = MarketsState.Loading
            
            repository.getMarkets()
                .onSuccess { markets ->
                    allMarkets = markets
                    if (markets.isEmpty()) {
                        _marketsState.value = MarketsState.Error(
                            "No markets found.\nScan a QR code to add markets!"
                        )
                    } else {
                        filterMarkets(_searchQuery.value)
                    }
                }
                .onFailure { error ->
                    _marketsState.value = MarketsState.Error(
                        error.message ?: "Failed to load markets"
                    )
                }
        }
    }
    
    fun searchMarkets(query: String) {
        _searchQuery.value = query
        filterMarkets(query)
    }
    
    private fun filterMarkets(query: String) {
        val filtered = if (query.isBlank()) {
            allMarkets
        } else {
            allMarkets.filter { market ->
                market.name.contains(query, ignoreCase = true) ||
                market.address.contains(query, ignoreCase = true) ||
                market.market_id.contains(query, ignoreCase = true)
            }
        }
        _marketsState.value = MarketsState.Success(filtered)
    }
    
    fun refreshMarkets() {
        loadMarkets()
    }
    
    fun loadMarketProducts(marketId: String) {
        viewModelScope.launch {
            repository.getMarketProducts(marketId)
                .onSuccess { response ->
                    _selectedMarketProducts.value = response
                }
                .onFailure { error ->
                    // Handle error
                }
        }
    }
}

sealed class MarketsState {
    object Loading : MarketsState()
    data class Success(val markets: List<Market>) : MarketsState()
    data class Error(val message: String) : MarketsState()
}

