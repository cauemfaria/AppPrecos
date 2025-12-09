package com.appprecos.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "shopping_list")
data class ShoppingListItem(
    @PrimaryKey(autoGenerate = true)
    val id: Long = 0,
    val productName: String,
    val ean: String,
    val ncm: String,
    val unidadeComercial: String,
    val addedAt: Long = System.currentTimeMillis()
)

