import httpx
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Optional
import xml.etree.ElementTree as ET
import urllib.parse
from matchmaker import calculate_job_match

@dataclass
class JobOffer:
    title: str
    company: str
    location: str
    url: str
    salary: str
    source: str
    description: str
    match_score: float
    matched_skills: List[str]
    badge: str

async def fetch_github_community_jobs(keywords: List[str] = ["estagio", "junior", "php", "python", "node", "react"]) -> List[JobOffer]:
    """Busca vagas recentes nos repositórios comunitários do GitHub (backend-br/vagas, frontendbr/vagas)."""
    jobs = []
    repos = [
        ("backend-br/vagas", "Backend-BR"),
        ("frontendbr/vagas", "Frontend-BR"),
        ("react-brasil/vagas", "React-Brasil"),
        ("phpdevbr/vagas", "PHP-Brasil")
    ]
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
        for repo, source_name in repos:
            try:
                api_url = f"https://api.github.com/repos/{repo}/issues?state=open&per_page=15"
                resp = await client.get(api_url)
                if resp.status_code == 200:
                    issues = resp.json()
                    for issue in issues:
                        title = issue.get("title", "")
                        body = issue.get("body", "") or ""
                        url = issue.get("html_url", "")
                        labels = [l.get("name", "") for l in issue.get("labels", [])]
                        
                        # Extrai localização dos labels ou título
                        location = "Remoto / Brasil"
                        for lbl in labels:
                            if any(x in lbl.lower() for x in ["remoto", "híbrido", "curitiba", "paraná", "pr", "presencial"]):
                                location = lbl
                                break
                                
                        # Extrai empresa
                        company = source_name
                        if "[" in title and "]" in title:
                            parts = title.split("]")
                            if len(parts) > 1:
                                company = parts[0].replace("[", "").strip()
                                
                        score, skills, badge = calculate_job_match(title, body + " " + " ".join(labels), location)
                        
                        if score >= 35.0: # Apenas vagas relevantes
                            jobs.append(JobOffer(
                                title=title,
                                company=company,
                                location=location,
                                url=url,
                                salary="A Combinar / Na Vaga",
                                source=f"GitHub ({source_name})",
                                description=body[:300] + "..." if len(body) > 300 else body,
                                match_score=score,
                                matched_skills=skills,
                                badge=badge
                            ))
            except Exception as e:
                print(f"Erro ao buscar vagas do GitHub {repo}: {e}")
                
    return jobs

async def fetch_programathor_jobs() -> List[JobOffer]:
    """Busca vagas recentes no Programathor via RSS / Web."""
    jobs = []
    url = "https://programathor.com.br/jobs"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=headers, follow_redirects=True) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                job_cards = soup.find_all("div", class_="cell-list")
                
                for card in job_cards[:15]:
                    title_elem = card.find("h3")
                    if not title_elem:
                        continue
                    title = title_elem.get_text(strip=True)
                    
                    link_elem = card.find("a")
                    link = "https://programathor.com.br" + link_elem["href"] if link_elem and link_elem.get("href") else url
                    
                    company_elem = card.find("span", class_="cell-list-content-partner")
                    company = company_elem.get_text(strip=True) if company_elem else "Empresa Confidencial"
                    
                    details = card.find_all("span", class_="cell-list-content-info")
                    detail_text = " ".join([d.get_text(strip=True) for d in details])
                    
                    location = "Brasil / Remoto"
                    if "Remoto" in detail_text:
                        location = "100% Remoto"
                    elif "Curitiba" in detail_text or "PR" in detail_text:
                        location = "Curitiba, PR"
                        
                    score, skills, badge = calculate_job_match(title, detail_text, location)
                    
                    jobs.append(JobOffer(
                        title=title,
                        company=company,
                        location=location,
                        url=link,
                        salary="Ver no site",
                        source="Programathor",
                        description=detail_text,
                        match_score=score,
                        matched_skills=skills,
                        badge=badge
                    ))
    except Exception as e:
        print(f"Erro ao buscar Programathor: {e}")
        
    return jobs

async def fetch_remotar_jobs() -> List[JobOffer]:
    """Busca vagas remotas de estágio e júnior."""
    jobs = []
    # Remotar feed / RSS
    url = "https://remotar.com.br/feed"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                root = ET.fromstring(resp.text)
                for item in root.findall("./channel/item")[:15]:
                    title = item.find("title").text if item.find("title") is not None else ""
                    link = item.find("link").text if item.find("link") is not None else ""
                    desc = item.find("description").text if item.find("description") is not None else ""
                    
                    score, skills, badge = calculate_job_match(title, desc, "Remoto")
                    
                    if score >= 35.0:
                        jobs.append(JobOffer(
                            title=title,
                            company="Remotar Vagas",
                            location="100% Remoto",
                            url=link,
                            salary="A Combinar",
                            source="Remotar",
                            description=desc[:250] + "...",
                            match_score=score,
                            matched_skills=skills,
                            badge=badge
                        ))
    except Exception as e:
        # Fallback silencioso
        pass
        
    return jobs

async def get_all_jobs(custom_query: str = "") -> List[JobOffer]:
    """Agrega e ordena todas as vagas por score de afinidade com o perfil do Vitor."""
    all_jobs: List[JobOffer] = []
    
    github_jobs = await fetch_github_community_jobs()
    prog_jobs = await fetch_programathor_jobs()
    remotar_jobs = await fetch_remotar_jobs()
    
    all_jobs.extend(github_jobs)
    all_jobs.extend(prog_jobs)
    all_jobs.extend(remotar_jobs)
    
    if custom_query:
        query_lower = custom_query.lower()
        all_jobs = [j for j in all_jobs if query_lower in j.title.lower() or query_lower in j.description.lower() or query_lower in j.company.lower()]
        
    # Ordenar por maior score de compatibilidade primeiro
    all_jobs.sort(key=lambda x: x.match_score, reverse=True)
    
    # Remover duplicatas por URL
    seen_urls = set()
    unique_jobs = []
    for job in all_jobs:
        if job.url not in seen_urls:
            seen_urls.add(job.url)
            unique_jobs.append(job)
            
    return unique_jobs
