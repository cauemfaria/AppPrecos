package com.appprecos.ui.scanner

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.appprecos.data.repository.AppRepository
import com.appprecos.data.repository.DuplicateURLException
import com.appprecos.data.service.QrProcessingManager
import com.appprecos.data.service.QrProcessingItem
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class ScannerViewModel(
    private val repository: AppRepository = AppRepository()
) : ViewModel() {
    
    private val _scanState = MutableStateFlow<ScanState>(ScanState.Idle)
    val scanState: StateFlow<ScanState> = _scanState.asStateFlow()
    
    // Processing queue from QrProcessingManager
    val processingQueue: StateFlow<List<QrProcessingItem>> = QrProcessingManager.processingQueue
    
    /**
     * Add URL to background processing queue (for camera scans)
     */
    fun addToQueue(url: String): Boolean {
        return QrProcessingManager.addToQueue(url)
    }
    
    /**
     * Remove item from queue
     */
    fun removeFromQueue(url: String) {
        QrProcessingManager.removeFromQueue(url)
    }
    
    /**
     * Process NFCe synchronously (for manual URL input)
     */
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
                    if (error is DuplicateURLException) {
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
    
    fun resetState() {
        _scanState.value = ScanState.Idle
    }
}

sealed class ScanState {
    object Idle : ScanState()
    object Processing : ScanState()
    data class Success(
        val marketName: String,
        val marketId: String,
        val productsCount: Int,
        val action: String
    ) : ScanState()
    data class Duplicate(
        val processedAt: String,
        val marketId: String,
        val productsCount: Int
    ) : ScanState()
    data class Error(val message: String) : ScanState()
}
