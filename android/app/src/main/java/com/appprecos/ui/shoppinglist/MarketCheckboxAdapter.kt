package com.appprecos.ui.shoppinglist

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.appprecos.data.model.Market
import com.appprecos.databinding.ItemMarketCheckboxBinding

class MarketCheckboxAdapter(
    private val onMarketToggle: (String) -> Unit,
    private val isSelected: (String) -> Boolean
) : ListAdapter<Market, MarketCheckboxAdapter.ViewHolder>(DiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemMarketCheckboxBinding.inflate(
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
        private val binding: ItemMarketCheckboxBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(market: Market) {
            binding.textMarketName.text = market.name
            binding.textMarketAddress.text = market.address
            binding.checkboxMarket.isChecked = isSelected(market.market_id)
            
            binding.root.setOnClickListener {
                binding.checkboxMarket.isChecked = !binding.checkboxMarket.isChecked
                onMarketToggle(market.market_id)
            }
            
            binding.checkboxMarket.setOnClickListener {
                onMarketToggle(market.market_id)
            }
        }
    }

    private class DiffCallback : DiffUtil.ItemCallback<Market>() {
        override fun areItemsTheSame(oldItem: Market, newItem: Market): Boolean {
            return oldItem.market_id == newItem.market_id
        }

        override fun areContentsTheSame(oldItem: Market, newItem: Market): Boolean {
            return oldItem == newItem
        }
    }
}

