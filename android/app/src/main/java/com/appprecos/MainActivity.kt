package com.appprecos

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.fragment.app.Fragment
import com.appprecos.databinding.ActivityMainBinding
import com.appprecos.ui.markets.MarketsFragment
import com.appprecos.ui.scanner.ScannerFragment
import com.appprecos.ui.settings.SettingsFragment
import com.google.android.material.badge.BadgeDrawable
import com.google.android.material.navigation.NavigationBarView

class MainActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityMainBinding
    private var currentNavigationItemId = R.id.navigation_scanner
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Enable edge-to-edge display
        WindowCompat.setDecorFitsSystemWindows(window, false)
        
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        // Apply window insets
        setupWindowInsets()
        
        // Setup navigation (either BottomNav or NavigationRail based on screen size)
        setupNavigation()
        
        // Show scanner fragment by default
        if (savedInstanceState == null) {
            showFragment(ScannerFragment())
        }
    }
    
    private fun setupWindowInsets() {
        ViewCompat.setOnApplyWindowInsetsListener(binding.fragmentContainer) { view, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            view.setPadding(systemBars.left, systemBars.top, systemBars.right, 0)
            insets
        }
    }
    
    private fun setupNavigation() {
        // Setup TopAppBar
        binding.topAppBar?.setOnMenuItemClickListener { menuItem ->
            when (menuItem.itemId) {
                R.id.action_search -> {
                    // TODO: Open search
                    true
                }
                R.id.action_refresh -> {
                    refreshCurrentFragment()
                    true
                }
                else -> false
            }
        }
        
        // Get the navigation view (either BottomNavigationView or NavigationRailView)
        val navigationView = getNavigationView()
        
        navigationView?.setOnItemSelectedListener { menuItem ->
            when (menuItem.itemId) {
                R.id.navigation_scanner -> {
                    if (currentNavigationItemId != R.id.navigation_scanner) {
                        showFragment(ScannerFragment())
                        binding.topAppBar?.title = getString(R.string.scanner_title)
                        currentNavigationItemId = R.id.navigation_scanner
                    }
                    true
                }
                R.id.navigation_markets -> {
                    if (currentNavigationItemId != R.id.navigation_markets) {
                        showFragment(MarketsFragment())
                        binding.topAppBar?.title = getString(R.string.markets_title)
                        currentNavigationItemId = R.id.navigation_markets
                    }
                    true
                }
                R.id.navigation_settings -> {
                    if (currentNavigationItemId != R.id.navigation_settings) {
                        showFragment(SettingsFragment())
                        binding.topAppBar?.title = "Settings"
                        currentNavigationItemId = R.id.navigation_settings
                    }
                    true
                }
                else -> false
            }
        }
        
        // Set initial selected item
        navigationView?.selectedItemId = R.id.navigation_scanner
    }
    
    fun switchToMarketsTab() {
        binding.bottomNavigation?.selectedItemId = R.id.navigation_markets
    }
    
    private fun refreshCurrentFragment() {
        supportFragmentManager.fragments.firstOrNull()?.let { fragment ->
            if (fragment is MarketsFragment) {
                fragment.refresh()
            }
        }
    }
    
    private fun getNavigationView(): NavigationBarView? {
        // Try to get BottomNavigationView first (compact/medium screens)
        return try {
            binding.bottomNavigation
        } catch (e: Exception) {
            // If not found, try NavigationRailView (large screens)
            try {
                binding.navigationRail
            } catch (e: Exception) {
                null
            }
        }
    }
    
    private fun showFragment(fragment: Fragment) {
        supportFragmentManager.beginTransaction()
            .setCustomAnimations(
                R.anim.fade_in,
                R.anim.fade_out,
                R.anim.fade_in,
                R.anim.fade_out
            )
            .replace(R.id.fragmentContainer, fragment)
            .commit()
    }
    
    /**
     * Show a badge on a navigation item
     * @param navigationItemId The menu item id (R.id.navigation_scanner or R.id.navigation_markets)
     * @param count The number to display on the badge (0 to hide number, show dot only)
     */
    fun showBadge(navigationItemId: Int, count: Int = 0) {
        val navigationView = getNavigationView()
        val badge = navigationView?.getOrCreateBadge(navigationItemId)
        badge?.apply {
            isVisible = true
            if (count > 0) {
                number = count
            } else {
                clearNumber()
            }
        }
    }
    
    /**
     * Hide badge on a navigation item
     */
    fun hideBadge(navigationItemId: Int) {
        val navigationView = getNavigationView()
        navigationView?.removeBadge(navigationItemId)
    }
}

