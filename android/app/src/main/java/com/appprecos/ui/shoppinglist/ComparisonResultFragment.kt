package com.appprecos.ui.shoppinglist

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.ContextCompat
import androidx.fragment.app.DialogFragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.appprecos.R
import com.appprecos.data.model.CompareResponse
import com.appprecos.data.model.ComparisonRow
import com.appprecos.databinding.FragmentComparisonResultBinding
import com.google.gson.Gson
import java.text.NumberFormat
import java.util.Locale

class ComparisonResultFragment : DialogFragment() {
    
    private var _binding: FragmentComparisonResultBinding? = null
    private val binding get() = _binding!!
    
    private lateinit var comparisonData: CompareResponse
    private val currencyFormat = NumberFormat.getCurrencyInstance(Locale("pt", "BR"))
    
    companion object {
        private const val ARG_DATA = "comparison_data"
        
        fun newInstance(data: CompareResponse): ComparisonResultFragment {
            val fragment = ComparisonResultFragment()
            val args = Bundle()
            args.putString(ARG_DATA, Gson().toJson(data))
            fragment.arguments = args
            return fragment
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setStyle(STYLE_NORMAL, R.style.Theme_AppPrecos_FullScreenDialog)
        
        arguments?.getString(ARG_DATA)?.let { json ->
            comparisonData = Gson().fromJson(json, CompareResponse::class.java)
        }
    }
    
    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = FragmentComparisonResultBinding.inflate(inflater, container, false)
        return binding.root
    }
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        binding.buttonClose.setOnClickListener {
            dismiss()
        }
        
        setupRecyclerView()
    }
    
    private fun setupRecyclerView() {
        val adapter = ComparisonAdapter(
            comparisonData.comparison,
            comparisonData.markets,
            currencyFormat
        )
        
        binding.recyclerComparison.apply {
            layoutManager = LinearLayoutManager(context)
            this.adapter = adapter
        }
    }
    
    override fun onStart() {
        super.onStart()
        dialog?.window?.setLayout(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.MATCH_PARENT
        )
    }
    
    override fun onDestroyView() {
        super.onDestroyView()
        _binding = null
    }
    
    // RecyclerView Adapter
    inner class ComparisonAdapter(
        private val items: List<ComparisonRow>,
        private val markets: Map<String, String>,
        private val currencyFormat: NumberFormat
    ) : RecyclerView.Adapter<ComparisonAdapter.ViewHolder>() {
        
        inner class ViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
            val textProductName: TextView = itemView.findViewById(R.id.textProductName)
            val containerPrices: LinearLayout = itemView.findViewById(R.id.containerPrices)
        }
        
        override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
            val view = LayoutInflater.from(parent.context)
                .inflate(R.layout.item_comparison_product, parent, false)
            return ViewHolder(view)
        }
        
        override fun onBindViewHolder(holder: ViewHolder, position: Int) {
            val row = items[position]
            
            holder.textProductName.text = row.product_name
            
            // Clear previous prices
            holder.containerPrices.removeAllViews()
            
            // Sort markets by price (lowest first)
            val sortedMarkets = markets.entries.sortedBy { entry ->
                row.getPriceForMarket(entry.key) ?: Double.MAX_VALUE
            }
            
            // Add price rows for each market
            for (entry in sortedMarkets) {
                val marketId = entry.key
                val marketName = entry.value
                val price = row.getPriceForMarket(marketId)
                
                val priceView = LayoutInflater.from(holder.itemView.context)
                    .inflate(R.layout.item_comparison_market_price, holder.containerPrices, false)
                
                val textMarketName = priceView.findViewById<TextView>(R.id.textMarketName)
                val textPrice = priceView.findViewById<TextView>(R.id.textPrice)
                
                textMarketName.text = marketName
                
                if (price == null) {
                    textPrice.text = "—"
                    textPrice.setTextColor(ContextCompat.getColor(requireContext(), R.color.price_not_found))
                    textPrice.setBackgroundResource(R.drawable.price_chip_not_found)
                } else {
                    textPrice.text = currencyFormat.format(price)
                    
                    when {
                        row.all_equal -> {
                            textPrice.setTextColor(ContextCompat.getColor(requireContext(), R.color.price_equal))
                            textPrice.setBackgroundResource(R.drawable.price_chip_equal)
                        }
                        row.min_price != null && price == row.min_price -> {
                            textPrice.setTextColor(ContextCompat.getColor(requireContext(), android.R.color.white))
                            textPrice.setBackgroundResource(R.drawable.price_chip_lowest)
                        }
                        row.max_price != null && price == row.max_price -> {
                            textPrice.setTextColor(ContextCompat.getColor(requireContext(), android.R.color.white))
                            textPrice.setBackgroundResource(R.drawable.price_chip_highest)
                        }
                        else -> {
                            textPrice.setTextColor(ContextCompat.getColor(requireContext(), R.color.md_theme_light_onSurface))
                            textPrice.setBackgroundResource(R.drawable.price_chip_normal)
                        }
                    }
                }
                
                holder.containerPrices.addView(priceView)
            }
        }
        
        override fun getItemCount() = items.size
    }
}
