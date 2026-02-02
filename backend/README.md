# AppPrecos - Backend (Flask)

Este é o backend do aplicativo AppPrecos, construído com Flask e Playwright. Ele é responsável pela extração de dados de NFCe e pelo enriquecimento de produtos.

## 🚀 Início Rápido

1.  **Instalar dependências:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Instalar Navegador Playwright:**
    ```bash
    playwright install chromium
    ```

3.  **Configurar Variáveis de Ambiente:**
    Crie um arquivo `.env` nesta pasta com as chaves do Supabase e Cosmos API.

4.  **Rodar Servidor:**
    ```bash
    python app.py
    ```

## 🏗️ Estrutura

-   `app.py`: Servidor Flask e endpoints da API.
-   `enrichment_service.py`: Lógica de integração com a API Bluesoft Cosmos.
-   `enrichment_worker.py`: Script para processamento em background de produtos pendentes.
-   `nfce_extractor.py`: Motor de raspagem de dados utilizando Playwright.

---

Para informações completas sobre a arquitetura e o frontend, consulte o [README principal na raiz do projeto](../README.md).
