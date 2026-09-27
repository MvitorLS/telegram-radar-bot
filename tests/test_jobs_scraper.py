import httpx

from scrapers import jobs_scraper

ISSUES = [
    {
        "title": "[Acme] Estágio Backend Python - Remoto",
        "body": "Buscamos estagiário com Python, Docker e SQL.",
        "html_url": "https://github.com/backend-br/vagas/issues/1",
        "labels": [{"name": "Remoto"}],
    },
    {
        "title": "[BigCo] Tech Lead Java",
        "body": "10 anos de experiência com Java.",
        "html_url": "https://github.com/backend-br/vagas/issues/2",
        "labels": [],
    },
]

REMOTAR = {
    "data": [
        {"id": 1, "title": "Desenvolvedor Júnior React", "description": "<p>React, TypeScript e <b>Node</b></p>",
         "company": {"name": "Acme"}},
        {"id": 2, "title": "Backend Sênior Go", "description": "<p>Go e Kubernetes</p>", "company": None},
    ]
}


async def test_github_extrai_empresa_local_e_filtra_irrelevantes(fake_http):
    fake_http["https://api.github.com/repos/backend-br/vagas"] = httpx.Response(200, json=ISSUES)

    jobs = await jobs_scraper.fetch_github_community_jobs()

    assert [j.company for j in jobs] == ["Acme"]
    assert jobs[0].location == "Remoto"
    assert jobs[0].source == "GitHub (Backend-BR)"


async def test_remotar_le_api_e_limpa_html(fake_http):
    fake_http["https://api.remotar.com.br/jobs"] = httpx.Response(200, json=REMOTAR)

    jobs = await jobs_scraper.get_all_jobs()  # dedup por URL: 3 termos de busca, 1 vaga

    assert [j.url for j in jobs] == ["https://remotar.com.br/job/1"]
    assert jobs[0].company == "Acme"
    assert "<" not in jobs[0].description


async def test_fonte_fora_do_ar_nao_derruba_agregacao(fake_http):
    fake_http["https://api.remotar.com.br/jobs"] = httpx.Response(200, json=REMOTAR)
    # GitHub e Programathor respondem 404

    jobs = await jobs_scraper.get_all_jobs()

    assert [j.source for j in jobs] == ["Remotar"]


async def test_busca_customizada_filtra_e_remove_duplicatas(fake_http):
    fake_http["https://api.github.com/repos/"] = httpx.Response(200, json=ISSUES)

    jobs = await jobs_scraper.get_all_jobs(custom_query="python")

    assert len(jobs) == 1  # a mesma issue aparece nos 4 repositórios, mas a URL é a mesma
