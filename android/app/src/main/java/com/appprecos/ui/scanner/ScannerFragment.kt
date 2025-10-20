package com.appprecos.ui.scanner

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import com.google.android.material.snackbar.Snackbar
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import com.appprecos.MainActivity
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
        // Extended FAB to start camera scanning
        binding.fabScan.setOnClickListener {
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
                        binding.textStatus.text = getString(com.appprecos.R.string.scanner_status_idle)
                    }
                    is ScanState.Processing -> {
                        binding.progressIndicator.visibility = View.VISIBLE
                        binding.textStatus.text = getString(com.appprecos.R.string.scanner_status_processing)
                    }
                    is ScanState.Success -> {
                        binding.progressIndicator.visibility = View.GONE
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
                            (activity as? MainActivity)?.findViewById<com.google.android.material.navigation.NavigationBarView>(
                                com.appprecos.R.id.bottomNavigation
                            )?.selectedItemId = com.appprecos.R.id.navigation_markets
                        }.show()
                        
                        binding.editTextUrl.text?.clear()
                    }
                    is ScanState.Duplicate -> {
                        binding.progressIndicator.visibility = View.GONE
                        binding.textStatus.text = getString(com.appprecos.R.string.duplicate_qr_title)
                        com.google.android.material.snackbar.Snackbar.make(
                            binding.root,
                            getString(com.appprecos.R.string.duplicate_qr_message),
                            com.google.android.material.snackbar.Snackbar.LENGTH_LONG
                        ).show()
                    }
                    is ScanState.Error -> {
                        binding.progressIndicator.visibility = View.GONE
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
        // TODO: Implement CameraX QR scanning
        // For now, show manual input
        com.google.android.material.snackbar.Snackbar.make(
            binding.root,
            getString(com.appprecos.R.string.scanner_coming_soon),
            com.google.android.material.snackbar.Snackbar.LENGTH_SHORT
        ).show()
    }
    
    private fun processNFCeUrl(url: String) {
        viewModel.processNFCe(url)
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

