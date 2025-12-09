(() => {
  const registerServiceWorker = async () => {
    if (!("serviceWorker" in navigator)) {
      return;
    }
    try {
      await navigator.serviceWorker.register("/static/pwa/service-worker.js");
      console.info("[PWA] Service worker registrado");
    } catch (err) {
      console.warn("[PWA] Falha ao registrar service worker", err);
    }
  };

  const setupInstallPrompt = () => {
    let deferredPrompt;
    const template = document.getElementById("install-toast-template");
    if (!template) return;
    const toast = template.content.firstElementChild.cloneNode(true);
    document.body.appendChild(toast);

    window.addEventListener("beforeinstallprompt", (event) => {
      event.preventDefault();
      deferredPrompt = event;
      toast.classList.remove("hidden");
    });

    toast.querySelector("[data-dismiss]")?.addEventListener("click", () => {
      toast.classList.add("hidden");
    });

    toast.querySelector("[data-install]")?.addEventListener("click", async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const choice = await deferredPrompt.userChoice;
      if (choice.outcome !== "accepted") {
        console.info("[PWA] Instalação cancelada");
      }
      toast.classList.add("hidden");
      deferredPrompt = null;
    });
  };

  document.addEventListener("DOMContentLoaded", () => {
    registerServiceWorker();
    setupInstallPrompt();
  });
})();

