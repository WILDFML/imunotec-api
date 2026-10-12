import base64
import mimetypes
import os
import posixpath
import re
from pathlib import Path
from datetime import date
from urllib.parse import quote, unquote, urlsplit

import pandas as pd
import requests
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Imunotec - Gestão de Estoque", page_icon="🧪", layout="wide"
)

# URL base da sua API no Render (sem barra no fim)
API_URL = "https://imunotec-api-2.onrender.com"
LOGO_PATH = Path(__file__).parent / "Logo lab.jpeg"

def extrair_erro_api(resposta):
    try:
        payload = resposta.json()
    except ValueError:
        return resposta.text or "Erro desconhecido"
    if isinstance(payload, dict):
        return payload.get("detail", payload)
    return payload


def obter_cabecalho_auth():
    return {"Authorization": f"Bearer {st.session_state['access_token']}"}


def validar_sessao(resposta):
    if resposta.status_code == 401:
        st.session_state.pop("access_token", None)
        st.warning("A sessão expirou ou é inválida. Entre novamente.")
        st.stop()


def configuracao_caderno():
    def obter_segredo(nome):
        valor = os.getenv(nome)
        if valor:
            return valor
        try:
            return st.secrets[nome]
        except (KeyError, st.errors.StreamlitSecretNotFoundError):
            return ""

    return {
        "repository": obter_segredo("MEETINGS_REPOSITORY"),
        "token": obter_segredo("MEETINGS_GITHUB_TOKEN"),
    }


def incorporar_imagens(html, repository, headers):
    padrao_imagem = re.compile(
        r'(<img\b[^>]*?\bsrc\s*=\s*)(["\'])(.*?)\2',
        flags=re.IGNORECASE | re.DOTALL,
    )

    def incorporar(match):
        origem = match.group(3)
        url = urlsplit(origem)
        if url.scheme or url.netloc or url.path.startswith("/"):
            return match.group(0)

        caminho_imagem = posixpath.normpath(
            posixpath.join("atas", unquote(url.path))
        )
        if not caminho_imagem.startswith("atas/"):
            raise ValueError(f"Caminho de imagem inválido na ata: {origem}")

        tipo_mime, _ = mimetypes.guess_type(caminho_imagem)
        if not tipo_mime or not tipo_mime.startswith("image/"):
            raise ValueError(f"Formato de imagem não reconhecido: {origem}")

        url_api = (
            f"https://api.github.com/repos/{repository}/contents/"
            f"{quote(caminho_imagem, safe='/')}"
        )
        resposta = requests.get(
            url_api,
            headers={
                **headers,
                "Accept": "application/vnd.github.raw+json",
            },
            timeout=20,
        )
        resposta.raise_for_status()
        imagem_codificada = base64.b64encode(resposta.content).decode("ascii")
        origem_embutida = f"data:{tipo_mime};base64,{imagem_codificada}"
        return (
            f"{match.group(1)}{match.group(2)}{origem_embutida}"
            f"{match.group(2)}"
        )

    return padrao_imagem.sub(incorporar, html)


def carregar_reunioes(repository, token):
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    api_url = f"https://api.github.com/repos/{repository}/contents/atas"
    resposta = requests.get(api_url, headers=headers, timeout=20)
    resposta.raise_for_status()

    arquivos = [
        item
        for item in resposta.json()
        if item.get("type") == "file"
        and item.get("name", "").lower().endswith(".html")
        and not item.get("name", "").startswith("_")
    ]
    reunioes = []
    for arquivo in sorted(arquivos, key=lambda item: item["name"], reverse=True):
        conteudo_resposta = requests.get(
            arquivo["url"], headers=headers, timeout=20
        )
        conteudo_resposta.raise_for_status()
        payload = conteudo_resposta.json()
        conteudo_codificado = payload.get("content")
        if payload.get("encoding") != "base64" or not isinstance(
            conteudo_codificado, str
        ):
            raise ValueError(
                f"O GitHub não retornou o conteúdo Base64 esperado para "
                f"{arquivo['name']}."
            )
        try:
            conteudo_codificado = "".join(conteudo_codificado.split())
            html = base64.b64decode(conteudo_codificado, validate=True).decode(
                "utf-8"
            )
        except (UnicodeDecodeError, ValueError) as erro:
            raise ValueError(
                f"Não foi possível decodificar o arquivo {arquivo['name']}."
            ) from erro
        html = incorporar_imagens(html, repository, headers)
        reunioes.append((arquivo["name"], html))
    return reunioes


if "access_token" not in st.session_state:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(ellipse at 12% 10%, #e4f5ef 0, transparent 38%),
                #f5f8f7;
        }
        div[data-testid="stMainBlockContainer"] {
            max-width: 1080px;
            padding-top: 4rem;
            padding-bottom: 3rem;
        }
        div[data-testid="stForm"] {
            padding: 1.6rem;
            background: #ffffff;
            border: 1px solid #e2eae7;
            border-radius: 16px;
            box-shadow: 0 16px 45px rgba(25, 65, 52, 0.08);
        }
        div[data-testid="stForm"] button[kind="primaryFormSubmit"] {
            min-height: 2.8rem;
            border-radius: 9px;
            background: #087f68;
            border-color: #087f68;
        }
        div[data-testid="stForm"] button[kind="primaryFormSubmit"]:hover {
            background: #066b58;
            border-color: #066b58;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: #087f68;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: #087f68;
        }
        .login-panel {
            padding: 1.5rem 1.6rem;
            color: #f4fffb;
            background: linear-gradient(145deg, #075c50, #0c8a70);
            border-radius: 18px;
            box-shadow: 0 20px 50px rgba(18, 92, 74, 0.18);
        }
        .login-panel p {
            margin: 0;
            color: #ddf5ec;
            font-size: 1.02rem;
            line-height: 1.65;
        }
        .login-note {
            margin-top: 2.4rem;
            padding-top: 1.1rem;
            border-top: 1px solid rgba(255, 255, 255, 0.22);
            color: #d2eee5;
            font-size: 0.86rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    branding, access = st.columns([1.05, 0.95], gap="large")
    with branding:
        logo_columns = st.columns([1, 5, 1])
        with logo_columns[1]:
            st.image(str(LOGO_PATH), width=320)
        st.markdown(
            """
            <section class="login-panel">
                <p>Gestão de recursos para cuidar das atividades do laboratório com eficiência.</p>
                <div class="login-note">Reagentes, lotes e validades em um só lugar.</div>
            </section>
            """,
            unsafe_allow_html=True,
        )

    with access:
        st.subheader("Acesso ao laboratório")
        st.caption("Entre na sua conta ou crie um novo acesso autorizado.")
        login_tab, register_tab = st.tabs(["Entrar", "Criar conta"])

        with login_tab:
            with st.form("form_login"):
                email = st.text_input("E-mail", placeholder="nome@laboratorio.org")
                password = st.text_input("Palavra-passe", type="password")
                entrar = st.form_submit_button(
                    "Entrar no sistema", type="primary", use_container_width=True
                )

            if entrar:
                try:
                    resposta = requests.post(
                        f"{API_URL}/token",
                        data={"username": email, "password": password},
                        timeout=60,
                    )
                    if resposta.status_code == 200:
                        st.session_state["access_token"] = resposta.json()["access_token"]
                        st.rerun()
                    else:
                        st.error(
                            f"Não foi possível iniciar sessão: {extrair_erro_api(resposta)}"
                        )
                except requests.RequestException:
                    st.error("Não foi possível ligar à API. Verifique a ligação.")

        with register_tab:
            with st.form("form_registo"):
                email = st.text_input("E-mail", placeholder="nome@laboratorio.org")
                password = st.text_input(
                    "Palavra-passe (mínimo 8 caracteres)", type="password"
                )
                registration_key = st.text_input(
                    "Chave de criação fornecida pelo administrador",
                    type="password",
                )
                criar_conta = st.form_submit_button(
                    "Criar conta", type="primary", use_container_width=True
                )

            if criar_conta:
                try:
                    resposta = requests.post(
                        f"{API_URL}/register",
                        json={"email": email, "password": password},
                        headers={"X-Registration-Key": registration_key},
                        timeout=60,
                    )
                    if resposta.status_code == 201:
                        st.success("Conta criada. Agora pode iniciar sessão.")
                    else:
                        st.error(
                            f"Não foi possível criar a conta: {extrair_erro_api(resposta)}"
                        )
                except requests.RequestException:
                    st.error("Não foi possível ligar à API. Verifique a ligação.")

    st.stop()

with st.sidebar:
    if st.button("Terminar sessão"):
        st.session_state.pop("access_token", None)
        st.rerun()

    def selecionar_secao(secao):
        st.session_state["secao"] = secao

    secao = st.radio(
        "Navegação",
        ["Início", "Caderno de reuniões", "Estoque"],
        key="secao",
    )

if secao == "Início":
    st.title("Imunotec | Espaço do laboratório")
    st.write(
        "Um espaço compartilhado para organizar recursos, registrar reuniões "
        "e apoiar as atividades do laboratório."
    )
    estoque_col, reunioes_col = st.columns(2)
    with estoque_col:
        with st.container(border=True):
            st.subheader("📦 Estoque")
            st.write("Consulte reagentes, lotes, quantidades e validades.")
            st.button(
                "Abrir estoque",
                on_click=selecionar_secao,
                args=("Estoque",),
                use_container_width=True,
            )
    with reunioes_col:
        with st.container(border=True):
            st.subheader("📝 Caderno de reuniões")
            st.write("Acesse atas e registros internos publicados em Quarto.")
            st.button(
                "Abrir caderno",
                on_click=selecionar_secao,
                args=("Caderno de reuniões",),
                use_container_width=True,
            )
    st.stop()

if secao == "Caderno de reuniões":
    st.title("📝 Caderno de reuniões")
    st.caption("Registros internos do laboratório, publicados em Quarto.")
    configuracao = configuracao_caderno()
    if not configuracao["repository"] or not configuracao["token"]:
        st.info(
            "O caderno ainda não está conectado. O administrador precisa "
            "configurar o repositório privado e o token de leitura do GitHub."
        )
        st.stop()

    try:
        reunioes = carregar_reunioes(
            configuracao["repository"], configuracao["token"]
        )
    except requests.RequestException as erro:
        st.error(f"Não foi possível carregar o caderno do GitHub: {erro}")
        st.stop()
    except ValueError as erro:
        st.error(str(erro))
        st.stop()

    if not reunioes:
        st.info("Ainda não há reuniões publicadas no caderno.")
    else:
        reunioes_formatadas = []
        for nome_arquivo, html in reunioes:
            nome = Path(nome_arquivo).stem
            data_reuniao = None
            try:
                data_reuniao = date.fromisoformat(nome[:10])
            except ValueError:
                pass

            titulo = nome[11:] if data_reuniao else nome
            titulo = titulo.replace("-", " ").replace("_", " ").title()
            reunioes_formatadas.append(
                (nome_arquivo, html, titulo, data_reuniao)
            )

        reuniao_aberta = st.session_state.get("reuniao_aberta")
        reuniao_selecionada = next(
            (
                reuniao
                for reuniao in reunioes_formatadas
                if reuniao[0] == reuniao_aberta
            ),
            None,
        )
        if reuniao_selecionada:
            if st.button("← Voltar às reuniões"):
                st.session_state.pop("reuniao_aberta", None)
                st.rerun()
            _, html, titulo, data_reuniao = reuniao_selecionada
            st.subheader(titulo)
            if data_reuniao:
                st.caption(data_reuniao.strftime("%d/%m/%Y"))
            st.html(html)
        else:
            st.session_state.pop("reuniao_aberta", None)
            for inicio in range(0, len(reunioes_formatadas), 2):
                colunas = st.columns(2)
                for coluna, reuniao in zip(
                    colunas, reunioes_formatadas[inicio : inicio + 2]
                ):
                    nome_arquivo, _, titulo, data_reuniao = reuniao
                    with coluna:
                        with st.container(border=True):
                            st.caption(
                                data_reuniao.strftime("%d/%m/%Y")
                                if data_reuniao
                                else "Registro do laboratório"
                            )
                            st.subheader(titulo)
                            st.write("Registro da reunião em formato Quarto.")
                            if st.button(
                                "Ler ata",
                                key=f"abrir_reuniao_{nome_arquivo}",
                                use_container_width=True,
                            ):
                                st.session_state["reuniao_aberta"] = nome_arquivo
                                st.rerun()
    st.stop()

st.title("📦 Gestão de estoque")
st.write("Controle de reagentes, lotes e validades do laboratório.")

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
                resposta = requests.post(
                    f"{API_URL}/lotes/",
                    json=payload,
                    headers=obter_cabecalho_auth(),
                    timeout=10,
                )
                validar_sessao(resposta)
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
# --- MENU LATERAL PARA REABASTECER LOTE EXISTENTE ---
st.sidebar.markdown("---")
st.sidebar.header("➕ Reabastecer Lote Existente")

with st.sidebar.form("form_reabastecer"):
    lote_id_reabastecer = st.number_input(
        "ID do Lote a Atualizar", min_value=1, step=1, format="%d", key="id_reab"
    )
    quantidade_adicional = st.number_input(
        "Quantidade a Adicionar", min_value=0.1, format="%.2f", key="qtd_add"
    )
    botao_reabastecer = st.form_submit_button("Adicionar ao Stock")

    if botao_reabastecer:
        try:
            # Enviamos a quantidade extra como parâmetro na query (params)
            params = {"quantidade_extra": quantidade_adicional}
            resposta = requests.patch(
                f"{API_URL}/lotes/{lote_id_reabastecer}/adicionar",
                params=params,
                headers=obter_cabecalho_auth(),
                timeout=30,
            )
            validar_sessao(resposta)
            if resposta.status_code == 200:
                st.sidebar.success(
                    f"Stock atualizado com sucesso!"
                )
                st.rerun()
            else:
                st.sidebar.error(
                    f"Erro ao reabastecer: {extrair_erro_api(resposta)}"
                )
        except requests.RequestException:
            st.sidebar.error("Não foi possível ligar à API.")
            
# --- MENU LATERAL PARA ELIMINAR LOTES ---
st.sidebar.markdown("---")
st.sidebar.header("🗑️ Eliminar / Dar Baixa em Lote")

with st.sidebar.form("form_eliminar"):
    lote_id_para_apagar = st.number_input(
        "ID do Lote a Eliminar", min_value=1, step=1, format="%d"
    )
    botao_apagar = st.form_submit_button("Eliminar Lote")

    if botao_apagar:
        try:
            resposta = requests.delete(
                f"{API_URL}/lotes/{lote_id_para_apagar}",
                headers=obter_cabecalho_auth(),
                timeout=10,
            )
            validar_sessao(resposta)
            if resposta.status_code == 200:
                st.sidebar.success(
                    f"Lote ID {lote_id_para_apagar} eliminado com sucesso!"
                )
                st.rerun()
            else:
                st.sidebar.error(
                    f"Erro ao eliminar: {extrair_erro_api(resposta)}"
                )
        except requests.RequestException:
            st.sidebar.error("Não foi possível ligar à API.")

# --- CORPO PRINCIPAL: LISTAGEM E PESQUISA DE STOCK ---
st.subheader("📦 Stock Atual de Reagentes")

try:
    response = requests.get(
        f"{API_URL}/lotes/",
        headers=obter_cabecalho_auth(),
        timeout=30,
    )
    validar_sessao(response)
    if response.status_code == 200:
        dados = response.json()
        if dados:
            df = pd.DataFrame(dados)
            
            # --- BARRA DE PESQUISA RÁPIDA ---
            pesquisa = st.text_input("🔍 Pesquisar por reagente ou fabricante...").strip()
            if pesquisa:
                df = df[
                    df["nome_reagente"].str.contains(pesquisa, case=False, na=False) |
                    df["fabricante"].str.contains(pesquisa, case=False, na=False)
                ]

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
            
            # Mostrar a tabela interativa
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Ainda não existem reagentes registados no stock.")
    else:
        st.error(f"Erro ao carregar os dados da API: {extrair_erro_api(response)}")
except requests.RequestException:
    st.warning("⚠️ Não foi possível ligar à API para carregar o stock.")