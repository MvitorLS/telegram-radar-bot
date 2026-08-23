# 🤖 Telegram Radar Bot — Vagas & Promoções Tech

Bot inteligente para Telegram desenvolvido sob medida para **Matheus Vitor Lourenço Schionato**, integrando:
1. 🎯 **Radar de Vagas de TI (Estágio & Júnior)**: Rastreamento automático e matchmaking de afinidade (% de compatibilidade) com o seu currículo (PHP, Python, Node, React, Docker, Linux, Celepar/Lottopar).
2. ⚡ **Radar de Promoções de Eletrônicos & Hardware**: Monitoramento de ofertas relâmpago de smartphones (POCO, Xiaomi), SSDs, GPUs, periféricos, monitores e hardware gamer.

---

## 🚀 Como Iniciar

### 1. Criar o Bot no Telegram
1. Abra o Telegram e procure por **`@BotFather`**.
2. Envie o comando `/newbot`.
3. Escolha o nome do seu bot (ex: `Vitor Radar Bot`) e o username (ex: `vitor_radar_bot`).
4. O BotFather vai te dar um **Token HTTP API** (ex: `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`).

### 2. Configurar o Token
Copie o arquivo `.env.example` para `.env` e adicione o seu token:
```bash
cp .env.example .env
nano .env  # Cole o token no TELEGRAM_BOT_TOKEN
```

### 3. Rodar Localmente
```bash
cd /home/vitor/Projetos/telegram-radar-bot
source .venv/bin/activate
python3 bot.py
```

### 4. Rodar 24/7 com Docker Compose
```bash
docker compose up -d
```

---

## 🎮 Comandos do Bot no Telegram

| Comando | Descrição |
| :--- | :--- |
| `/start` | Menu interativo com botões rápidos. |
| `/vagas` | Busca instantânea das vagas de Estágio e Júnior com maior Match Score. |
| `/promocoes` | Busca instantânea das melhores promoções de eletrônicos do dia. |
| `/buscar <termo>` | Busca customizada (ex: `/buscar react`, `/buscar poco x6`, `/buscar curitiba`). |
| `/perfil` | Exibe o perfil profissional cadastrado (skills, histórico, GitHub e LinkedIn). |
| `/radar_on` | Ativa notificações automáticas periódicas. |
| `/radar_off` | Pausa notificações automáticas. |
| `/status` | Exibe estatísticas de vagas/ofertas enviadas e status do banco SQLite. |

---

## 🛠️ Tecnologias Utilizadas
- **Python 3.14+**
- **python-telegram-bot v22** (Async / Await)
- **httpx & BeautifulSoup4** (Web Scraping assíncrono de alta performance)
- **APScheduler** (Agendador de tarefas em background)
- **aiosqlite** (Banco de dados SQLite assíncrono com prevenção de duplicatas)
- **Docker & Docker Compose**
