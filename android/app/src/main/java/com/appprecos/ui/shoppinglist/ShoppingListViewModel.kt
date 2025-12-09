package com.appprecos.ui.shoppinglist

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.appprecos.data.local.AppDatabase
import com.appprecos.data.local.ShoppingListItem
import com.appprecos.data.model.*
import com.appprecos.data.repository.AppRepository
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

class ShoppingListViewModel(application: Application) : AndroidViewModel(application) {
    
    private val dao = AppDatabase.getDatabase(application).shoppingListDao()
    private val repository = AppRepository()
    
    // Shopping list items
    val shoppingList: Flow<List<ShoppingListItem>> = dao.getAllItems()
    
    // Selected markets for comparison
    private val _selectedMarketIds = MutableStateFlow<Set<String>>(emptySet())
    val selectedMarketIds: StateFlow<Set<String>> = _selectedMarketIds.asStateFlow()
    
    // Available markets
    private val _markets = MutableStateFlow<List<Market>>(emptyList())
    val markets: StateFlow<List<Market>> = _markets.asStateFlow()
    
    // Search results
    private val _searchResults = MutableStateFlow<List<ProductSearchResult>>(emptyList())
    val searchResults: StateFlow<List<ProductSearchResult>> = _searchResults.asStateFlow()
    
    // Search loading state
    private val _isSearching = MutableStateFlow(false)
    val isSearching: StateFlow<Boolean> = _isSearching.asStateFlow()
    
    // Comparison results
    private val _comparisonResult = MutableStateFlow<CompareResponse?>(null)
    val comparisonResult: StateFlow<CompareResponse?> = _comparisonResult.asStateFlow()
    
    // Loading state
    private val _isLoading = MutableStateFlow(false)
    val isLoading: StateFlow<Boolean> = _isLoading.asStateFlow()
    
    // Error state
    private val _error = MutableStateFlow<String?>(null)
    val error: StateFlow<String?> = _error.asStateFlow()
    
    init {
        loadMarkets()
    }
    
    fun loadMarkets() {
        viewModelScope.launch {
            repository.getMarkets()
                .onSuccess { _markets.value = it }
                .onFailure { _error.value = it.message }
        }
    }
    
    fun searchProducts(query: String) {
        if (query.length < 2) {
            _searchResults.value = emptyList()
            return
        }
        
        viewModelScope.launch {
            _isSearching.value = true
            repository.searchProducts(query)
                .onSuccess { _searchResults.value = it.results }
                .onFailure { 
                    _error.value = it.message
                    _searchResults.value = emptyList()
                }
            _isSearching.value = false
        }
    }
    
    fun clearSearchResults() {
        _searchResults.value = emptyList()
    }
    
    fun addToShoppingList(product: ProductSearchResult) {
        viewModelScope.launch {
            // Check if already exists
            val exists = if (product.ean != null && product.ean != "SEM GTIN") {
                dao.existsByEan(product.ean)
            } else {
                dao.existsByNcmAndName(product.ncm, product.product_name)
            }
            
            if (!exists) {
                val item = ShoppingListItem(
                    productName = product.product_name,
                    ean = product.ean ?: "SEM GTIN",
                    ncm = product.ncm,
                    unidadeComercial = product.unidade_comercial
                )
                dao.insert(item)
            }
        }
    }
    
    fun removeFromShoppingList(item: ShoppingListItem) {
        viewModelScope.launch {
            dao.delete(item)
        }
    }
    
    fun clearShoppingList() {
        viewModelScope.launch {
            dao.deleteAll()
        }
    }
    
    companion object {
        const val MAX_MARKETS_FOR_COMPARISON = 5
    }
    
    fun toggleMarketSelection(marketId: String): Boolean {
        val current = _selectedMarketIds.value.toMutableSet()
        if (marketId in current) {
            current.remove(marketId)
            _selectedMarketIds.value = current
            return true
        } else {
            // Check if we've reached the limit
            if (current.size >= MAX_MARKETS_FOR_COMPARISON) {
                _error.value = "Máximo de $MAX_MARKETS_FOR_COMPARISON mercados para comparação"
                return false
            }
            current.add(marketId)
            _selectedMarketIds.value = current
            return true
        }
    }
    
    fun isMarketSelected(marketId: String): Boolean {
        return marketId in _selectedMarketIds.value
    }
    
    fun compareProducts(items: List<ShoppingListItem>) {
        val marketIds = _selectedMarketIds.value.toList()
        
        if (marketIds.isEmpty()) {
            _error.value = "Selecione pelo menos um mercado"
            return
        }
        
        if (items.isEmpty()) {
            _error.value = "Adicione produtos à lista primeiro"
            return
        }
        
        viewModelScope.launch {
            _isLoading.value = true
            
            val compareProducts = items.map { item ->
                CompareProduct(
                    product_name = item.productName,
                    ean = if (item.ean != "SEM GTIN") item.ean else null,
                    ncm = item.ncm
                )
            }
            
            repository.compareProducts(compareProducts, marketIds)
                .onSuccess { _comparisonResult.value = it }
                .onFailure { _error.value = it.message }
            
            _isLoading.value = false
        }
    }
    
    fun clearComparison() {
        _comparisonResult.value = null
    }
    
    fun clearError() {
        _error.value = null
    }
}

