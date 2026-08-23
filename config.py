import os
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class UserProfile:
    name: str = "Matheus Vitor Lourenço Schionato"
    title: str = "Desenvolvedor Fullstack & Infraestrutura de TI"
    location: str = "São José dos Pinhais, PR / Curitiba, PR"
    email: str = "matheus.schionato17@gmail.com"
    phone: str = "(41) 99666-4983"
    linkedin_url: str = "https://www.linkedin.com/in/matheus-vitor-louren%C3%A7o-schionato-9a254a223/"
    github_url: str = "https://github.com/MvitorLS"
    education: str = "Bacharelado em Ciência da Computação — IFPR (Previsão: 2029)"
    
    # Skills principais para matchmaking
    core_skills: List[str] = field(default_factory=lambda: [
        "python", "php", "javascript", "typescript", "node.js", "node", "react", "react native",
        "docker", "docker compose", "linux", "bash", "shell", "git", "github",
        "sql", "mysql", "postgresql", "postgres", "sqlite", "sequelize",
        "rest api", "api", "graphql", "devops", "prometheus", "grafana", "snmp", "nginx",
        "pytest", "testes", "qa", "ci/cd", "html5", "css3", "tailwind"
    ])
    
    # Níveis prioritários
    target_levels: List[str] = field(default_factory=lambda: [
        "estágio", "estagio", "estagiário", "estagiaria", "junior", "júnior", "trainee", "iniciante", "assistente"
    ])

@dataclass
class BotConfig:
    # Telegram Tokens
    telegram_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    admin_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")
    
    # Intervalos de busca (em minutos)
    jobs_check_interval: int = int(os.getenv("JOBS_CHECK_INTERVAL", "60"))
    deals_check_interval: int = int(os.getenv("DEALS_CHECK_INTERVAL", "30"))
    
    # Banco de Dados SQLite
    db_path: str = os.getenv("DATABASE_PATH", "radar_bot.db")
    
    # Filtros de Promoções de Eletrônicos
    deals_keywords: List[str] = field(default_factory=lambda: [
        "poco", "xiaomi", "redmi", "smartphone", "celular", "galaxy", "iphone",
        "ssd", "nvme", "ram", "memória", "ddr4", "ddr5", "placa de vídeo", "gpu",
        "rtx", "gtx", "radeon", "rx", "ryzen", "intel", "core i5", "core i7",
        "monitor", "144hz", "165hz", "240hz", "ips", "teclado mecânico", "mouse",
        "headset", "fone", "notebook", "laptop", "cadeira gamer", "fonte", "gabinete"
    ])

PROFILE = UserProfile()
CONFIG = BotConfig()
