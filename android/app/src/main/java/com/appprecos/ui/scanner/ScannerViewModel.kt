package com.appprecos.ui.scanner

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.appprecos.data.repository.AppRepository
import com.appprecos.data.repository.DuplicateURLException
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ScannerViewModel(
    private val repository: AppRepository = AppRepository()
) : ViewModel() {
    
    private val _scanState = MutableStateFlow<ScanState>(ScanState.Idle)
    val scanState: StateFlow<ScanState> = _scanState.asStateFlow()
    
    fun processNFCe(url: String) {
        viewModelScope.launch {
            _scanState.value = ScanState.Processing
            
            repository.extractNFCe(url)
                .onSuccess { response ->
                    if (response is com.appprecos.data.model.NFCeResponse) {
                        _scanState.value = ScanState.Success(
                            marketName = response.market.name,
                            marketId = response.market.market_id,
                            productsCount = response.statistics.products_saved_to_main,
                            action = response.market.action
                        )
                    }
                }
                .onFailure { error ->
                    if (error is com.appprecos.data.repository.DuplicateURLException) {
                        val errorData = error.errorData
                        _scanState.value = ScanState.Duplicate(
                            processedAt = errorData?.processed_at ?: "Unknown",
                            marketId = errorData?.market_id ?: "",
                            productsCount = errorData?.products_count ?: 0
                        )
                    } else {
                        _scanState.value = ScanState.Error(
                            error.message ?: "Unknown error"
                        )
                    }
                }
        }
    }
}

sealed class ScanState {
    object Idle : ScanState()
    object Processing : ScanState()
    data class Success(
        val marketName: String,
        val marketId: String,
        val productsCount: Int,
        val action: String  // "created" or "matched"
    ) : ScanState()
    data class Duplicate(
        val processedAt: String,
        val marketId: String,
        val productsCount: Int
    ) : ScanState()
    data class Error(val message: String) : ScanState()
}

