package com.appprecos.ui.shoppinglist

import android.graphics.Typeface
import android.os.Bundle
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TableRow
import android.widget.TextView
import androidx.core.content.ContextCompat
import androidx.fragment.app.DialogFragment
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
        
        buildComparisonTable()
    }
    
    private fun buildComparisonTable() {
        val table = binding.tableComparison
        table.removeAllViews()
        
        val marketIds = comparisonData.markets.keys.toList()
        
        // Header row
        val headerRow = TableRow(requireContext()).apply {
            layoutParams = TableRow.LayoutParams(
                TableRow.LayoutParams.WRAP_CONTENT,
                TableRow.LayoutParams.WRAP_CONTENT
            )
        }
        
        // Product column header
        headerRow.addView(createHeaderCell("Produto", 200))
        
        // Market column headers
        for (marketId in marketIds) {
            val marketName = comparisonData.markets[marketId] ?: marketId
            // Truncate long names
            val displayName = if (marketName.length > 15) {
                marketName.take(12) + "..."
            } else {
                marketName
            }
            headerRow.addView(createHeaderCell(displayName, 100))
        }
        
        table.addView(headerRow)
        
        // Data rows
        for (row in comparisonData.comparison) {
            val tableRow = TableRow(requireContext()).apply {
                layoutParams = TableRow.LayoutParams(
                    TableRow.LayoutParams.WRAP_CONTENT,
                    TableRow.LayoutParams.WRAP_CONTENT
                )
            }
            
            // Product name cell
            tableRow.addView(createProductCell(row.product_name))
            
            // Price cells for each market
            for (marketId in marketIds) {
                val price = row.getPriceForMarket(marketId)
                tableRow.addView(createPriceCell(price, row))
            }
            
            table.addView(tableRow)
        }
    }
    
    private fun createHeaderCell(text: String, minWidth: Int): TextView {
        return TextView(requireContext()).apply {
            this.text = text
            this.minWidth = (minWidth * resources.displayMetrics.density).toInt()
            this.setPadding(16, 12, 16, 12)
            this.setTypeface(null, Typeface.BOLD)
            this.textSize = 14f
            this.setTextColor(ContextCompat.getColor(requireContext(), android.R.color.black))
            this.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.price_equal_bg))
            this.gravity = Gravity.CENTER
        }
    }
    
    private fun createProductCell(productName: String): TextView {
        return TextView(requireContext()).apply {
            this.text = productName
            this.minWidth = (200 * resources.displayMetrics.density).toInt()
            this.maxWidth = (250 * resources.displayMetrics.density).toInt()
            this.setPadding(16, 12, 16, 12)
            this.textSize = 13f
            this.maxLines = 2
        }
    }
    
    private fun createPriceCell(price: Double?, row: ComparisonRow): TextView {
        return TextView(requireContext()).apply {
            this.minWidth = (100 * resources.displayMetrics.density).toInt()
            this.setPadding(16, 12, 16, 12)
            this.textSize = 13f
            this.gravity = Gravity.CENTER
            
            if (price == null) {
                this.text = "-"
                this.setTextColor(ContextCompat.getColor(requireContext(), R.color.price_not_found))
            } else {
                this.text = currencyFormat.format(price)
                
                // Determine color based on comparison
                when {
                    row.all_equal -> {
                        this.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.price_equal_bg))
                        this.setTextColor(ContextCompat.getColor(requireContext(), R.color.price_equal))
                    }
                    row.min_price != null && price == row.min_price -> {
                        this.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.price_lowest_bg))
                        this.setTextColor(ContextCompat.getColor(requireContext(), R.color.price_lowest))
                        this.setTypeface(null, Typeface.BOLD)
                    }
                    row.max_price != null && price == row.max_price -> {
                        this.setBackgroundColor(ContextCompat.getColor(requireContext(), R.color.price_highest_bg))
                        this.setTextColor(ContextCompat.getColor(requireContext(), R.color.price_highest))
                    }
                    else -> {
                        // Middle price - no special color
                        this.setTextColor(ContextCompat.getColor(requireContext(), android.R.color.black))
                    }
                }
            }
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
}

