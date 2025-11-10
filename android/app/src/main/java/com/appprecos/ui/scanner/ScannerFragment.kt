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
import com.appprecos.MainActivity
import com.appprecos.databinding.FragmentCameraScannerBinding
import com.appprecos.databinding.FragmentScannerBinding
import kotlinx.coroutines.launch
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

class ScannerFragment : Fragment() {
    
    private var _binding: FragmentScannerBinding? = null
    private val binding get() = _binding!!
    
    private var _cameraBinding: FragmentCameraScannerBinding? = null
    private val cameraBinding get() = _cameraBinding!!
    
    private val viewModel: ScannerViewModel by viewModels()
    
    private var cameraProvider: ProcessCameraProvider? = null
    private var cameraExecutor: ExecutorService? = null
    private var isCameraActive = false
    
    private val cameraPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            startCamera()
        } else {
            view?.let {
                Snackbar.make(
                    it,
                    getString(com.appprecos.R.string.scanner_camera_permission_required),
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
        
        setupUI()
        observeViewModel()
    }
    
    private fun setupUI() {
        // Scan QR Code button (primary action)
        binding.buttonScanQr.setOnClickListener {
            checkCameraPermissionAndStart()
        }
        
        // Manual URL input
        binding.buttonSubmitUrl.setOnClickListener {
            val url = binding.editTextUrl.text.toString()
            if (url.isNotBlank()) {
                processNFCeUrl(url)
            } else {
                com.google.android.material.snackbar.Snackbar.make(
                    binding.root,
                    getString(com.appprecos.R.string.scanner_enter_url),
                    com.google.android.material.snackbar.Snackbar.LENGTH_SHORT
                ).show()
            }
        }
    }
    
    private fun observeViewModel() {
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
                        binding.textStatus.text = getString(com.appprecos.R.string.scanner_status_processing)
                    }
                    is ScanState.Success -> {
                        binding.progressIndicator.visibility = View.GONE
                        binding.textStatus.visibility = View.VISIBLE
                        val actionText = if (state.action == "created") 
                            getString(com.appprecos.R.string.success_new_market) 
                        else 
                            getString(com.appprecos.R.string.success_existing_market)
                        binding.textStatus.text = getString(
                            com.appprecos.R.string.success_message,
                            actionText,
                            state.productsCount
                        )
                        
                        com.google.android.material.snackbar.Snackbar.make(
                            binding.root,
                            getString(com.appprecos.R.string.success_qr_processed),
                            com.google.android.material.snackbar.Snackbar.LENGTH_LONG
                        ).setAction("View") {
                            // Switch to markets tab
                            (activity as? MainActivity)?.switchToMarketsTab()
                        }.show()
                        
                        binding.editTextUrl.text?.clear()
                    }
                    is ScanState.Duplicate -> {
                        binding.progressIndicator.visibility = View.GONE
                        binding.textStatus.visibility = View.VISIBLE
                        binding.textStatus.text = getString(com.appprecos.R.string.duplicate_qr_title)
                        com.google.android.material.snackbar.Snackbar.make(
                            binding.root,
                            getString(com.appprecos.R.string.duplicate_qr_message),
                            com.google.android.material.snackbar.Snackbar.LENGTH_LONG
                        ).show()
                    }
                    is ScanState.Error -> {
                        binding.progressIndicator.visibility = View.GONE
                        binding.textStatus.visibility = View.VISIBLE
                        binding.textStatus.text = getString(com.appprecos.R.string.error_label, state.message)
                        com.google.android.material.snackbar.Snackbar.make(
                            binding.root,
                            state.message,
                            com.google.android.material.snackbar.Snackbar.LENGTH_LONG
                        ).show()
                    }
                }
            }
        }
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
        // Initialize camera executor if needed
        if (cameraExecutor == null) {
            cameraExecutor = Executors.newSingleThreadExecutor()
        }
        
        // Show camera UI
        showCameraView()
        
        // Start camera
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
        
        // Replace current view with camera view
        val container = binding.root.parent as? ViewGroup
        container?.let {
            val index = it.indexOfChild(binding.root)
            it.removeView(binding.root)
            it.addView(cameraBinding.root, index)
        }
        
        // Setup close button
        cameraBinding.buttonClose.setOnClickListener {
            closeCameraView()
        }
    }
    
    private fun closeCameraView() {
        isCameraActive = false
        
        // Unbind camera
        cameraProvider?.unbindAll()
        
        // Restore scanner view
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
        
        // Preview use case
        val preview = Preview.Builder()
            .build()
            .also {
                it.setSurfaceProvider(cameraBinding.previewView.surfaceProvider)
            }
        
        // Image analysis use case for QR scanning
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
        
        // Select back camera
        val cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA
        
        try {
            // Unbind all use cases before rebinding
            cameraProvider.unbindAll()
            
            // Bind use cases to camera
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
        
        // Run on main thread
        activity?.runOnUiThread {
            Log.d(TAG, "QR Code detected: $qrCode")
            
            // Show feedback
            Snackbar.make(
                cameraBinding.root,
                getString(com.appprecos.R.string.scanner_qr_detected),
                Snackbar.LENGTH_SHORT
            ).show()
            
            // Close camera and process the QR code
            closeCameraView()
            processNFCeUrl(qrCode)
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
        
        // Clean up camera resources
        cameraProvider?.unbindAll()
        cameraExecutor?.shutdown()
        cameraExecutor = null
        
        _binding = null
        _cameraBinding = null
    }
}

