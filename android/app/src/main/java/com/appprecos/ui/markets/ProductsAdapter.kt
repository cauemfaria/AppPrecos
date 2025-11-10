package com.appprecos.ui.markets

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.appprecos.data.model.ProductDetail
import com.appprecos.databinding.ItemProductBinding
import com.appprecos.util.NcmTableManager
import java.text.SimpleDateFormat
import java.util.*

class ProductsAdapter : ListAdapter<ProductDetail, ProductsAdapter.ProductViewHolder>(ProductDiffCallback()) {
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ProductViewHolder {
        val binding = ItemProductBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return ProductViewHolder(binding)
    }
    
    override fun onBindViewHolder(holder: ProductViewHolder, position: Int) {
        holder.bind(getItem(position))
    }
    
    class ProductViewHolder(
        private val binding: ItemProductBinding
    ) : RecyclerView.ViewHolder(binding.root) {
        
        fun bind(product: ProductDetail) {
            val context = binding.root.context
            
            // Get NCM description from the table
            val ncmDescription = NcmTableManager.getDescription(product.ncm)
            binding.textProductNcm.text = ncmDescription
            
            // Display unit type (simple text, no quantity numbers)
            val unitText = when (product.unidade_comercial.uppercase()) {
                "UN" -> context.getString(com.appprecos.R.string.product_unit_unidade)
                "KG" -> context.getString(com.appprecos.R.string.product_unit_kg)
                else -> product.unidade_comercial
            }
            binding.textProductQuantity.text = unitText
            
            // Display total price
            binding.textProductPrice.text = String.format("R$ %.2f", product.price)
            
            // Calculate and display unit price (only if quantity is valid and > 0)
            if (product.quantity > 0 && product.quantity.isFinite()) {
                val unitPrice = product.price / product.quantity
                // Check if unitPrice is valid (not infinity or NaN)
                if (unitPrice.isFinite() && !unitPrice.isNaN()) {
                    val unitPriceText = when (product.unidade_comercial.uppercase()) {
                        "UN" -> String.format("R$ %.2f/un", unitPrice)
                        "KG" -> String.format("R$ %.2f/Kg", unitPrice)
                        else -> String.format("R$ %.2f/${product.unidade_comercial}", unitPrice)
                    }
                    binding.textProductUnitPrice.text = unitPriceText
                    binding.textProductUnitPrice.visibility = android.view.View.VISIBLE
                } else {
                    binding.textProductUnitPrice.visibility = android.view.View.GONE
                }
            } else {
                binding.textProductUnitPrice.visibility = android.view.View.GONE
            }
            
            // Format and display last_updated date (or fall back to purchase_date)
            val dateToDisplay = product.last_updated ?: product.purchase_date
            try {
                val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
                val outputFormat = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault())
                val date = inputFormat.parse(dateToDisplay.replace(" ", "T").substring(0, 19))
                binding.textProductUpdated.text = "Updated: ${outputFormat.format(date ?: Date())}"
            } catch (e: Exception) {
                // Try alternative format
                try {
                    val inputFormat2 = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                    val outputFormat = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault())
                    val date = inputFormat2.parse(dateToDisplay.substring(0, 19))
                    binding.textProductUpdated.text = "Updated: ${outputFormat.format(date ?: Date())}"
                } catch (e2: Exception) {
                    binding.textProductUpdated.text = "Updated: $dateToDisplay"
                }
            }
        }
    }
    
    private class ProductDiffCallback : DiffUtil.ItemCallback<ProductDetail>() {
        override fun areItemsTheSame(oldItem: ProductDetail, newItem: ProductDetail): Boolean {
            return oldItem.ncm == newItem.ncm
        }
        
        override fun areContentsTheSame(oldItem: ProductDetail, newItem: ProductDetail): Boolean {
            return oldItem == newItem
        }
    }
}

