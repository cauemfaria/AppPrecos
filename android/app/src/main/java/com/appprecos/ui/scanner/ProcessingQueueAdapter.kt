package com.appprecos.ui.scanner

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.appprecos.R
import com.appprecos.data.service.ProcessingStatus
import com.appprecos.data.service.QrProcessingItem
import com.appprecos.databinding.ItemProcessingQueueBinding

class ProcessingQueueAdapter(
    private val onDismissClick: (QrProcessingItem) -> Unit
) : ListAdapter<QrProcessingItem, ProcessingQueueAdapter.ViewHolder>(DiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemProcessingQueueBinding.inflate(
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
        private val binding: ItemProcessingQueueBinding
    ) : RecyclerView.ViewHolder(binding.root) {

        fun bind(item: QrProcessingItem) {
            val context = binding.root.context
            
            when (item.status) {
                ProcessingStatus.QUEUED -> {
                    binding.progressItem.visibility = View.VISIBLE
                    binding.iconStatus.visibility = View.GONE
                    binding.textItemTitle.text = context.getString(R.string.queue_status_queued)
                    binding.textItemSubtitle.visibility = View.GONE
                    binding.buttonDismiss.visibility = View.GONE
                }
                ProcessingStatus.SENDING -> {
                    binding.progressItem.visibility = View.VISIBLE
                    binding.iconStatus.visibility = View.GONE
                    binding.textItemTitle.text = context.getString(R.string.queue_status_sending)
                    binding.textItemSubtitle.visibility = View.GONE
                    binding.buttonDismiss.visibility = View.GONE
                }
                ProcessingStatus.PROCESSING -> {
                    binding.progressItem.visibility = View.VISIBLE
                    binding.iconStatus.visibility = View.GONE
                    binding.textItemTitle.text = context.getString(R.string.queue_status_processing)
                    binding.textItemSubtitle.visibility = View.GONE
                    binding.buttonDismiss.visibility = View.GONE
                }
                ProcessingStatus.SUCCESS -> {
                    binding.progressItem.visibility = View.GONE
                    binding.iconStatus.visibility = View.VISIBLE
                    binding.iconStatus.setImageResource(R.drawable.ic_check)
                    binding.textItemTitle.text = item.marketName ?: context.getString(R.string.queue_status_success)
                    if (item.productsCount != null && item.productsCount > 0) {
                        binding.textItemSubtitle.visibility = View.VISIBLE
                        binding.textItemSubtitle.text = context.getString(
                            R.string.queue_products_count, 
                            item.productsCount
                        )
                    } else {
                        binding.textItemSubtitle.visibility = View.GONE
                    }
                    binding.buttonDismiss.visibility = View.VISIBLE
                }
                ProcessingStatus.ERROR -> {
                    binding.progressItem.visibility = View.GONE
                    binding.iconStatus.visibility = View.VISIBLE
                    binding.iconStatus.setImageResource(R.drawable.ic_error)
                    binding.textItemTitle.text = context.getString(R.string.queue_status_error)
                    binding.textItemSubtitle.visibility = View.VISIBLE
                    binding.textItemSubtitle.text = item.errorMessage ?: "Erro desconhecido"
                    binding.buttonDismiss.visibility = View.VISIBLE
                }
                ProcessingStatus.DUPLICATE -> {
                    binding.progressItem.visibility = View.GONE
                    binding.iconStatus.visibility = View.VISIBLE
                    binding.iconStatus.setImageResource(R.drawable.ic_warning)
                    binding.textItemTitle.text = context.getString(R.string.queue_status_duplicate)
                    binding.textItemSubtitle.visibility = View.GONE
                    binding.buttonDismiss.visibility = View.VISIBLE
                }
            }
            
            binding.buttonDismiss.setOnClickListener {
                onDismissClick(item)
            }
        }
    }

    private class DiffCallback : DiffUtil.ItemCallback<QrProcessingItem>() {
        override fun areItemsTheSame(oldItem: QrProcessingItem, newItem: QrProcessingItem): Boolean {
            return oldItem.url == newItem.url
        }

        override fun areContentsTheSame(oldItem: QrProcessingItem, newItem: QrProcessingItem): Boolean {
            return oldItem == newItem
        }
    }
}

