package com.appprecos.ui.markets

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.appprecos.data.model.Market
import com.appprecos.databinding.ItemMarketBinding

class MarketsAdapter(
    private val onMarketClick: (Market) -> Unit
) : ListAdapter<Market, MarketsAdapter.MarketViewHolder>(MarketDiffCallback()) {
    
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): MarketViewHolder {
        val binding = ItemMarketBinding.inflate(
            LayoutInflater.from(parent.context),
            parent,
            false
        )
        return MarketViewHolder(binding)
    }
    
    override fun onBindViewHolder(holder: MarketViewHolder, position: Int) {
        holder.bind(getItem(position), onMarketClick)
    }
    
    class MarketViewHolder(
        private val binding: ItemMarketBinding
    ) : RecyclerView.ViewHolder(binding.root) {
        
        fun bind(market: Market, onClick: (Market) -> Unit) {
            binding.textMarketName.text = market.name
            binding.textMarketAddress.text = market.address
            
            // Set click listener on button instead of card
            binding.buttonViewProducts.setOnClickListener {
                onClick(market)
            }
        }
    }
    
    private class MarketDiffCallback : DiffUtil.ItemCallback<Market>() {
        override fun areItemsTheSame(oldItem: Market, newItem: Market): Boolean {
            return oldItem.market_id == newItem.market_id
        }
        
        override fun areContentsTheSame(oldItem: Market, newItem: Market): Boolean {
            return oldItem == newItem
        }
    }
}

