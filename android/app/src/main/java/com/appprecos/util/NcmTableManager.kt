package com.appprecos.util

import android.content.Context
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import java.io.InputStreamReader

data class NcmEntry(
    val Codigo: String,
    val Descricao: String
)

object NcmTableManager {
    private var ncmTable: Map<String, String>? = null
    private var isInitialized = false

    /**
     * Initialize the NCM table by loading the JSON file from assets
     * This should be called once when the app starts or when first needed
     */
    fun initialize(context: Context) {
        if (isInitialized) return
        
        try {
            val inputStream = context.assets.open("ncm_table.json")
            val reader = InputStreamReader(inputStream, Charsets.UTF_8)
            
            val gson = Gson()
            val listType = object : TypeToken<List<NcmEntry>>() {}.type
            val entries: List<NcmEntry> = gson.fromJson(reader, listType)
            
            // Create a map for fast lookup: NCM code -> Description
            ncmTable = entries.associate { it.Codigo to it.Descricao }
            
            reader.close()
            isInitialized = true
            
            android.util.Log.d("NcmTableManager", "Loaded ${ncmTable?.size} NCM entries")
        } catch (e: Exception) {
            android.util.Log.e("NcmTableManager", "Error loading NCM table", e)
            ncmTable = emptyMap()
        }
    }

    /**
     * Get the description for a given NCM code
     * Returns the description if found, or the original code if not found
     */
    fun getDescription(ncmCode: String): String {
        // Ensure the table is initialized
        if (ncmTable == null) {
            android.util.Log.w("NcmTableManager", "NCM table not initialized, returning code")
            return ncmCode
        }
        
        // Try exact match first
        ncmTable?.get(ncmCode)?.let { return cleanDescription(it) }
        
        // If not found, try progressive truncation (e.g., "1234.56.78" -> "1234.56.7" -> "1234.56")
        var code = ncmCode
        while (code.isNotEmpty()) {
            ncmTable?.get(code)?.let { return cleanDescription(it) }
            
            // Remove last character/segment
            code = when {
                code.endsWith("0") && code.length > 1 -> code.dropLast(1)
                code.contains(".") -> {
                    val lastDot = code.lastIndexOf(".")
                    if (lastDot > 0) {
                        val beforeDot = code.substring(0, lastDot)
                        val afterDot = code.substring(lastDot + 1)
                        if (afterDot.length > 1) {
                            "$beforeDot.${afterDot.dropLast(1)}"
                        } else {
                            beforeDot
                        }
                    } else {
                        ""
                    }
                }
                else -> code.dropLast(1)
            }
        }
        
        // If still not found, return the original code
        return ncmCode
    }

    /**
     * Clean up the description text
     * Fixes encoding issues and removes extra spaces
     */
    private fun cleanDescription(description: String): String {
        return description
            .replace("A�", "ã")
            .replace("A-", "í")
            .replace("Ac", "é")
            .replace("A3", "ó")
            .replace("A'", "ô")
            .replace("AA�", "ão")
            .replace("A�", "á")
            .replace("AA�", "ça")
            .replace("A1", "á")
            .replace("Aç", "ê")
            .replace("AO", "ú")
            .replace("A2", "â")
            .trim()
    }

    /**
     * Search for NCM entries that match the query
     * Searches both codes and descriptions
     */
    fun search(query: String): List<Pair<String, String>> {
        if (ncmTable == null) return emptyList()
        
        val lowercaseQuery = query.lowercase()
        return ncmTable!!
            .filter { (code, description) ->
                code.lowercase().contains(lowercaseQuery) || 
                cleanDescription(description).lowercase().contains(lowercaseQuery)
            }
            .map { (code, description) -> code to cleanDescription(description) }
            .take(50) // Limit results for performance
    }

    /**
     * Check if the table is loaded
     */
    fun isLoaded(): Boolean = isInitialized && ncmTable != null
}

