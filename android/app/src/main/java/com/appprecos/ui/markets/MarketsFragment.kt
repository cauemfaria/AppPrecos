package com.appprecos.ui.markets

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import com.appprecos.databinding.FragmentMarketsBinding
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
        observeViewModel()
        
        // Refresh button
        binding.buttonRefresh?.setOnClickListener {
            viewModel.refreshMarkets()
        }
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
                        binding.progressBar.visibility = View.VISIBLE
                        binding.recyclerViewMarkets.visibility = View.GONE
                    }
                    is MarketsState.Success -> {
                        binding.progressBar.visibility = View.GONE
                        binding.recyclerViewMarkets.visibility = View.VISIBLE
                        marketsAdapter.submitList(state.markets)
                    }
                    is MarketsState.Error -> {
                        binding.progressBar.visibility = View.GONE
                        binding.textError.visibility = View.VISIBLE
                        binding.textError.text = state.message
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
        val dialog = android.app.AlertDialog.Builder(requireContext())
            .setTitle(response.market.name)
            .setMessage("Loading products...")
            .create()
        
        val dialogView = layoutInflater.inflate(
            com.appprecos.R.layout.dialog_products,
            null
        )
        
        dialog.setView(dialogView)
        
        // Setup RecyclerView in dialog
        val recyclerView = dialogView.findViewById<androidx.recyclerview.widget.RecyclerView>(
            com.appprecos.R.id.recyclerViewProducts
        )
        val titleText = dialogView.findViewById<android.widget.TextView>(
            com.appprecos.R.id.textDialogTitle
        )
        val closeButton = dialogView.findViewById<android.widget.Button>(
            com.appprecos.R.id.buttonClose
        )
        
        titleText.text = "${response.market.name}\n${response.total} Unique Products"
        
        val productsAdapter = ProductsAdapter()
        recyclerView.layoutManager = androidx.recyclerview.widget.LinearLayoutManager(context)
        recyclerView.adapter = productsAdapter
        productsAdapter.submitList(response.products)
        
        closeButton.setOnClickListener {
            dialog.dismiss()
        }
        
        dialog.show()
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
}

