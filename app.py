import streamlit as st
import requests
import base64
import json

# Configurações via variáveis de ambiente do Render (seguro)
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
username = st.secrets["username"]
password = st.secrets["password"]

auth_url = "https://api.gs1br.org/oauth/access-token"
product_url = "https://api.gs1br.org/gs1/v2/products"

padroes_malas = {
    'PP': {'peso': 2.5, 'altura': 51, 'largura': 32, 'profundidade': 23},
    'P':  {'peso': 3.0, 'altura': 55, 'largura': 35, 'profundidade': 25},
    'M':  {'peso': 5.0, 'altura': 64, 'largura': 41, 'profundidade': 27},
    'G':  {'peso': 6.0, 'altura': 74, 'largura': 48, 'profundidade': 30},
    'KBMOP': {'peso': 1.0, 'altura': 41, 'largura': 32, 'profundidade': 17},
    'KBMOU': {'peso': 1.0, 'altura': 45, 'largura': 30, 'profundidade': 23},
    'KBMOE': {'peso': 1.0, 'altura': 45, 'largura': 30, 'profundidade': 23},
    'KBSHPV': {'peso': 0.3, 'altura': 81, 'largura': 42, 'profundidade': 37},
    'KBSHG':  {'peso': 0.3, 'altura': 17, 'largura': 27, 'profundidade': 8},
    'KBSHR':  {'peso': 0.3, 'altura': 18, 'largura': 11, 'profundidade': 7},
    'NAOSEI': {'peso': 1.0, 'altura': 1,  'largura': 1,  'profundidade': 1}
}

def get_token():
    credentials = f"{client_id}:{client_secret}"
    basic_auth = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {basic_auth}",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/121"
    }
    payload = {
        "grant_type": "password",
        "username": username,
        "password": password
    }
    try:
        r = requests.post(auth_url, data=payload, headers=headers, timeout=20)
        r.raise_for_status()
        return r.json()["access_token"]
    except Exception as e:
        st.error("Erro ao pegar token")
        st.code(r.text)
        return None

def gerar_payload(nome, sku, marca, ncm, tamanho, imagem):
    p = padroes_malas.get(tamanho, padroes_malas["NAOSEI"])
    return { ... }  # (cole o payload completo que você já tem – igual ao anterior)

# ==================== INTERFACE =====================
st.set_page_config(page_title="GTIN GS1BR – WBS", layout="centered")
st.title("Cadastrador de GTIN – GS1 Brasil")
st.markdown("### Malas & Bolsas • Funcionando 24h no Render")

with st.form("form"):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome do Produto *")
        sku = st.text_input("SKU *")
        marca = st.text_input("Marca *", "WBS")
    with col2:
        ncm = st.text_input("NCM *", "4202.12.10")
        tamanho = st.selectbox("Tamanho *", list(padroes_malas.keys()))
        imagem = st.text_input("URL da Imagem *")

    if st.form_submit_button("GERAR GTIN", type="primary", use_container_width=True):
        if not all([nome, sku, marca, ncm, imagem]):
            st.error("Preencha todos os campos")
        else:
            with st.spinner("Pegando token..."):
                token = get_token()
            if token:
                payload = gerar_payload(nome, sku, marca, marca, ncm, tamanho, imagem)
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                with st.spinner("Cadastrando produto..."):
                    r = requests.post(product_url, json=payload, headers=headers)
                    if r.status_code in [200, 201]:
                        gtin = r.json().get("gtin", "Ver resposta")
                        st.success(f"GTIN Gerado: **{gtin}**")
                        st.balloons()
                        st.json(r.json())
                    else:
                        st.error("Erro no cadastro")
                        st.code(r.text(r.text)
