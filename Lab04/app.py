"""Dashboard do Lab04 — testes de hipótese por dentro (par P4).

Execução, a partir da pasta Lab04: ``streamlit run app.py``
"""

import streamlit as st

from hipotese.config import URL_DASHBOARD, URL_PROJECT, URL_REPOSITORIO

# Seções na ordem exigida pelo roteiro, com a issue que preenche cada uma.
SECOES = [
    ("1. Cenário", "#264"),
    ("2. Os dados", "#267"),
    ("3. Como os testes funcionam", "#268"),
    ("4. Erro tipo I", "#273"),
    ("5. Poder", "#274"),
    ("6. Dados reais", "#275"),
    ("7. Conclusão", "#276"),
]

st.set_page_config(page_title="Lab04 — Testes de hipótese", layout="wide")

st.title("Testes de hipótese por dentro: Z para proporção × binomial exato")
link_dashboard = f"[Dashboard publicado]({URL_DASHBOARD})" if URL_DASHBOARD else "Dashboard publicado: em breve (#277)"
st.markdown(
    f"[Repositório]({URL_REPOSITORIO}) · [GitHub Projects]({URL_PROJECT}) · {link_dashboard}"
)

for titulo, issue in SECOES:
    st.header(titulo)
    st.info(f"Conteúdo em construção ({issue}).")
