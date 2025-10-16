package com.appprecos.ui.scanner

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import com.appprecos.databinding.FragmentScannerBinding
import kotlinx.coroutines.launch

class ScannerFragment : Fragment() {
    
    private var _binding: FragmentScannerBinding? = null
    private val binding get() = _binding!!
    
    private val viewModel: ScannerViewModel by viewModels()
    
    private val cameraPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            startCamera()
        } else {
            Toast.makeText(context, "Camera permission required", Toast.LENGTH_SHORT).show()
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
        // Button to start camera scanning
        binding.buttonScan.setOnClickListener {
            checkCameraPermissionAndStart()
        }
        
        // Manual URL input
        binding.buttonSubmitUrl.setOnClickListener {
            val url = binding.editTextUrl.text.toString()
            if (url.isNotBlank()) {
                processNFCeUrl(url)
            } else {
                Toast.makeText(context, "Please enter a URL", Toast.LENGTH_SHORT).show()
            }
        }
    }
    
    private fun observeViewModel() {
        lifecycleScope.launch {
            viewModel.scanState.collect { state ->
                when (state) {
                    is ScanState.Idle -> {
                        binding.progressBar.visibility = View.GONE
                        binding.textStatus.text = "Scan QR code or enter URL"
                    }
                    is ScanState.Processing -> {
                        binding.progressBar.visibility = View.VISIBLE
                        binding.textStatus.text = "Processing NFCe..."
                    }
                    is ScanState.Success -> {
                        binding.progressBar.visibility = View.GONE
                        val actionText = if (state.action == "created") "NEW market created!" else "Existing market updated"
                        binding.textStatus.text = "✓ Success!\n$actionText\n${state.productsCount} products saved"
                        Toast.makeText(
                            context,
                            "✓ QR Code Successfully Processed!\n\n" +
                            "Market: ${state.marketName}\n" +
                            "Products: ${state.productsCount}\n" +
                            "Status: $actionText",
                            Toast.LENGTH_LONG
                        ).show()
                        binding.editTextUrl.text?.clear()
                    }
                    is ScanState.Duplicate -> {
                        binding.progressBar.visibility = View.GONE
                        binding.textStatus.text = "⚠ QR Code Already Used"
                        Toast.makeText(
                            context,
                            "✗ This QR Code Was Already Used!\n\n" +
                            "Processed: ${state.processedAt}\n" +
                            "Market ID: ${state.marketId}\n" +
                            "Products: ${state.productsCount}",
                            Toast.LENGTH_LONG
                        ).show()
                    }
                    is ScanState.Error -> {
                        binding.progressBar.visibility = View.GONE
                        binding.textStatus.text = "Error: ${state.message}"
                        Toast.makeText(context, state.message, Toast.LENGTH_LONG).show()
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
        // TODO: Implement CameraX QR scanning
        // For now, show manual input
        Toast.makeText(context, "Camera scanning - Coming soon!\nUse manual input for now", Toast.LENGTH_SHORT).show()
    }
    
    private fun processNFCeUrl(url: String) {
        viewModel.processNFCe(url)
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

