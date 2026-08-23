import aiosqlite
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from config import CONFIG

def generate_item_hash(url: str, title: str) -> str:
    """Gera um hash único SHA256 para cada item para evitar duplicatas."""
    raw = f"{url.strip()}|{title.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

async def init_db() -> None:
    """Inicializa as tabelas do banco de dados SQLite."""
    async with aiosqlite.connect(CONFIG.db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sent_items (
                id TEXT PRIMARY KEY,
                item_type TEXT NOT NULL, -- 'job' ou 'deal'
                title TEXT NOT NULL,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                price_or_salary TEXT,
                match_score REAL DEFAULT 0,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                chat_id TEXT PRIMARY KEY,
                radar_active INTEGER DEFAULT 1,
                min_job_score REAL DEFAULT 50.0,
                notify_deals INTEGER DEFAULT 1,
                notify_jobs INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT,
                search_term TEXT,
                results_count INTEGER,
                searched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await db.commit()

async def is_item_sent(item_hash: str) -> bool:
    """Verifica se um item já foi enviado anteriormente."""
    async with aiosqlite.connect(CONFIG.db_path) as db:
        async with db.execute("SELECT 1 FROM sent_items WHERE id = ?", (item_hash,)) as cursor:
            row = await cursor.fetchone()
            return row is not None

async def mark_item_sent(item_hash: str, item_type: str, title: str, source: str, url: str, price_or_salary: str = "", match_score: float = 0.0) -> None:
    """Registra o item no banco de dados como enviado."""
    async with aiosqlite.connect(CONFIG.db_path) as db:
        await db.execute("""
            INSERT OR IGNORE INTO sent_items (id, item_type, title, source, url, price_or_salary, match_score, sent_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_hash, item_type, title, source, url, price_or_salary, match_score, datetime.now().isoformat()))
        await db.commit()

async def get_user_settings(chat_id: str) -> Dict[str, Any]:
    """Obtém ou cria as configurações de um usuário."""
    async with aiosqlite.connect(CONFIG.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM user_settings WHERE chat_id = ?", (str(chat_id),)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            
            # Criar padrão
            await db.execute("""
                INSERT INTO user_settings (chat_id, radar_active, min_job_score, notify_deals, notify_jobs)
                VALUES (?, 1, 50.0, 1, 1)
            """, (str(chat_id),))
            await db.commit()
            return {
                "chat_id": str(chat_id),
                "radar_active": 1,
                "min_job_score": 50.0,
                "notify_deals": 1,
                "notify_jobs": 1
            }

async def toggle_radar_state(chat_id: str, active: bool) -> None:
    """Ativa ou desativa o radar automático para o chat_id."""
    async with aiosqlite.connect(CONFIG.db_path) as db:
        await db.execute("""
            INSERT INTO user_settings (chat_id, radar_active, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(chat_id) DO UPDATE SET radar_active = ?, updated_at = CURRENT_TIMESTAMP
        """, (str(chat_id), 1 if active else 0, 1 if active else 0))
        await db.commit()

async def get_all_active_chats() -> List[str]:
    """Retorna todos os chat_ids com radar ativo."""
    async with aiosqlite.connect(CONFIG.db_path) as db:
        async with db.execute("SELECT chat_id FROM user_settings WHERE radar_active = 1") as cursor:
            rows = await cursor.fetchall()
            return [str(r[0]) for r in rows]

async def get_statistics() -> Dict[str, int]:
    """Retorna estatísticas de vagas e ofertas monitoradas."""
    async with aiosqlite.connect(CONFIG.db_path) as db:
        async with db.execute("SELECT COUNT(*) FROM sent_items WHERE item_type = 'job'") as c1:
            total_jobs = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM sent_items WHERE item_type = 'deal'") as c2:
            total_deals = (await c2.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM user_settings WHERE radar_active = 1") as c3:
            active_users = (await c3.fetchone())[0]
        return {
            "total_jobs": total_jobs,
            "total_deals": total_deals,
            "active_users": active_users
        }
