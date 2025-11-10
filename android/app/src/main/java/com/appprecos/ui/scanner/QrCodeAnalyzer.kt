package com.appprecos.ui.scanner

import android.annotation.SuppressLint
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage

class QrCodeAnalyzer(
    private val onQrCodeDetected: (String) -> Unit
) : ImageAnalysis.Analyzer {

    private val options = BarcodeScannerOptions.Builder()
        .setBarcodeFormats(Barcode.FORMAT_QR_CODE)
        .build()

    private val scanner = BarcodeScanning.getClient(options)
    private var lastScannedTime = 0L
    private val scanThrottleMs = 2000L // Prevent duplicate scans within 2 seconds

    @SuppressLint("UnsafeOptInUsageError")
    override fun analyze(imageProxy: ImageProxy) {
        val mediaImage = imageProxy.image
        if (mediaImage != null) {
            val image = InputImage.fromMediaImage(
                mediaImage,
                imageProxy.imageInfo.rotationDegrees
            )

            scanner.process(image)
                .addOnSuccessListener { barcodes ->
                    for (barcode in barcodes) {
                        barcode.rawValue?.let { qrCode ->
                            val currentTime = System.currentTimeMillis()
                            if (currentTime - lastScannedTime > scanThrottleMs) {
                                lastScannedTime = currentTime
                                onQrCodeDetected(qrCode)
                            }
                        }
                    }
                }
                .addOnFailureListener {
                    // Handle barcode scanning failure
                }
                .addOnCompleteListener {
                    imageProxy.close()
                }
        } else {
            imageProxy.close()
        }
    }
}


