package com.appprecos.ui.shoppinglist

import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.LinearLayoutManager
import com.appprecos.R
import com.appprecos.databinding.FragmentShoppingListBinding
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.snackbar.Snackbar
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.launch

class ShoppingListFragment : Fragment() {
    
    private var _binding: FragmentShoppingListBinding? = null
    private val binding get() = _binding!!
    
    private val viewModel: ShoppingListViewModel by viewModels()
    
    private lateinit var shoppingListAdapter: ShoppingListAdapter
    
    // Track dialog coroutine jobs for cleanup
    private var dialogJobs: MutableList<Job> = mutableListOf()
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentShoppingListBinding.inflate(inflater, container, false)
        return binding.root
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        setupRecyclerView()
        setupButtons()
        observeViewModel()
    }
    
    private fun setupRecyclerView() {
        shoppingListAdapter = ShoppingListAdapter { item ->
            viewModel.removeFromShoppingList(item)
            Snackbar.make(binding.root, R.string.shopping_list_removed, Snackbar.LENGTH_SHORT).show()
        }
        
        binding.recyclerProducts.apply {
            layoutManager = LinearLayoutManager(context)
            adapter = shoppingListAdapter
        }
    }
    
    private fun setupButtons() {
        binding.fabAddProduct.setOnClickListener {
            showAddProductDialog()
        }
        
        binding.buttonSelectMarkets.setOnClickListener {
            showSelectMarketsDialog()
        }
        
        binding.buttonClear.setOnClickListener {
            MaterialAlertDialogBuilder(requireContext())
                .setTitle(R.string.shopping_list_clear)
                .setMessage("Remover todos os produtos da lista?")
                .setPositiveButton("Sim") { _, _ ->
                    viewModel.clearShoppingList()
                }
                .setNegativeButton("Não", null)
                .show()
        }
        
        binding.buttonCompare.setOnClickListener {
            lifecycleScope.launch {
                val items = viewModel.shoppingList.first()
                if (items.isEmpty()) {
                    Snackbar.make(binding.root, R.string.shopping_list_add_products_first, Snackbar.LENGTH_SHORT).show()
                    return@launch
                }
                if (viewModel.selectedMarketIds.value.isEmpty()) {
                    Snackbar.make(binding.root, R.string.shopping_list_select_at_least_one, Snackbar.LENGTH_SHORT).show()
                    return@launch
                }
                viewModel.compareProducts(items)
            }
        }
    }
    
    private fun observeViewModel() {
        viewLifecycleOwner.lifecycleScope.launch {
            viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch {
                    viewModel.shoppingList.collect { items ->
                        shoppingListAdapter.submitList(items)
                        
                        binding.emptyState.visibility = if (items.isEmpty()) View.VISIBLE else View.GONE
                        binding.recyclerProducts.visibility = if (items.isEmpty()) View.GONE else View.VISIBLE
                        
                        binding.textProductsCount.text = getString(R.string.shopping_list_products_count, items.size)
                    }
                }
                
                launch {
                    viewModel.selectedMarketIds.collect { ids ->
                        binding.buttonSelectMarkets.text = if (ids.isEmpty()) {
                            getString(R.string.shopping_list_select_markets)
                        } else {
                            getString(R.string.shopping_list_markets_selected, ids.size)
                        }
                    }
                }
                
                launch {
                    viewModel.comparisonResult.collect { result ->
                        if (result != null) {
                            showComparisonDialog(result)
                            viewModel.clearComparison()
                        }
                    }
                }
                
                launch {
                    viewModel.error.collect { error ->
                        if (error != null) {
                            Snackbar.make(binding.root, error, Snackbar.LENGTH_LONG).show()
                            viewModel.clearError()
                        }
                    }
                }
            }
        }
    }
    
    private fun showAddProductDialog() {
        // Cancel any previous dialog jobs
        dialogJobs.forEach { it.cancel() }
        dialogJobs.clear()
        
        val dialogView = LayoutInflater.from(requireContext())
            .inflate(R.layout.dialog_add_product, null)
        
        val dialog = MaterialAlertDialogBuilder(requireContext())
            .setTitle(R.string.shopping_list_add_product)
            .setView(dialogView)
            .setNegativeButton(R.string.dialog_close, null)
            .setOnDismissListener {
                // Cancel jobs when dialog is dismissed
                dialogJobs.forEach { it.cancel() }
                dialogJobs.clear()
                viewModel.clearSearchResults()
            }
            .create()
        
        val editSearch = dialogView.findViewById<com.google.android.material.textfield.TextInputEditText>(R.id.editSearch)
        val progressSearch = dialogView.findViewById<android.widget.ProgressBar>(R.id.progressSearch)
        val textHint = dialogView.findViewById<android.widget.TextView>(R.id.textSearchHint)
        val recyclerResults = dialogView.findViewById<androidx.recyclerview.widget.RecyclerView>(R.id.recyclerSearchResults)
        
        val searchAdapter = SearchResultAdapter { product ->
            viewModel.addToShoppingList(product)
            Snackbar.make(binding.root, R.string.shopping_list_added, Snackbar.LENGTH_SHORT).show()
            dialog.dismiss()
        }
        
        recyclerResults.apply {
            layoutManager = LinearLayoutManager(context)
            adapter = searchAdapter
        }
        
        editSearch.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {}
            override fun afterTextChanged(s: Editable?) {
                val query = s?.toString() ?: ""
                if (query.length >= 2) {
                    viewModel.searchProducts(query)
                } else {
                    viewModel.clearSearchResults()
                }
            }
        })
        
        // Observe search state with cancellable jobs
        dialogJobs.add(viewLifecycleOwner.lifecycleScope.launch {
            viewModel.isSearching.collect { isSearching ->
                progressSearch.visibility = if (isSearching) View.VISIBLE else View.GONE
            }
        })
        
        dialogJobs.add(viewLifecycleOwner.lifecycleScope.launch {
            viewModel.searchResults.collect { results ->
                searchAdapter.submitList(results)
                
                val query = editSearch.text?.toString() ?: ""
                when {
                    query.length < 2 -> {
                        textHint.visibility = View.VISIBLE
                        textHint.text = getString(R.string.shopping_list_search_min)
                        recyclerResults.visibility = View.GONE
                    }
                    results.isEmpty() && !viewModel.isSearching.value -> {
                        textHint.visibility = View.VISIBLE
                        textHint.text = getString(R.string.shopping_list_no_results)
                        recyclerResults.visibility = View.GONE
                    }
                    else -> {
                        textHint.visibility = View.GONE
                        recyclerResults.visibility = View.VISIBLE
                    }
                }
            }
        })
        
        dialog.show()
    }
    
    private fun showSelectMarketsDialog() {
        // Cancel any previous dialog jobs
        dialogJobs.forEach { it.cancel() }
        dialogJobs.clear()
        
        val dialogView = LayoutInflater.from(requireContext())
            .inflate(R.layout.dialog_select_markets, null)
        
        val dialog = MaterialAlertDialogBuilder(requireContext())
            .setView(dialogView)
            .setPositiveButton("OK", null)
            .setOnDismissListener {
                dialogJobs.forEach { it.cancel() }
                dialogJobs.clear()
            }
            .create()
        
        val recyclerMarkets = dialogView.findViewById<androidx.recyclerview.widget.RecyclerView>(R.id.recyclerMarkets)
        val progressMarkets = dialogView.findViewById<android.widget.ProgressBar>(R.id.progressMarkets)
        
        val marketsAdapter = MarketCheckboxAdapter(
            onMarketToggle = { marketId -> viewModel.toggleMarketSelection(marketId) },
            isSelected = { marketId -> viewModel.isMarketSelected(marketId) }
        )
        
        recyclerMarkets.apply {
            layoutManager = LinearLayoutManager(context)
            adapter = marketsAdapter
        }
        
        dialogJobs.add(viewLifecycleOwner.lifecycleScope.launch {
            viewModel.markets.collect { markets ->
                progressMarkets.visibility = View.GONE
                marketsAdapter.submitList(markets)
            }
        })
        
        dialog.show()
    }
    
    private fun showComparisonDialog(result: com.appprecos.data.model.CompareResponse) {
        val fragment = ComparisonResultFragment.newInstance(result)
        fragment.show(parentFragmentManager, "comparison")
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        dialogJobs.forEach { it.cancel() }
        dialogJobs.clear()
        _binding = null
    }
}
