package com.appprecos.ui.scanner

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.util.Log
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import com.google.android.material.snackbar.Snackbar
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.*
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.appprecos.MainActivity
import com.appprecos.R
import com.appprecos.data.service.ProcessingStatus
import com.appprecos.databinding.FragmentCameraScannerBinding
import com.appprecos.databinding.FragmentScannerBinding
import com.appprecos.databinding.ViewProcessingQueueBinding
import kotlinx.coroutines.launch
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class ScannerFragment : Fragment() {
    
    private var _binding: FragmentScannerBinding? = null
    private val binding get() = _binding!!
    
    private var _cameraBinding: FragmentCameraScannerBinding? = null
    private val cameraBinding get() = _cameraBinding!!
    
    private var _queueBinding: ViewProcessingQueueBinding? = null
    private val queueBinding get() = _queueBinding!!
    
    private val viewModel: ScannerViewModel by viewModels()
    
    private var cameraProvider: ProcessCameraProvider? = null
    private var cameraExecutor: ExecutorService? = null
    private var isCameraActive = false
    private var isQueueExpanded = false
    
    private lateinit var queueAdapter: ProcessingQueueAdapter
    
    private val cameraPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            startCamera()
        } else {
            view?.let {
                Snackbar.make(
                    it,
                    getString(R.string.scanner_camera_permission_required),
                    Snackbar.LENGTH_SHORT
                ).show()
            }
        }
    }
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentScannerBinding.inflate(inflater, container, false)
        return binding.root
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        setupQueueView()
        setupUI()
        observeViewModel()
    }
    
    private fun setupQueueView() {
        // Get the included view binding
        _queueBinding = ViewProcessingQueueBinding.bind(binding.processingQueueView.root)
        
        // Setup adapter
        queueAdapter = ProcessingQueueAdapter { item ->
            viewModel.removeFromQueue(item.url)
        }
        
        queueBinding.recyclerQueueItems.apply {
            layoutManager = LinearLayoutManager(context)
            adapter = queueAdapter
        }
        
        // Setup expand/collapse
        queueBinding.headerProcessingQueue.setOnClickListener {
            toggleQueueExpanded()
        }
        
        queueBinding.buttonExpandQueue.setOnClickListener {
            toggleQueueExpanded()
        }
    }
    
    private fun toggleQueueExpanded() {
        isQueueExpanded = !isQueueExpanded
        queueBinding.recyclerQueueItems.visibility = if (isQueueExpanded) View.VISIBLE else View.GONE
        queueBinding.buttonExpandQueue.rotation = if (isQueueExpanded) 180f else 0f
    }
    
    private fun setupUI() {
        binding.buttonScanQr.setOnClickListener {
            checkCameraPermissionAndStart()
        }
        
        binding.buttonSubmitUrl.setOnClickListener {
            val url = binding.editTextUrl.text.toString()
            if (url.isNotBlank()) {
                processNFCeUrl(url)
            } else {
                Snackbar.make(
                    binding.root,
                    getString(R.string.scanner_enter_url),
                    Snackbar.LENGTH_SHORT
                ).show()
            }
        }
    }
    
    private fun observeViewModel() {
        // Observe sync processing state (for manual URL)
        lifecycleScope.launch {
            viewModel.scanState.collect { state ->
                when (state) {
                    is ScanState.Idle -> {
                        binding.progressIndicator.visibility = View.GONE
                        binding.textStatus.visibility = View.GONE
                    }
                    is ScanState.Processing -> {
                        binding.progressIndicator.visibility = View.VISIBLE
                        binding.textStatus.visibility = View.VISIBLE
                        binding.textStatus.text = getString(R.string.scanner_status_processing)
                    }
                    is ScanState.Success -> {
                        binding.progressIndicator.visibility = View.GONE
                        binding.textStatus.visibility = View.VISIBLE
                        val actionText = if (state.action == "created") 
                            getString(R.string.success_new_market) 
                        else 
                            getString(R.string.success_existing_market)
                        binding.textStatus.text = getString(
                            R.string.success_message,
                            actionText,
                            state.productsCount
                        )
                        
                        Snackbar.make(
                            binding.root,
                            getString(R.string.success_qr_processed),
                            Snackbar.LENGTH_LONG
                        ).setAction("View") {
                            (activity as? MainActivity)?.switchToMarketsTab()
                        }.show()
                        
                        binding.editTextUrl.text?.clear()
                    }
                    is ScanState.Duplicate -> {
                        binding.progressIndicator.visibility = View.GONE
                        binding.textStatus.visibility = View.VISIBLE
                        binding.textStatus.text = getString(R.string.duplicate_qr_title)
                        Snackbar.make(
                            binding.root,
                            getString(R.string.duplicate_qr_message),
                            Snackbar.LENGTH_LONG
                        ).show()
                    }
                    is ScanState.Error -> {
                        binding.progressIndicator.visibility = View.GONE
                        binding.textStatus.visibility = View.VISIBLE
                        binding.textStatus.text = getString(R.string.error_label, state.message)
                        Snackbar.make(
                            binding.root,
                            state.message,
                            Snackbar.LENGTH_LONG
                        ).show()
                    }
                }
            }
        }
        
        // Observe background processing queue
        lifecycleScope.launch {
            viewModel.processingQueue.collect { queue ->
                updateQueueUI(queue)
            }
        }
    }
    
    private fun updateQueueUI(queue: List<com.appprecos.data.service.QrProcessingItem>) {
        if (queue.isEmpty()) {
            binding.processingQueueView.root.visibility = View.GONE
            return
        }
        
        binding.processingQueueView.root.visibility = View.VISIBLE
        queueAdapter.submitList(queue)
        
        // Update header text
        val activeCount = queue.count { 
            it.status in listOf(
                ProcessingStatus.QUEUED, 
                ProcessingStatus.SENDING, 
                ProcessingStatus.PROCESSING
            )
        }
        val successCount = queue.count { it.status == ProcessingStatus.SUCCESS }
        val errorCount = queue.count { 
            it.status in listOf(ProcessingStatus.ERROR, ProcessingStatus.DUPLICATE)
        }
        
        queueBinding.textQueueStatus.text = when {
            activeCount > 0 -> getString(R.string.queue_processing_count, activeCount)
            successCount > 0 && errorCount == 0 -> getString(R.string.queue_all_done)
            errorCount > 0 -> getString(R.string.queue_with_errors, errorCount)
            else -> getString(R.string.queue_processing_count, queue.size)
        }
        
        // Show/hide progress based on active items
        queueBinding.progressQueue.visibility = if (activeCount > 0) View.VISIBLE else View.GONE
    }
    
    private fun checkCameraPermissionAndStart() {
        when {
            ContextCompat.checkSelfPermission(
                requireContext(),
                Manifest.permission.CAMERA
            ) == PackageManager.PERMISSION_GRANTED -> {
                startCamera()
            }
            else -> {
                cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
            }
        }
    }
    
    private fun startCamera() {
        if (cameraExecutor == null) {
            cameraExecutor = Executors.newSingleThreadExecutor()
        }
        
        showCameraView()
        
        val cameraProviderFuture = ProcessCameraProvider.getInstance(requireContext())
        cameraProviderFuture.addListener({
            try {
                cameraProvider = cameraProviderFuture.get()
                bindCameraUseCases()
            } catch (e: Exception) {
                Log.e(TAG, "Camera initialization failed", e)
                closeCameraView()
                Snackbar.make(
                    binding.root,
                    "Failed to initialize camera: ${e.message}",
                    Snackbar.LENGTH_LONG
                ).show()
            }
        }, ContextCompat.getMainExecutor(requireContext()))
    }
    
    private fun showCameraView() {
        isCameraActive = true
        _cameraBinding = FragmentCameraScannerBinding.inflate(layoutInflater)
        
        val container = binding.root.parent as? ViewGroup
        container?.let {
            val index = it.indexOfChild(binding.root)
            it.removeView(binding.root)
            it.addView(cameraBinding.root, index)
        }
        
        cameraBinding.buttonClose.setOnClickListener {
            closeCameraView()
        }
    }
    
    private fun closeCameraView() {
        isCameraActive = false
        
        cameraProvider?.unbindAll()
        
        val container = cameraBinding.root.parent as? ViewGroup
        container?.let {
            val index = it.indexOfChild(cameraBinding.root)
            it.removeView(cameraBinding.root)
            it.addView(binding.root, index)
        }
        
        _cameraBinding = null
    }
    
    private fun bindCameraUseCases() {
        val cameraProvider = cameraProvider ?: return
        
        val preview = Preview.Builder()
            .build()
            .also {
                it.setSurfaceProvider(cameraBinding.previewView.surfaceProvider)
            }
        
        val imageAnalyzer = ImageAnalysis.Builder()
            .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
            .build()
            .also {
                it.setAnalyzer(
                    cameraExecutor!!,
                    QrCodeAnalyzer { qrCode ->
                        handleQrCodeDetected(qrCode)
                    }
                )
            }
        
        val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
        
        try {
            cameraProvider.unbindAll()
            
            cameraProvider.bindToLifecycle(
                viewLifecycleOwner,
                cameraSelector,
                preview,
                imageAnalyzer
            )
        } catch (e: Exception) {
            Log.e(TAG, "Use case binding failed", e)
        }
    }
    
    private fun handleQrCodeDetected(qrCode: String) {
        if (!isCameraActive) return
        
        activity?.runOnUiThread {
            Log.d(TAG, "QR Code detected: $qrCode")
            
            // Add to background queue instead of blocking
            val added = viewModel.addToQueue(qrCode)
            
            if (added) {
                // Show toast but keep camera open
                Snackbar.make(
                    cameraBinding.root,
                    getString(R.string.scanner_qr_added_to_queue),
                    Snackbar.LENGTH_SHORT
                ).show()
            }
            // Camera stays open for next scan!
        }
    }
    
    companion object {
        private const val TAG = "ScannerFragment"
    }
    
    private fun processNFCeUrl(url: String) {
        viewModel.processNFCe(url)
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        
        cameraProvider?.unbindAll()
        cameraExecutor?.shutdown()
        cameraExecutor = null
        
        _binding = null
        _cameraBinding = null
        _queueBinding = null
    }
}
