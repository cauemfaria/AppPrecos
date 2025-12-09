(() => {
  const qrResult = document.getElementById("qr-result");
  const submitBtn = document.getElementById("qr-submit");
  const resetBtn = document.getElementById("qr-reset");
  const statusBox = document.getElementById("qr-status");

  if (!qrResult || !submitBtn || !resetBtn || !statusBox) {
    return;
  }

  let lastResult = "";
  let html5QrCode;

  const setStatus = (message, kind = "info") => {
    statusBox.textContent = message;
    statusBox.dataset.kind = kind;
  };

  const startScanner = () => {
    html5QrCode = new Html5Qrcode("qr-reader", {
      formatsToSupport: [Html5QrcodeSupportedFormats.QR_CODE],
    });
    html5QrCode
      .start(
        { facingMode: "environment" },
        {
          fps: 10,
          qrbox: 250,
        },
        (decodedText) => {
          if (decodedText === lastResult) {
            return;
          }
          lastResult = decodedText;
          qrResult.value = decodedText;
          submitBtn.disabled = false;
          setStatus("QR Code capturado. Envie para processar.", "success");
        },
        (error) => {
          console.debug("[QR] frame error", error);
        },
      )
      .catch((err) => {
        setStatus(`Erro ao iniciar câmera: ${err}`, "error");
      });
  };

  const submitReceipt = async () => {
    if (!lastResult) return;
    submitBtn.disabled = true;
    setStatus("Enviando NFC-e para processamento...", "info");
    try {
      const response = await fetch("/api/nfce/extract/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: lastResult,
          save: true,
          async: true,
        }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || "Falha desconhecida");
      }
      setStatus(
        `Processamento iniciado! Consulte ${data.check_status_at} em alguns segundos.`,
        "success",
      );
    } catch (err) {
      console.error(err);
      setStatus(`Erro ao enviar NFC-e: ${err.message}`, "error");
      submitBtn.disabled = false;
    }
  };

  const resetForm = () => {
    lastResult = "";
    qrResult.value = "";
    submitBtn.disabled = true;
    setStatus("Aguardando QR Code...");
  };

  submitBtn.addEventListener("click", submitReceipt);
  resetBtn.addEventListener("click", resetForm);
  setStatus("Aguardando QR Code...");
  startScanner();
})();


