package com.appprecos.util

import android.content.Context
import com.google.gson.Gson
import java.io.InputStreamReader

data class NcmEntry(
    val Codigo: String,
    val Nome: String  // Clean product name (e.g., "Abacates")
)

data class NcmTableRoot(
    val Data_Ultima_Atualizacao: String,
    val Fonte: String,
    val Total_Entries: Int,
    val Produtos: List<NcmEntry>
)

object NcmTableManager {
    private var ncmTable: Map<String, String>? = null  // NCM code -> Clean product name
    private var isInitialized = false

    /**
     * Initialize the NCM table by loading cleaned product names
     * This should be called once when the app starts
     */
    fun initialize(context: Context) {
        if (isInitialized) return
        
        try {
            val inputStream = context.assets.open("ncm_table.json")
            val reader = InputStreamReader(inputStream, Charsets.UTF_8)
            
            val gson = Gson()
            val ncmRoot: NcmTableRoot = gson.fromJson(reader, NcmTableRoot::class.java)
            
            // Create map for fast lookup: NCM code -> Product name
            ncmTable = ncmRoot.Produtos.associate { it.Codigo to it.Nome }
            
            reader.close()
            isInitialized = true
            
            android.util.Log.d("NcmTableManager", "✓ Loaded ${ncmTable?.size} NCM product names (${ncmRoot.Data_Ultima_Atualizacao})")
        } catch (e: Exception) {
            android.util.Log.e("NcmTableManager", "Error loading NCM table", e)
            ncmTable = emptyMap()
            isInitialized = true // Mark as initialized even if failed
        }
    }

    /**
     * Get the clean product name for a given NCM code
     * Example: "07099300" -> "Abóboras"
     */
    fun getDescription(ncmCode: String): String {
        if (ncmTable == null) {
            android.util.Log.w("NcmTableManager", "NCM table not initialized")
            return ncmCode
        }
        
        // Try exact match first
        ncmTable?.get(ncmCode)?.let { return it }
        
        // Try formatting 8-digit code with dots: "07099300" -> "0709.93.00"
        if (ncmCode.length == 8 && !ncmCode.contains(".")) {
            val formatted = "${ncmCode.substring(0, 4)}.${ncmCode.substring(4, 6)}.${ncmCode.substring(6, 8)}"
            ncmTable?.get(formatted)?.let { return it }
        }
        
        // Try progressive truncation to find parent category
        var code = if (ncmCode.contains(".")) ncmCode else {
            if (ncmCode.length >= 8) {
                "${ncmCode.substring(0, 4)}.${ncmCode.substring(4, 6)}.${ncmCode.substring(6, 8)}"
            } else ncmCode
        }
        
        while (code.isNotEmpty()) {
            ncmTable?.get(code)?.let { return it }
            
            // Remove trailing parts progressively
            code = when {
                code.endsWith(".00") -> code.dropLast(3)
                code.endsWith(".0") -> code.dropLast(2)
                code.endsWith("00") && code.length > 2 -> code.dropLast(2)
                code.endsWith("0") && code.length > 1 -> code.dropLast(1)
                code.endsWith(".") -> code.dropLast(1)
                code.contains(".") -> {
                    val lastDot = code.lastIndexOf(".")
                    code.substring(0, lastDot)
                }
                else -> code.dropLast(1)
            }
        }
        
        // If still not found, return the original code
        return ncmCode
    }

    /**
     * Search for NCM entries that match the query
     * Searches both codes and product names
     */
    fun search(query: String): List<Pair<String, String>> {
        if (ncmTable == null) return emptyList()
        
        val lowercaseQuery = query.lowercase()
        return ncmTable!!
            .filter { (code, name) ->
                code.lowercase().contains(lowercaseQuery) || 
                name.lowercase().contains(lowercaseQuery)
            }
            .map { (code, name) -> code to name }
            .take(50) // Limit results for performance
    }

    /**
     * Check if the table is loaded
     */
    fun isLoaded(): Boolean = isInitialized && ncmTable != null
}

