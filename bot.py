import asyncio
import os
import sys
import re

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config import CONFIG, PROFILE
from database import init_db, get_user_settings, toggle_radar_state, get_statistics
from scrapers.jobs_scraper import get_all_jobs
from scrapers.deals_scraper import get_all_deals
from scheduler import check_jobs_task, check_deals_task

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Retorna o teclado do menu principal do bot."""
    keyboard = [
        [
            InlineKeyboardButton("🎯 Radar de Vagas (Estágio/Jr)", callback_data="btn_vagas"),
            InlineKeyboardButton("⚡ Promoções de Tech", callback_data="btn_promos")
        ],
        [
            InlineKeyboardButton("👤 Meu Perfil Profissional", callback_data="btn_perfil"),
            InlineKeyboardButton("📊 Status do Radar", callback_data="btn_status")
        ],
        [
            InlineKeyboardButton("🔔 Ativar Alertas", callback_data="btn_radar_on"),
            InlineKeyboardButton("🔕 Pausar Alertas", callback_data="btn_radar_off")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comando /start — Apresentação e menu principal."""
    user = update.effective_user
    chat_id = str(update.effective_chat.id)
    
    # Registra no banco
    await get_user_settings(chat_id)
    
    welcome_text = (
        f"👋 *Olá, {user.first_name}! Bem-vindo ao Radar Bot!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 *Seu Assistente Pessoal de Carreira & Ofertas*\n\n"
        f"🎯 **Radar de Vagas:** Monitoro constantemente oportunidades de **Estágio & Júnior** "
        f"com pontuação de afinidade (% de Match) baseada no seu currículo e GitHub.\n\n"
        f"⚡ **Radar de Promoções:** Rastreo ofertas de hardware, periféricos, POCO/Xiaomi e eletrônicos.\n\n"
        f"👇 *Escolha uma opção no menu abaixo ou use os comandos:* /vagas, /promocoes, /perfil, /buscar"
    )
    
    if update.message:
        await update.message.reply_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )
    elif update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_main_menu_keyboard()
        )

async def vagas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Busca instantânea de vagas com matchmaking."""
    query = update.callback_query
    msg_target = query.message if query else update.message
    
    status_msg = await msg_target.reply_text("🔍 *Rastreando vagas de Estágio e Júnior com seu perfil...*", parse_mode=ParseMode.MARKDOWN)
    
    try:
        jobs = await get_all_jobs()
        top_jobs = jobs[:5]
        
        if not top_jobs:
            await status_msg.edit_text("⚠️ Nenhuma vaga nova encontrada no momento. Tente novamente em instantes!")
            return
            
        await status_msg.delete()
        
        for job in top_jobs:
            skills_text = " • ".join(job.matched_skills[:6]) if job.matched_skills else "Geral"
            text = (
                f"💼 *{job.title}*\n"
                f"🏢 *Empresa:* `{job.company}`\n"
                f"📍 *Local:* `{job.location}`\n"
                f"📊 *Match Score:* `{job.match_score}%` — *{job.badge}*\n"
                f"🛠️ *Skills:* {skills_text}\n"
                f"💰 *Faixa:* `{job.salary}`\n"
                f"📡 *Fonte:* `{job.source}`\n"
            )
            
            keyboard = [[
                InlineKeyboardButton("🚀 Ver Vaga / Candidatar-se", url=job.url),
                InlineKeyboardButton("💼 Meu LinkedIn", url=PROFILE.linkedin_url)
            ]]
            
            await msg_target.reply_text(
                text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            await asyncio.sleep(0.5)
            
        # Botão de retorno
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu Principal", callback_data="btn_menu")]])
        await msg_target.reply_text("✨ *Essas são as melhores oportunidades compatíveis no momento!*", parse_mode=ParseMode.MARKDOWN, reply_markup=back_kb)
    except Exception as e:
        await status_msg.edit_text(f"❌ Erro ao buscar vagas: {e}")

async def promocoes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Busca instantânea de promoções de eletrônicos e hardware."""
    query = update.callback_query
    msg_target = query.message if query else update.message
    
    status_msg = await msg_target.reply_text("⚡ *Buscando as melhores ofertas de eletrônicos e hardware...*", parse_mode=ParseMode.MARKDOWN)
    
    try:
        deals = await get_all_deals()
        top_deals = deals[:5]
        
        if not top_deals:
            await status_msg.edit_text("⚠️ Nenhuma promoção encontrada no momento.")
            return
            
        await status_msg.delete()
        
        for deal in top_deals:
            coupon_text = f"\n🎟️ *Cupom:* `{deal.coupon}`" if deal.coupon else ""
            caption = (
                f"⚡ *{deal.discount}*\n"
                f"📦 *{deal.title}*\n"
                f"🏷️ *Preço:* `{deal.price}`\n"
                f"🏪 *Loja:* `{deal.store}`{coupon_text}\n"
            )
            keyboard = [[InlineKeyboardButton("🛒 Acessar Oferta", url=deal.url)]]
            
            try:
                if deal.image_url and deal.image_url.startswith("http"):
                    await msg_target.reply_photo(
                        photo=deal.image_url,
                        caption=caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                else:
                    await msg_target.reply_text(
                        caption,
                        parse_mode=ParseMode.MARKDOWN,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            except Exception:
                await msg_target.reply_text(
                    caption,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            await asyncio.sleep(0.5)
            
        back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Menu Principal", callback_data="btn_menu")]])
        await msg_target.reply_text("🔥 *Ofertas atualizadas em tempo real!*", parse_mode=ParseMode.MARKDOWN, reply_markup=back_kb)
    except Exception as e:
        await status_msg.edit_text(f"❌ Erro ao buscar promoções: {e}")

async def perfil_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe o perfil profissional do Vitor usado no matchmaking."""
    query = update.callback_query
    msg_target = query.message if query else update.message
    
    skills_list = " • ".join([f"`{s}`" for s in PROFILE.core_skills[:18]])
    
    text = (
        f"👤 *PERFIL PROFISSIONAL CADASTRADO*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎓 *Nome:* {PROFILE.name}\n"
        f"💼 *Cargo Alvo:* {PROFILE.title}\n"
        f"📍 *Localização:* {PROFILE.location}\n"
        f"🏛️ *Formação:* {PROFILE.education}\n\n"
        f"🛠️ *Principais Tecnologias & Stacks:*\n"
        f"{skills_list}\n\n"
        f"📌 *Experiências Recentes:*\n"
        f"• **Celepar** — Estagiário de Desenvolvimento\n"
        f"• **Lottopar** — Estagiário de TI (ETL & Suporte)\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔗 *Links Profissionais:* [GitHub]({PROFILE.github_url}) | [LinkedIn]({PROFILE.linkedin_url})"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("🐙 GitHub", url=PROFILE.github_url),
            InlineKeyboardButton("💼 LinkedIn", url=PROFILE.linkedin_url)
        ],
        [InlineKeyboardButton("🔙 Menu Principal", callback_data="btn_menu")]
    ]
    
    if query:
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)

async def buscar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Busca personalizada por termo (/buscar <termo>)."""
    if not context.args:
        await update.message.reply_text("💡 *Como usar:* `/buscar <termo>`\nExemplo: `/buscar react` ou `/buscar poco x6` ou `/buscar estágio`", parse_mode=ParseMode.MARKDOWN)
        return
        
    raw_query = " ".join(context.args).strip()
    # Sanitiza o termo de busca (limite de 50 caracteres e remoção de caracteres de controle)
    query_str = re.sub(r'[\x00-\x1f\x7f]', '', raw_query)[:50].strip()
    
    if not query_str:
        await update.message.reply_text("⚠️ Termo de busca inválido.", parse_mode=ParseMode.MARKDOWN)
        return
        
    status_msg = await update.message.reply_text(f"🔍 *Buscando por '{query_str}' em vagas e promoções...*", parse_mode=ParseMode.MARKDOWN)
    
    # 1. Buscar vagas
    jobs = await get_all_jobs(custom_query=query_str)
    # 2. Buscar promoções
    deals = await get_all_deals(custom_query=query_str)
    
    await status_msg.delete()
    
    if not jobs and not deals:
        await update.message.reply_text(f"⚠️ Nenhum resultado encontrado para *'{query_str}'*.", parse_mode=ParseMode.MARKDOWN)
        return
        
    # Exibir até 3 vagas
    if jobs:
        await update.message.reply_text(f"💼 *Vagas encontradas para '{query_str}':*", parse_mode=ParseMode.MARKDOWN)
        for j in jobs[:3]:
            text = f"🎯 *{j.title}*\n🏢 `{j.company}` | 📍 `{j.location}` | Match: `{j.match_score}%`"
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 Ver Vaga", url=j.url)]])
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
            await asyncio.sleep(0.3)
            
    # Exibir até 3 promoções
    if deals:
        await update.message.reply_text(f"⚡ *Promoções encontradas para '{query_str}':*", parse_mode=ParseMode.MARKDOWN)
        for d in deals[:3]:
            text = f"📦 *{d.title}*\n🏷️ Preço: `{d.price}` | Loja: `{d.store}`"
            kb = InlineKeyboardMarkup([[InlineKeyboardButton("🛒 Ver Oferta", url=d.url)]])
            await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
            await asyncio.sleep(0.3)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Exibe estatísticas e status do radar."""
    query = update.callback_query
    msg_target = query.message if query else update.message
    chat_id = str(update.effective_chat.id)
    
    stats = await get_statistics()
    user_conf = await get_user_settings(chat_id)
    
    radar_emoji = "🟢 ATIVO" if user_conf.get("radar_active") == 1 else "🔴 PAUSADO"
    
    text = (
        f"📊 *PAINEL DE STATUS DO RADAR*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📡 *Status dos Alertas:* {radar_emoji}\n"
        f"💼 *Vagas Rastreadas Enviadas:* `{stats['total_jobs']}`\n"
        f"⚡ *Ofertas Tech Enviadas:* `{stats['total_deals']}`\n"
        f"👥 *Chats Ativos com Radar:* `{stats['active_users']}`\n\n"
        f"⏱️ *Intervalo de Varredura de Vagas:* `{CONFIG.jobs_check_interval} min`\n"
        f"⏱️ *Intervalo de Varredura de Ofertas:* `{CONFIG.deals_check_interval} min`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔔 Ligar Radar", callback_data="btn_radar_on"),
            InlineKeyboardButton("🔕 Pausar Radar", callback_data="btn_radar_off")
        ],
        [InlineKeyboardButton("🔙 Menu Principal", callback_data="btn_menu")]
    ])
    
    if query:
        await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=kb)

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gerenciador central de cliques em botões inline."""
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = str(update.effective_chat.id)
    
    if data == "btn_vagas":
        await vagas_command(update, context)
    elif data == "btn_promos":
        await promocoes_command(update, context)
    elif data == "btn_perfil":
        await perfil_command(update, context)
    elif data == "btn_status":
        await status_command(update, context)
    elif data == "btn_radar_on":
        await toggle_radar_state(chat_id, True)
        await query.answer("🔔 Radar automático ATIVADO com sucesso!", show_alert=True)
        await status_command(update, context)
    elif data == "btn_radar_off":
        await toggle_radar_state(chat_id, False)
        await query.answer("🔕 Radar automático PAUSADO!", show_alert=True)
        await status_command(update, context)
    elif data == "btn_menu":
        await start_command(update, context)

async def post_init(application) -> None:
    """Inicialização de banco e agendamento de tarefas em background."""
    await init_db()
    print("🚀 [Bot] Banco de dados SQLite inicializado!")
    
    scheduler = AsyncIOScheduler()
    # Varredura de vagas
    scheduler.add_job(
        check_jobs_task,
        "interval",
        minutes=CONFIG.jobs_check_interval,
        args=[application.bot],
        id="jobs_job",
        replace_existing=True
    )
    # Varredura de ofertas
    scheduler.add_job(
        check_deals_task,
        "interval",
        minutes=CONFIG.deals_check_interval,
        args=[application.bot],
        id="deals_job",
        replace_existing=True
    )
    scheduler.start()
    print(f"⏰ [Scheduler] Agendador ativo! Vagas a cada {CONFIG.jobs_check_interval}min | Promoções a cada {CONFIG.deals_check_interval}min")

def main():
    """Ponto de entrada do Bot."""
    token = CONFIG.telegram_token
    if not token:
        print("⚠️ [AVISO] TELEGRAM_BOT_TOKEN não foi configurado nas variáveis de ambiente.")
        print("👉 Crie seu bot no @BotFather no Telegram e adicione o token no arquivo .env ou execute:")
        print("   export TELEGRAM_BOT_TOKEN=\"seu_token_aqui\"")
        print("   python3 bot.py")
        sys.exit(1)
        
    app = ApplicationBuilder().token(token).post_init(post_init).build()
    
    # Handlers de comando
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("vagas", vagas_command))
    app.add_handler(CommandHandler("promocoes", promocoes_command))
    app.add_handler(CommandHandler("perfil", perfil_command))
    app.add_handler(CommandHandler("buscar", buscar_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("radar_on", lambda u, c: toggle_radar_state(str(u.effective_chat.id), True)))
    app.add_handler(CommandHandler("radar_off", lambda u, c: toggle_radar_state(str(u.effective_chat.id), False)))
    
    # Handler de botões inline
    app.add_handler(CallbackQueryHandler(button_callback_handler))
    
    print("🤖 [Radar Bot] Bot iniciado com sucesso! Escutando mensagens...")
    app.run_polling()

if __name__ == "__main__":
    main()
