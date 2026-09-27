from matchmaker import calculate_job_match


def test_estagio_com_stack_e_local_tem_alta_afinidade():
    score, skills, badge = calculate_job_match(
        "Estágio em Desenvolvimento", "Python, Docker, PostgreSQL e React", "Curitiba - PR"
    )
    assert score >= 80
    assert "🐍 Python" in skills and "🐳 Docker" in skills
    assert badge.endswith("ALTA AFINIDADE")


def test_vaga_senior_sem_stack_fica_exploratoria():
    score, _, badge = calculate_job_match("Engenheiro Sênior Java", "Spring, Kotlin", "São Paulo")
    assert score < 40
    assert badge.endswith("EXPLORATÓRIA")


def test_pr_nao_casa_dentro_de_outras_palavras():
    # "programador" e "experiência" contêm "pr", mas não são localização
    _, skills, _ = calculate_job_match("Programador", "Experiência com expressões regulares")
    assert not any(s.startswith("📍") for s in skills)


def test_pontos_de_tecnologia_tem_teto():
    texto = "php python node react typescript javascript docker linux sql postgres mysql graphql"
    score, _, _ = calculate_job_match("Vaga", texto)
    assert score <= 15 + 45  # nível genérico + teto de tecnologia


def test_skill_nao_conta_duas_vezes():
    _, skills, _ = calculate_job_match("Vaga", "node e node.js")
    assert skills.count("🟢 Node.js") == 1


def test_score_nunca_passa_de_100():
    score, _, _ = calculate_job_match("Estágio júnior", "python " * 50, "remoto curitiba")
    assert score <= 100


def test_vaga_senior_com_stack_certa_nao_passa_no_corte_de_aviso():
    score, _, _ = calculate_job_match("Desenvolvedor Python Sênior", "Python, Docker, SQL", "Remoto")
    assert score < 50


def test_score_nunca_fica_negativo():
    score, _, _ = calculate_job_match("Tech Lead", "")
    assert score >= 0
