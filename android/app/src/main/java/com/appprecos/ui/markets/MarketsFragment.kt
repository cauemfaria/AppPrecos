package com.appprecos.ui.markets

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.appprecos.databinding.FragmentMarketsBinding
import com.appprecos.util.NcmTableManager
import kotlinx.coroutines.launch

class MarketsFragment : Fragment() {
    
    private var _binding: FragmentMarketsBinding? = null
    private val binding get() = _binding!!
    
    private val viewModel: MarketsViewModel by viewModels()
    private lateinit var marketsAdapter: MarketsAdapter
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentMarketsBinding.inflate(inflater, container, false)
        return binding.root
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        setupRecyclerView()
        setupUI()
        observeViewModel()
    }
    
    private fun setupUI() {
        // Search input - filter markets as user types
        binding.editTextSearch.addTextChangedListener(object : android.text.TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                viewModel.searchMarkets(s.toString())
            }
            override fun afterTextChanged(s: android.text.Editable?) {}
        })
    }
    
    override fun onResume() {
        super.onResume()
        // Reload markets when fragment becomes visible
        // This ensures if a market was deleted from backend, it disappears from app
        viewModel.loadMarkets()
    }
    
    private fun setupRecyclerView() {
        marketsAdapter = MarketsAdapter { market ->
            // Navigate to market details (show products)
            viewModel.loadMarketProducts(market.market_id)
        }
        
        binding.recyclerViewMarkets.apply {
            layoutManager = LinearLayoutManager(context)
            adapter = marketsAdapter
        }
    }
    
    private fun observeViewModel() {
        lifecycleScope.launch {
            viewModel.marketsState.collect { state ->
                when (state) {
                    is MarketsState.Loading -> {
                        binding.progressIndicator.visibility = View.VISIBLE
                        binding.recyclerViewMarkets.visibility = View.GONE
                        binding.emptyState.visibility = View.GONE
                        binding.textError.visibility = View.GONE
                    }
                    is MarketsState.Success -> {
                        binding.progressIndicator.visibility = View.GONE
                        binding.textError.visibility = View.GONE
                        
                        if (state.markets.isEmpty()) {
                            binding.recyclerViewMarkets.visibility = View.GONE
                            binding.emptyState.visibility = View.VISIBLE
                        } else {
                            binding.recyclerViewMarkets.visibility = View.VISIBLE
                            binding.emptyState.visibility = View.GONE
                            marketsAdapter.submitList(state.markets)
                        }
                    }
                    is MarketsState.Error -> {
                        binding.progressIndicator.visibility = View.GONE
                        binding.recyclerViewMarkets.visibility = View.GONE
                        binding.emptyState.visibility = View.GONE
                        binding.textError.visibility = View.VISIBLE
                        binding.textError.text = state.message
                        
                        // Show Snackbar for error
                        com.google.android.material.snackbar.Snackbar.make(
                            binding.root,
                            state.message,
                            com.google.android.material.snackbar.Snackbar.LENGTH_LONG
                        ).setAction("Retry") {
                            viewModel.refreshMarkets()
                        }.show()
                    }
                }
            }
        }
        
        lifecycleScope.launch {
            viewModel.selectedMarketProducts.collect { products ->
                products?.let {
                    // Show products dialog or navigate to details screen
                    showProductsDialog(it)
                }
            }
        }
    }
    
    private fun showProductsDialog(response: com.appprecos.data.model.MarketProductsResponse) {
        val dialogView = layoutInflater.inflate(
            com.appprecos.R.layout.dialog_products,
            null
        )
        
        // Setup dialog using MaterialAlertDialogBuilder
        val dialog = com.google.android.material.dialog.MaterialAlertDialogBuilder(requireContext())
            .setView(dialogView)
            .create()
        
        // Setup views
        val recyclerView = dialogView.findViewById<androidx.recyclerview.widget.RecyclerView>(
            com.appprecos.R.id.recyclerViewProducts
        )
        val titleText = dialogView.findViewById<com.google.android.material.textview.MaterialTextView>(
            com.appprecos.R.id.textDialogTitle
        )
        val closeButton = dialogView.findViewById<com.google.android.material.button.MaterialButton>(
            com.appprecos.R.id.buttonClose
        )
        val searchInput = dialogView.findViewById<com.google.android.material.textfield.TextInputEditText>(
            com.appprecos.R.id.editTextSearch
        )
        
        // Set title with market info
        titleText.text = getString(
            com.appprecos.R.string.markets_products_title,
            response.market.name,
            response.total
        )
        
        // Setup RecyclerView
        val productsAdapter = ProductsAdapter()
        recyclerView.layoutManager = androidx.recyclerview.widget.LinearLayoutManager(context)
        recyclerView.adapter = productsAdapter
        productsAdapter.submitList(response.products)
        
        // Close button
        closeButton.setOnClickListener {
            dialog.dismiss()
        }
        
        // Search functionality - filter by both NCM code and description
        searchInput.addTextChangedListener(object : android.text.TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                val query = s.toString().lowercase()
                val filtered = response.products.filter {
                    val ncmDescription = NcmTableManager.getDescription(it.ncm).lowercase()
                    it.ncm.lowercase().contains(query) || ncmDescription.contains(query)
                }
                productsAdapter.submitList(filtered)
            }
            override fun afterTextChanged(s: android.text.Editable?) {}
        })
        
        dialog.show()
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

