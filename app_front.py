from datetime import date

import pandas as pd
import requests
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Imunotec - Gestão de Stock", page_icon="🧪", layout="wide"
)

st.title("🧪 Imunotec Laboratório - Gestão de Stock")
st.write(
    "Painel visual para controlo de reagentes, lotes e validades em tempo real."
)

# URL base da sua API no Render (sem barra no fim)
API_URL = "https://imunotec-api-2.onrender.com"

def extrair_erro_api(resposta):
    try:
        payload = resposta.json()
    except ValueError:
        return resposta.text or "Erro desconhecido"
    if isinstance(payload, dict):
        return payload.get("detail", payload)
    return payload


# --- MENU LATERAL PARA ADICIONAR REAGENTES ---
st.sidebar.header("➕ Registar Novo Lote")

with st.sidebar.form("form_lote"):
    nome_reagente = st.text_input("Nome do Reagente").strip()
    numero_lote = st.text_input("Número do Lote").strip()
    fabricante = st.text_input("Fabricante").strip()
    quantidade_atual = st.number_input(
        "Quantidade Atual", min_value=0.0, format="%.2f"
    )
    unidade_medida = st.selectbox(
        "Unidade de Medida", ["mL", "g", "L", "Unidades", "Frascos"]
    )
    data_validade = st.date_input("Data de Validade", value=date.today())
    temperatura_armazenamento = st.selectbox(
        "Temperatura", ["2°C a 8°C", "-20°C", "Temperatura Ambiente", "-80°C"]
    )

    botao_enviar = st.form_submit_button("Guardar Reagente")

    if botao_enviar:
        if nome_reagente and numero_lote:
            payload = {
                "nome_reagente": nome_reagente,
                "numero_lote": numero_lote,
                "fabricante": fabricante,
                "quantidade_atual": quantidade_atual,
                "unidade_medida": unidade_medida,
                "data_validade": str(data_validade),
                "temperatura_armazenamento": temperatura_armazenamento,
            }
            try:
                resposta = requests.post(f"{API_URL}/lotes/", json=payload, timeout=10)
                if resposta.status_code in (200, 201):
                    st.sidebar.success("Lote registado com sucesso!")
                    st.rerun()
                else:
                    st.sidebar.error(
                        f"Erro ao registar: {extrair_erro_api(resposta)}"
                    )
            except requests.RequestException:
                st.sidebar.error(
                    "Não foi possível ligar à API. Verifique a ligação."
                )
        else:
            st.sidebar.warning(
                "Preencha pelo menos o nome e o número do lote."
            )

# --- CORPO PRINCIPAL: LISTAGEM DO STOCK ---
st.subheader("📦 Stock Atual de Reagentes")

try:
    response = requests.get(f"{API_URL}/lotes/", timeout=10)
    if response.status_code == 200:
        dados = response.json()
        if dados:
            df = pd.DataFrame(dados)
            # Reorganizar colunas para melhor visualização
            colunas_exibicao = {
                "id": "ID",
                "nome_reagente": "Reagente",
                "numero_lote": "Lote",
                "fabricante": "Fabricante",
                "quantidade_atual": "Qtd",
                "unidade_medida": "Unidade",
                "data_validade": "Validade",
                "temperatura_armazenamento": "Armazenamento",
            }
            df = df.rename(columns=colunas_exibicao)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Ainda não existem reagentes registados no stock.")
    else:
        st.error(f"Erro ao carregar os dados da API: {extrair_erro_api(response)}")
except requests.RequestException:
    st.warning(
        "⚠️ Certifique-se de que o servidor FastAPI está a correr (`python -m"
        " uvicorn main:app --reload`)."
    )