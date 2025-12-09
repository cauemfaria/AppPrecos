package com.appprecos.data.local

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface ShoppingListDao {
    
    @Query("SELECT * FROM shopping_list ORDER BY addedAt DESC")
    fun getAllItems(): Flow<List<ShoppingListItem>>
    
    @Query("SELECT * FROM shopping_list ORDER BY addedAt DESC")
    suspend fun getAllItemsList(): List<ShoppingListItem>
    
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(item: ShoppingListItem): Long
    
    @Delete
    suspend fun delete(item: ShoppingListItem)
    
    @Query("DELETE FROM shopping_list WHERE id = :id")
    suspend fun deleteById(id: Long)
    
    @Query("DELETE FROM shopping_list")
    suspend fun deleteAll()
    
    @Query("SELECT COUNT(*) FROM shopping_list")
    suspend fun getCount(): Int
    
    @Query("SELECT EXISTS(SELECT 1 FROM shopping_list WHERE ean = :ean AND ean != 'SEM GTIN' LIMIT 1)")
    suspend fun existsByEan(ean: String): Boolean
    
    @Query("SELECT EXISTS(SELECT 1 FROM shopping_list WHERE ncm = :ncm AND productName = :productName LIMIT 1)")
    suspend fun existsByNcmAndName(ncm: String, productName: String): Boolean
}

