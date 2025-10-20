package com.appprecos

import android.app.Application
import com.google.android.material.color.DynamicColors

class AppApplication : Application() {
    
    override fun onCreate() {
        super.onCreate()
        
        // Apply dynamic colors on Android 12+ devices
        // Falls back to static colors on older versions
        DynamicColors.applyToActivitiesIfAvailable(this)
    }
}

