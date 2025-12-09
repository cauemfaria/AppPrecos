package com.appprecos.data.service

import android.util.Log
import com.appprecos.api.ApiClient
import com.appprecos.data.model.NFCeAsyncRequest
import com.appprecos.data.model.NFCeStatusResponse
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow

/**
 * Singleton manager for background QR code processing.
 * Allows scanning multiple QR codes without waiting for each to complete.
 */
object QrProcessingManager {
    private const val TAG = "QrProcessingManager"
    private const val POLL_INTERVAL_MS = 2000L
    private const val MAX_POLL_ATTEMPTS = 60 // 2 minutes max
    
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val apiService = ApiClient.apiService
    
    // Recently scanned URLs to prevent duplicate scans (debounce)
    private val recentUrls = mutableMapOf<String, Long>()
    private const val DEBOUNCE_MS = 3000L
    
    // Processing queue state
    private val _processingQueue = MutableStateFlow<List<QrProcessingItem>>(emptyList())
    val processingQueue: StateFlow<List<QrProcessingItem>> = _processingQueue.asStateFlow()
    
    /**
     * Add a QR code URL to the processing queue.
     * Returns false if URL was recently scanned (debounce).
     */
    fun addToQueue(url: String): Boolean {
        val now = System.currentTimeMillis()
        
        // Check debounce
        recentUrls[url]?.let { lastTime ->
            if (now - lastTime < DEBOUNCE_MS) {
                Log.d(TAG, "URL debounced (scanned ${now - lastTime}ms ago)")
                return false
            }
        }
        
        // Check if already in queue
        if (_processingQueue.value.any { it.url == url }) {
            Log.d(TAG, "URL already in queue")
            return false
        }
        
        recentUrls[url] = now
        
        // Clean old entries from recentUrls
        recentUrls.entries.removeIf { now - it.value > 60000 }
        
        // Add to queue
        val item = QrProcessingItem(
            url = url,
            status = ProcessingStatus.QUEUED,
            addedAt = now
        )
        
        _processingQueue.value = _processingQueue.value + item
        Log.d(TAG, "Added to queue: ${url.take(50)}...")
        
        // Start processing
        processItem(item)
        
        return true
    }
    
    private fun processItem(item: QrProcessingItem) {
        scope.launch {
            try {
                // Update status to SENDING
                updateItemStatus(item.url, ProcessingStatus.SENDING)
                
                // Send async request
                val request = NFCeAsyncRequest(url = item.url, save = true, async = true)
                val response = apiService.extractNFCeAsync(request)
                
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    val recordId = body.record_id
                    
                    // Update status to PROCESSING
                    updateItemStatus(item.url, ProcessingStatus.PROCESSING, recordId = recordId)
                    
                    // Poll for completion
                    pollForCompletion(item.url, recordId)
                    
                } else if (response.code() == 409) {
                    // Duplicate URL
                    updateItemStatus(item.url, ProcessingStatus.DUPLICATE)
                    scheduleRemoval(item.url)
                } else {
                    val errorMsg = response.errorBody()?.string() ?: "Unknown error"
                    Log.e(TAG, "API error: $errorMsg")
                    updateItemStatus(item.url, ProcessingStatus.ERROR, errorMessage = "Erro ao enviar")
                    scheduleRemoval(item.url)
                }
                
            } catch (e: Exception) {
                Log.e(TAG, "Processing error", e)
                updateItemStatus(item.url, ProcessingStatus.ERROR, errorMessage = e.message ?: "Erro")
                scheduleRemoval(item.url)
            }
        }
    }
    
    private suspend fun pollForCompletion(url: String, recordId: Int) {
        var attempts = 0
        
        while (attempts < MAX_POLL_ATTEMPTS) {
            delay(POLL_INTERVAL_MS)
            attempts++
            
            try {
                val response = apiService.getNfceStatus(recordId)
                
                if (response.isSuccessful && response.body() != null) {
                    val status = response.body()!!
                    
                    when (status.status) {
                        "success" -> {
                            updateItemStatus(
                                url, 
                                ProcessingStatus.SUCCESS,
                                marketName = status.market_name,
                                productsCount = status.products_count
                            )
                            scheduleRemoval(url)
                            return
                        }
                        "error" -> {
                            updateItemStatus(
                                url, 
                                ProcessingStatus.ERROR, 
                                errorMessage = status.error_message ?: "Erro no servidor"
                            )
                            scheduleRemoval(url)
                            return
                        }
                        "processing" -> {
                            // Still processing, continue polling
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Poll error", e)
            }
        }
        
        // Timeout
        updateItemStatus(url, ProcessingStatus.ERROR, errorMessage = "Timeout")
        scheduleRemoval(url)
    }
    
    private fun updateItemStatus(
        url: String,
        status: ProcessingStatus,
        recordId: Int? = null,
        marketName: String? = null,
        productsCount: Int? = null,
        errorMessage: String? = null
    ) {
        _processingQueue.value = _processingQueue.value.map { item ->
            if (item.url == url) {
                item.copy(
                    status = status,
                    recordId = recordId ?: item.recordId,
                    marketName = marketName ?: item.marketName,
                    productsCount = productsCount ?: item.productsCount,
                    errorMessage = errorMessage ?: item.errorMessage
                )
            } else {
                item
            }
        }
    }
    
    private fun scheduleRemoval(url: String, delayMs: Long = 5000L) {
        scope.launch {
            delay(delayMs)
            removeFromQueue(url)
        }
    }
    
    fun removeFromQueue(url: String) {
        _processingQueue.value = _processingQueue.value.filter { it.url != url }
    }
    
    fun clearQueue() {
        _processingQueue.value = emptyList()
    }
    
    fun getActiveCount(): Int {
        return _processingQueue.value.count { 
            it.status in listOf(ProcessingStatus.QUEUED, ProcessingStatus.SENDING, ProcessingStatus.PROCESSING)
        }
    }
}

data class QrProcessingItem(
    val url: String,
    val status: ProcessingStatus,
    val addedAt: Long,
    val recordId: Int? = null,
    val marketName: String? = null,
    val productsCount: Int? = null,
    val errorMessage: String? = null
)

enum class ProcessingStatus {
    QUEUED,      // Waiting to be sent
    SENDING,     // Sending to server
    PROCESSING,  // Server is processing
    SUCCESS,     // Completed successfully
    ERROR,       // Failed
    DUPLICATE    // URL already processed
}

