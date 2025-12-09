package com.appprecos.ui.shoppinglist

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.appprecos.data.model.ProductSearchResult
import com.appprecos.databinding.ItemSearchResultBinding
import java.text.NumberFormat
import java.util.Locale

class SearchResultAdapter(
    private val onItemClick: (ProductSearchResult) -> Unit
) : ListAdapter<ProductSearchResult, SearchResultAdapter.ViewHolder>(DiffCallback()) {

    private val currencyFormat = NumberFormat.getCurrencyInstance(Locale("pt", "BR"))

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemSearchResultBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class ViewHolder(
        private val binding: ItemSearchResultBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(item: ProductSearchResult) {
            binding.textProductName.text = item.product_name
            binding.textProductInfo.text = "NCM: ${item.ncm}"
            
            val minPrice = currencyFormat.format(item.min_price)
            val maxPrice = currencyFormat.format(item.max_price)
            binding.textPriceRange.text = if (item.min_price == item.max_price) {
                minPrice
            } else {
                "$minPrice - $maxPrice"
            }
            
            binding.textMarketsCount.text = "Disponível em ${item.markets_count} mercado(s)"
            
            binding.root.setOnClickListener {
                onItemClick(item)
            }
        }
    }

    private class DiffCallback : DiffUtil.ItemCallback<ProductSearchResult>() {
        override fun areItemsTheSame(oldItem: ProductSearchResult, newItem: ProductSearchResult): Boolean {
            return oldItem.ncm == newItem.ncm && oldItem.ean == newItem.ean
        }

        override fun areContentsTheSame(oldItem: ProductSearchResult, newItem: ProductSearchResult): Boolean {
            return oldItem == newItem
        }
    }
}

