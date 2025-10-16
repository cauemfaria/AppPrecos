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
    
    fun loadMarkets() {
        viewModelScope.launch {
            _marketsState.value = MarketsState.Loading
            
            repository.getMarkets()
                .onSuccess { markets ->
                    if (markets.isEmpty()) {
                        _marketsState.value = MarketsState.Error(
                            "No markets found.\nScan a QR code to add markets!"
                        )
                    } else {
                        _marketsState.value = MarketsState.Success(markets)
                    }
                }
                .onFailure { error ->
                    _marketsState.value = MarketsState.Error(
                        error.message ?: "Failed to load markets"
                    )
                }
        }
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

