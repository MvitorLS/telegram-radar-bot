import asyncio
from scrapers.jobs_scraper import get_all_jobs
from scrapers.deals_scraper import get_all_deals
from config import PROFILE

async def main():
    print("==================================================")
    print("🚀 RADAR BOT — TESTE DE TERMINAL (SEM TELEGRAM) 🚀")
    print(f"👤 Candidato: {PROFILE.name}")
    print(f"🎓 Formação: {PROFILE.education}")
    print("==================================================")
    
    print("\n[1/2] 🔍 Buscando vagas e calculando Match Score...")
    jobs = await get_all_jobs()
    print(f"✅ Total de vagas agregadas: {len(jobs)}")
    print("\n--- TOP 5 VAGAS COM MAIOR AFINIDADE ---")
    for i, j in enumerate(jobs[:5], 1):
        print(f"\n{i}. [{j.badge} | Match: {j.match_score}%]")
        print(f"   💼 {j.title}")
        print(f"   🏢 Empresa: {j.company} | 📍 Local: {j.location}")
        print(f"   🛠️ Skills: {', '.join(j.matched_skills)}")
        print(f"   🔗 Link: {j.url}")
        
    print("\n" + "="*50)
    print("[2/2] ⚡ Buscando promoções de eletrônicos e tech...")
    deals = await get_all_deals()
    print(f"✅ Total de ofertas encontradas: {len(deals)}")
    print("\n--- TOP 5 PROMOÇÕES DO DIA ---")
    for i, d in enumerate(deals[:5], 1):
        print(f"\n{i}. [{d.store}] {d.title}")
        print(f"   🏷️ Preço: {d.price} | Cupom: {d.coupon or 'Sem cupom'}")
        print(f"   🛒 Link: {d.url}")
        
    print("\n==================================================")
    print("✨ Teste concluído com sucesso!")

if __name__ == "__main__":
    asyncio.run(main())
