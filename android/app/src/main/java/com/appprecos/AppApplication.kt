package com.appprecos

import android.app.Application
import com.google.android.material.color.DynamicColors
import com.appprecos.util.NcmTableManager

class AppApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
        
        // Apply dynamic colors on Android 12+ devices
        // Falls back to static colors on older versions
        DynamicColors.applyToActivitiesIfAvailable(this)
        
        // Initialize NCM table for product descriptions
        NcmTableManager.initialize(this)
    }
}

