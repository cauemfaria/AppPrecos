package com.appprecos.ui.shoppinglist

import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.appprecos.data.local.ShoppingListItem
import com.appprecos.databinding.ItemShoppingListBinding

class ShoppingListAdapter(
    private val onRemoveClick: (ShoppingListItem) -> Unit
) : ListAdapter<ShoppingListItem, ShoppingListAdapter.ViewHolder>(DiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemShoppingListBinding.inflate(
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
        private val binding: ItemShoppingListBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(item: ShoppingListItem) {
            binding.textProductName.text = item.productName
            binding.textProductInfo.text = "NCM: ${item.ncm} • ${item.unidadeComercial}"
            
            binding.buttonRemove.setOnClickListener {
                onRemoveClick(item)
            }
        }
    }

    private class DiffCallback : DiffUtil.ItemCallback<ShoppingListItem>() {
        override fun areItemsTheSame(oldItem: ShoppingListItem, newItem: ShoppingListItem): Boolean {
            return oldItem.id == newItem.id
        }

        override fun areContentsTheSame(oldItem: ShoppingListItem, newItem: ShoppingListItem): Boolean {
            return oldItem == newItem
        }
    }
}

