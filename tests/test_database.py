import pytest

import database
from config import CONFIG


@pytest.fixture(autouse=True)
async def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(CONFIG, "db_path", str(tmp_path / "test.db"))
    await database.init_db()


def test_hash_ignora_caixa_e_espacos_do_titulo():
    a = database.generate_item_hash("https://x.com/1", "Vaga Python ")
    b = database.generate_item_hash("https://x.com/1", "vaga python")
    assert a == b
    assert a != database.generate_item_hash("https://x.com/2", "vaga python")


async def test_item_enviado_nao_e_reenviado():
    h = database.generate_item_hash("https://x.com/1", "Vaga")
    assert not await database.is_item_sent(h)
    await database.mark_item_sent(h, "job", "Vaga", "GitHub", "https://x.com/1", match_score=80)
    await database.mark_item_sent(h, "job", "Vaga", "GitHub", "https://x.com/1", match_score=80)
    assert await database.is_item_sent(h)
    assert (await database.get_statistics())["total_jobs"] == 1


async def test_liga_e_desliga_radar():
    await database.toggle_radar_state("42", True)
    assert "42" in await database.get_all_active_chats()
    await database.toggle_radar_state("42", False)
    assert "42" not in await database.get_all_active_chats()
