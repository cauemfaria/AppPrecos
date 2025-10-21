package com.appprecos.ui.products

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.LinearLayoutManager
import com.appprecos.data.model.MarketProductsResponse
import com.appprecos.databinding.FragmentProductsBottomSheetBinding
import com.appprecos.ui.markets.ProductsAdapter
import com.google.android.material.bottomsheet.BottomSheetDialogFragment

class ProductsBottomSheetFragment : BottomSheetDialogFragment() {
    
    private var _binding: FragmentProductsBottomSheetBinding? = null
    private val binding get() = _binding!!
    
    private lateinit var productsAdapter: ProductsAdapter
    private var marketProductsResponse: MarketProductsResponse? = null
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentProductsBottomSheetBinding.inflate(inflater, container, false)
        return binding.root
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        marketProductsResponse = arguments?.getSerializable(ARG_PRODUCTS) as? MarketProductsResponse
        
        setupUI()
        displayProducts()
    }
    
    private fun setupUI() {
        productsAdapter = ProductsAdapter()
        binding.recyclerViewProducts.apply {
            layoutManager = LinearLayoutManager(context)
            adapter = productsAdapter
        }
        
        binding.buttonClose.setOnClickListener {
            dismiss()
        }
    }
    
    private fun displayProducts() {
        marketProductsResponse?.let { response ->
            binding.textDialogTitle.text = "${response.market.name}\n${response.total} Unique Products"
            productsAdapter.submitList(response.products)
        }
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
    
    companion object {
        private const val ARG_PRODUCTS = "products"
        
        fun newInstance(productsResponse: MarketProductsResponse): ProductsBottomSheetFragment {
            return ProductsBottomSheetFragment().apply {
                arguments = Bundle().apply {
                    putSerializable(ARG_PRODUCTS, productsResponse as java.io.Serializable)
                }
            }
        }
    }
}

