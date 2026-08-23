import httpx
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional
import re
from config import CONFIG

@dataclass
class TechDeal:
    title: str
    price: str
    original_price: str
    discount: str
    store: str
    coupon: str
    url: str
    image_url: str
    source: str
    category: str

async def fetch_gatry_deals() -> List[TechDeal]:
    """Scraper robusto do Gatry para ofertas de tecnologia e eletrônicos."""
    deals = []
    urls = [
        "https://gatry.com/",
        "https://gatry.com/promocoes/informatica-e-tecnologia"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
        for url in urls:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    articles = soup.find_all("article")
                    
                    for art in articles:
                        # 1. Título e Link
                        h3 = art.find("h3")
                        if not h3:
                            continue
                        link_tag = h3.find("a")
                        title = link_tag.get_text(strip=True) if link_tag else h3.get_text(strip=True)
                        link = link_tag["href"] if link_tag and link_tag.get("href") else ""
                        
                        # 2. Preço
                        price_tag = art.find("p", class_="price")
                        price = price_tag.get_text(strip=True) if price_tag else "Consulte"
                        
                        # 3. Loja
                        store_tag = art.find("div", class_="option-store")
                        store = "Loja Online"
                        if store_tag:
                            store_text = store_tag.get_text(strip=True).replace("Ir para", "").strip()
                            if store_text:
                                store = store_text
                                
                        # 4. Imagem
                        img_tag = art.find("div", class_="image")
                        img_url = ""
                        if img_tag:
                            img = img_tag.find("img")
                            if img and img.get("src"):
                                img_url = img["src"]
                                
                        # 5. Cupom (se mencionado no título ou comentário)
                        comment_tag = art.find("p", class_="comment")
                        comment = comment_tag.get_text(strip=True) if comment_tag else ""
                        coupon = ""
                        coupon_match = re.search(r'cupom[:\s]+([A-Z0-9\-_]+)', f"{title} {comment}", re.IGNORECASE)
                        if coupon_match:
                            coupon = coupon_match.group(1).upper()
                            
                        # Categoria / Detecção de Tech
                        is_tech = any(k in f"{title} {comment}".lower() for k in CONFIG.deals_keywords) or any(x in title.lower() for x in ["monitor", "pc", "gamer", "ssd", "ram", "mouse", "teclado", "fone", "xiaomi", "poco", "intel", "amd", "ryzen", "notebook", "tv", "smart"])
                        
                        if is_tech or "r$" in price.lower():
                            deals.append(TechDeal(
                                title=title,
                                price=price,
                                original_price="",
                                discount="⚡ PROMOÇÃO",
                                store=store,
                                coupon=coupon,
                                url=link,
                                image_url=img_url,
                                source="Gatry",
                                category="Eletrônicos & Informática"
                            ))
            except Exception as e:
                print(f"Erro ao buscar Gatry {url}: {e}")
                
    return deals

async def get_all_deals(custom_query: str = "") -> List[TechDeal]:
    """Agrega e filtra promoções de tecnologia."""
    all_deals = await fetch_gatry_deals()
    
    if custom_query:
        query_lower = custom_query.lower()
        all_deals = [d for d in all_deals if query_lower in d.title.lower() or query_lower in d.store.lower()]
        
    # Remover duplicatas por URL / Título
    seen = set()
    unique_deals = []
    for d in all_deals:
        key = d.title.strip().lower()
        if key not in seen and d.url:
            seen.add(key)
            unique_deals.append(d)
            
    return unique_deals
