import re
from typing import Dict, Any, List, Tuple
from config import PROFILE

def calculate_job_match(title: str, description: str, location: str = "") -> Tuple[float, List[str], str]:
    """
    Calcula a compatibilidade (% de Match) de uma vaga com o currículo e perfil do Vitor.
    Retorna: (score_percentual, skills_encontradas, badge_status)
    """
    full_text = f"{title} {description} {location}".lower()
    
    score = 0.0
    matched_skills = []
    
    # 1. Checagem de Nível de Experiência (Estágio, Júnior, Trainee) - Peso: 35%
    is_target_level = False
    for level in PROFILE.target_levels:
        if level in full_text:
            is_target_level = True
            matched_skills.append(f"🎓 Nível: {level.capitalize()}")
            break
            
    if is_target_level:
        score += 35.0
    else:
        # Se for estágio/júnior sem menção explícita no texto, dá pontuação base moderada
        if "estágio" in title.lower() or "júnior" in title.lower() or "junior" in title.lower():
            score += 35.0
        else:
            score += 15.0 # vaga geral de tech
            
    # Vaga de nível acima do buscado: perde os pontos de nível e mais um pouco
    if not is_target_level and re.search(r'\b(s[êe]nior|sr\.?|pleno|pl|especialista|tech lead|staff)\b', title.lower()):
        score -= 30.0

    # 2. Checagem de Tecnologias do Perfil do Vitor - Peso: 45%
    # Destaques especiais
    priority_techs = {
        "php": "🐘 PHP",
        "python": "🐍 Python",
        "node": "🟢 Node.js",
        "node.js": "🟢 Node.js",
        "react": "⚛️ React",
        "react native": "📱 React Native",
        "typescript": "🟦 TypeScript",
        "javascript": "🟨 JavaScript",
        "docker": "🐳 Docker",
        "linux": "🐧 Linux",
        "sql": "🗄️ SQL",
        "postgres": "🐘 PostgreSQL",
        "postgresql": "🐘 PostgreSQL",
        "mysql": "🐬 MySQL",
        "sqlite": "📦 SQLite",
        "api": "🔌 REST API",
        "rest": "🔌 REST API",
        "graphql": "🕸️ GraphQL",
        "devops": "⚙️ DevOps",
        "qa": "🧪 QA / Testes",
        "testes": "🧪 Testes",
        "pytest": "🧪 Pytest",
        "git": "🐙 Git",
        "github": "🐙 GitHub"
    }
    
    tech_score = 0.0
    seen_techs = set()
    
    for tech_key, tech_label in priority_techs.items():
        # Busca exata por palavra para evitar falso positivo (ex: 'c' em 'casa')
        pattern = r'\b' + re.escape(tech_key) + r'\b'
        if re.search(pattern, full_text):
            if tech_label not in seen_techs:
                seen_techs.add(tech_label)
                matched_skills.append(tech_label)
                tech_score += 8.0
                
    score += min(tech_score, 45.0)
    
    # 3. Localização & Modalidade (Curitiba, PR, Remoto, Híbrido) - Peso: 20%
    location_keywords = ["curitiba", "são josé dos pinhais", "paraná", "pr", "remoto", "home office", "híbrido", "hibrido", "teletrabalho", "anywhere"]
    for loc in location_keywords:
        # Limite de palavra: "pr" não pode casar com "programador" ou "experiência"
        if re.search(r'\b' + re.escape(loc) + r'\b', full_text):
            matched_skills.append(f"📍 {loc.capitalize()}")
            score += 20.0
            break
            
    final_score = max(min(round(score, 1), 100.0), 0.0)
    
    # Badge de Classificação
    if final_score >= 80.0:
        badge = "🟢 ALTA AFINIDADE"
    elif final_score >= 60.0:
        badge = "🟡 BOA OPORTUNIDADE"
    elif final_score >= 40.0:
        badge = "⚪ INTERESSANTE"
    else:
        badge = "🔍 EXPLORATÓRIA"
        
    return final_score, matched_skills, badge
