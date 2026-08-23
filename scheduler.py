import asyncio
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from config import CONFIG, PROFILE
from database import is_item_sent, mark_item_sent, generate_item_hash, get_all_active_chats
from scrapers.jobs_scraper import get_all_jobs, JobOffer
from scrapers.deals_scraper import get_all_deals, TechDeal

async def send_job_notification(bot: Bot, chat_id: str, job: JobOffer) -> None:
    """Envia notificação de nova vaga formatada com botões inline."""
    skills_text = " • ".join(job.matched_skills[:6]) if job.matched_skills else "Geral"
    
    text = (
        f"🎯 *NOVA VAGA ENCONTRADA!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💼 *{job.title}*\n"
        f"🏢 *Empresa:* `{job.company}`\n"
        f"📍 *Local:* `{job.location}`\n"
        f"📊 *Afinidade:* `{job.match_score}%` — *{job.badge}*\n"
        f"🛠️ *Skills:* {skills_text}\n"
        f"💰 *Salário:* `{job.salary}`\n"
        f"📡 *Fonte:* `{job.source}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 *Resumo:* _{job.description[:180]}..._\n"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🚀 Ver Vaga / Candidatar-se", url=job.url),
            InlineKeyboardButton("💼 Meu LinkedIn", url=PROFILE.linkedin_url)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup,
            disable_web_page_preview=False
        )
    except Exception as e:
        print(f"Erro ao enviar notificação de vaga para {chat_id}: {e}")

async def send_deal_notification(bot: Bot, chat_id: str, deal: TechDeal) -> None:
    """Envia notificação de promoção formatada com imagem e botões."""
    coupon_text = f"\n🎟️ *Cupom:* `{deal.coupon}`" if deal.coupon else ""
    
    caption = (
        f"⚡ *PROMOÇÃO RELÂMPAGO TECH!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *{deal.title}*\n"
        f"🏷️ *Preço:* `{deal.price}`\n"
        f"🏪 *Loja:* `{deal.store}`{coupon_text}\n"
        f"🏷️ *Status:* `{deal.discount}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    keyboard = [
        [InlineKeyboardButton("🛒 Acessar Oferta Agora", url=deal.url)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        if deal.image_url and deal.image_url.startswith("http"):
            await bot.send_photo(
                chat_id=chat_id,
                photo=deal.image_url,
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup,
                disable_web_page_preview=False
            )
    except Exception as e:
        print(f"Erro ao enviar notificação de promoção para {chat_id}: {e}")

async def check_jobs_task(bot: Bot) -> None:
    """Tarefa periódica de varredura de vagas."""
    print("🔍 [Radar Vagas] Iniciando varredura periódica...")
    try:
        jobs = await get_all_jobs()
        active_chats = await get_all_active_chats()
        if not active_chats and CONFIG.admin_chat_id:
            active_chats = [CONFIG.admin_chat_id]
            
        count_sent = 0
        for job in jobs:
            # Enviar apenas vagas com mais de 50% de match score
            if job.match_score >= 50.0:
                item_hash = generate_item_hash(job.url, job.title)
                if not await is_item_sent(item_hash):
                    for chat_id in active_chats:
                        await send_job_notification(bot, chat_id, job)
                        await asyncio.sleep(1.0) # Rate limit safety
                    await mark_item_sent(item_hash, "job", job.title, job.source, job.url, job.salary, job.match_score)
                    count_sent += 1
                    if count_sent >= 5: # Limita a 5 novas vagas por ciclo para não poluir
                        break
        print(f"✅ [Radar Vagas] Varredura concluída. Novas vagas enviadas: {count_sent}")
    except Exception as e:
        print(f"❌ [Radar Vagas] Erro durante a varredura: {e}")

async def check_deals_task(bot: Bot) -> None:
    """Tarefa periódica de varredura de promoções."""
    print("⚡ [Radar Promos] Iniciando varredura periódica de ofertas...")
    try:
        deals = await get_all_deals()
        active_chats = await get_all_active_chats()
        if not active_chats and CONFIG.admin_chat_id:
            active_chats = [CONFIG.admin_chat_id]
            
        count_sent = 0
        for deal in deals:
            item_hash = generate_item_hash(deal.url, deal.title)
            if not await is_item_sent(item_hash):
                for chat_id in active_chats:
                    await send_deal_notification(bot, chat_id, deal)
                    await asyncio.sleep(1.0)
                await mark_item_sent(item_hash, "deal", deal.title, deal.store, deal.url, deal.price)
                count_sent += 1
                if count_sent >= 4: # Limita a 4 novas promoções por ciclo
                    break
        print(f"✅ [Radar Promos] Varredura concluída. Novas ofertas enviadas: {count_sent}")
    except Exception as e:
        print(f"❌ [Radar Promos] Erro durante a varredura: {e}")
