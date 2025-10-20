package com.appprecos.ui.markets

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.appprecos.data.model.ProductDetail
import com.appprecos.databinding.ItemProductBinding
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
            
            binding.textProductNcm.text = context.getString(
                com.appprecos.R.string.product_ncm_label,
                product.ncm
            )
            binding.textProductPrice.text = context.getString(
                com.appprecos.R.string.product_price_format,
                product.price
            )
            
            // Format date
            try {
                val inputFormat = SimpleDateFormat("yyyy-MM-dd HH:mm:ss", Locale.getDefault())
                val outputFormat = SimpleDateFormat("dd/MM/yyyy HH:mm", Locale.getDefault())
                val date = inputFormat.parse(product.purchase_date.replace("T", " ").substring(0, 19))
                binding.textProductUpdated.text = context.getString(
                    com.appprecos.R.string.product_updated_label,
                    outputFormat.format(date)
                )
            } catch (e: Exception) {
                binding.textProductUpdated.text = context.getString(
                    com.appprecos.R.string.product_updated_label,
                    product.purchase_date
                )
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

