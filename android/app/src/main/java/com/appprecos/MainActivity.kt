package com.appprecos

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.fragment.app.Fragment
import com.appprecos.databinding.ActivityMainBinding
import com.appprecos.ui.markets.MarketsFragment
import com.appprecos.ui.scanner.ScannerFragment
import com.google.android.material.tabs.TabLayout

class MainActivity : AppCompatActivity() {
    
    private lateinit var binding: ActivityMainBinding
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupTabs()
        
        // Show scanner fragment by default
        if (savedInstanceState == null) {
            showFragment(ScannerFragment())
        }
    }
    
    private fun setupTabs() {
        binding.tabLayout.addTab(binding.tabLayout.newTab().setText("📷 Scan"))
        binding.tabLayout.addTab(binding.tabLayout.newTab().setText("🏪 Markets"))
        
        binding.tabLayout.addOnTabSelectedListener(object : TabLayout.OnTabSelectedListener {
            override fun onTabSelected(tab: TabLayout.Tab) {
                when (tab.position) {
                    0 -> showFragment(ScannerFragment())
                    1 -> showFragment(MarketsFragment())
                }
            }
            
            override fun onTabUnselected(tab: TabLayout.Tab) {}
            override fun onTabReselected(tab: TabLayout.Tab) {}
        })
    }
    
    private fun showFragment(fragment: Fragment) {
        supportFragmentManager.beginTransaction()
            .replace(R.id.fragmentContainer, fragment)
            .commit()
    }
}

