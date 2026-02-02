# AppPrecos - Comparador de Preços Brasileiro

Aplicativo de comparação de preços que extrai dados de produtos de cupons fiscais (NFCe) e utiliza enriquecimento de dados para padronizar produtos entre diferentes mercados.

Este projeto foi convertido de um app nativo para uma **Web App Moderna (PWA)**, permitindo instalação em qualquer celular (Android/iOS) diretamente pelo navegador.

---

## 🏗️ Visão Geral da Arquitetura

O AppPrecos utiliza uma arquitetura desacoplada para garantir uma experiência rápida ao usuário enquanto mantém alta qualidade de dados:

1.  **Extração Rápida (Backend API):** Extrai instantaneamente os dados brutos da NFCe utilizando Playwright e salva no histórico.
2.  **Enriquecimento de Produtos (Background Worker):** Um processo separado que padroniza nomes e busca imagens através da API Bluesoft Cosmos.
3.  **Frontend PWA:** Interface React moderna instalável como aplicativo, com scanner de QR Code integrado.
4.  **Banco de Dados:** Supabase (PostgreSQL) como hub central de dados.

---

## 🚀 Principais Funcionalidades Técnicas

### ✅ Fluxo de Dados Desacoplado
O processo de extração não espera mais pelo enriquecimento externo.
- **NFCe Scan:** Extraído em ~15s e imediatamente disponível no histórico.
- **Enriquecimento:** Acionado automaticamente após o scan ou manualmente pelos Ajustes. Utiliza rotação de tokens para contornar limites de API.

### ✅ Padronização Inteligente
Transforma nomes "feios" de cupons (ex: `QJ MUSS PARLAK`) em nomes limpos e padronizados (ex: `QUEIJO MUSSARELA PARLAK`) usando a **API Bluesoft Cosmos**.

### ✅ Progressive Web App (PWA)
- Instalável na tela inicial do celular.
- Funciona offline para consulta de listas.
- Notificações de atualização automática.

---

## 📂 Estrutura do Projeto

```
AppPrecos/
├── backend/                    # Backend Flask (Python)
│   ├── app.py                  # Servidor API Principal
│   ├── enrichment_service.py   # Lógica de busca de produtos (Cosmos)
│   ├── enrichment_worker.py    # Processador de background
│   ├── nfce_extractor.py       # Scraper Playwright para SEFAZ
│   └── render.yaml             # Configuração de Deploy (Render)
│
├── frontend/                   # Frontend React (Vite + TS)
│   ├── src/                    # Código fonte (Páginas, Componentes)
│   ├── public/                 # Ícones e Manifest PWA
│   └── vite.config.ts          # Configuração Vite e PWA
│
└── android/                    # (Legado) App nativo anterior
```

---

## 🛠️ Stack Tecnológica

- **Backend:** Python 3.11+, Flask, Playwright (Chromium), Gunicorn.
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Lucide Icons.
- **Database:** Supabase (PostgreSQL).
- **APIs:** Bluesoft Cosmos (Dados de Produtos).
- **Hospedagem:** Render (Web Service + Static Site).

---

## ⚙️ Instruções de Configuração

### 1. Backend (Python)

1.  **Instalar dependências:**
    ```bash
    cd backend
    pip install -r requirements.txt
    ```

2.  **Instalar Navegador Playwright:**
    ```bash
    playwright install chromium
    ```

3.  **Configurar Variáveis de Ambiente (`.env`):**
    ```env
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=your-secret-key
    COSMOS_TOKENS=token1,token2,token3
    COSMOS_USER_AGENT=Cosmos-API-Request
    ```

### 2. Frontend (React)

1.  **Instalar dependências:**
    ```bash
    cd frontend
    npm install
    ```

2.  **Configurar Variáveis de Ambiente (`.env`):**
    ```env
    VITE_API_BASE_URL=https://seu-backend.onrender.com/api
    ```

3.  **Rodar em Desenvolvimento:**
    ```bash
    npm run dev
    ```

---

## 🔄 Fluxo de Dados

1.  **Scanner:** O usuário escaneia o QR Code no app.
2.  **Extração:** O backend recebe a URL, navega via Playwright, extrai os produtos e salva na tabela `purchases`.
3.  **Gatilho:** Assim que o cupom é salvo, o backend inicia o `enrichment_worker` em uma thread separada.
4.  **Enriquecimento:** O worker busca cada produto novo na API do Cosmos, recupera o nome oficial e a imagem, e atualiza a tabela `unique_products`.
5.  **Interface:** O usuário vê o progresso em tempo real na aba Scanner e pode consultar os preços na aba Mercados ou Lista de Compras.

---

**Desenvolvido com foco em qualidade de dados, velocidade e resiliência.** 🛒✨
