# app.py
import streamlit as st
import requests
import json
import base64
from datetime import datetime
from auth import AuthManager  # Seu arquivo antigo
# --- Configurações (você pode manter no config.json ou colocar no secrets do Streamlit) ---
# Para segurança máxima, use st.secrets (recomendado em produção)
# Mas para teste local, pode deixar assim:

CONFIG = {
    "client_id": "aa3e37ac-d64a-48c0-8628-e3470d26fc76",
    "client_secret": "4b15bc56-fe87-4cdc-8eae-3ef2810dd121",
    "username": "financeiro@wbsservices.com.br",
    "password": "Gs1@Mudar#123",
    "auth_url": "https://api.gs1br.org/oauth/access-token",
    "product_url": "https://api.gs1br.org/gs1/v2/products"
}

# Padrões de malas (mesmo do seu arquivo)
padroes_malas = {
    'PP':       {'peso': 2.5, 'altura': 51, 'largura': 32, 'profundidade': 23},
    'P':        {'peso': 3.0, 'altura': 55, 'largura': 35, 'profundidade': 25},
    'M':        {'peso': 5.0, 'altura': 64, 'largura': 41, 'profundidade': 27},
    'G':        {'peso': 6.0, 'altura': 74, 'largura': 48, 'profundidade': 30},
    'KBMOP':    {'peso': 1.0, 'altura': 41, 'largura': 32, 'profundidade': 17},
    'KBMOU':    {'peso': 1.0, 'altura': 45, 'largura': 30, 'profundidade': 23},
    'KBMOE':    {'peso': 1.0, 'altura': 45, 'largura': 30, 'profundidade': 23},
    'KBSHPV':   {'peso': 0.3, 'altura': 81, 'largura': 42, 'profundidade': 37},
    'KBSHG':    {'peso': 0.3, 'altura': 17, 'largura': 27, 'profundidade': 8},
    'KBSHR':    {'peso': 0.3, 'altura': 18, 'largura': 11, 'profundidade': 7},
    'NAOSEI':   {'peso': 1.0, 'altura': 1,  'largura': 1,  'profundidade': 1}
}

def get_token():
    auth = AuthManager('config.json')  # Seu config.json com senha "Gs1@Mudar#123"
    try:
        token = auth.get_token()
        st.success("Token obtido com sucesso!")
        return token
    except Exception as e:
        st.error(f"Erro no auth: {e}")
        st.info("Se for 'HEADER client_id', gere novo client_id no portal GS1.")
        return None
def gerar_payload(nome_produto, sku, marca, ncm, tamanho, imagem_url):
    padrao = padroes_malas.get(tamanho, padroes_malas["NAOSEI"])

    return {
        "company": {"cad": "A78480"},
        "gtinStatusCode": "ACTIVE",
        "acceptResponsibility": True,
        "shareDataIndicator": True,
        "gs1TradeItemIdentificationKey": {
            "gs1TradeItemIdentificationKeyCode": "GTIN_13"
        },
        "tradeItemDescriptionInformationLang": [
            {"tradeItemDescription": nome_produto, "languageCode": "pt-BR", "default": True}
        ],
        "referencedFileInformations": [
            {
                "uniformResourceIdentifier": imagem_url,
                "referencedFileTypeCode": "OUT_OF_PACKAGE_IMAGE",
                "featuredFile": True
            }
        ],
        "tradeItemMeasurements": {
            "netContent": {"measurementUnitCode": "LTR", "value": padrao["peso"]},
            "height": {"value": padrao["altura"], "measurementUnitCode": "CMT"},
            "width": {"value": padrao["largura"], "measurementUnitCode": "CMT"},
            "depth": {"value": padrao["profundidade"], "measurementUnitCode": "CMT"}
        },
        "brandNameInformationLang": [
            {"brandName": marca, "languageCode": "pt-BR", "default": True}
        ],
        "additionalTradeItemIdentifications": [
            {"additionalTradeItemIdentificationTypeCode": "SKU", "additionalTradeItemIdentificationValue": sku}
        ],
        "tradeItemWeight": {
            "grossWeight": {"value": padrao["peso"], "measurementUnitCode": "KGM"},
            "netWeight": {"value": padrao["peso"], "measurementUnitCode": "KGM"}
        },
        "tradeItemClassification": {
            "additionalTradeItemClassifications": [
                {
                    "additionalTradeItemClassificationSystemCode": "NCM",
                    "additionalTradeItemClassificationCodeValue": ncm.replace(".", "")
                }
            ],
            "gpcCategoryCode": "10001096"  # Malas, bolsas e acessórios
        },
        "tradeItem": {
            "targetMarket": {"targetMarketCountryCodes": ["076"]},
            "tradeItemUnitDescriptorCode": "CASE"
        },
        "placeOfProductActivity": {
            "countryOfOrigin": {
                "countryCode": "076",
                "countrySubdivisionCodes": ["BR-SP"]
            }
        }
    }

# ====================== INTERFACE STREAMLIT ======================
st.set_page_config(page_title="Cadastrador GTIN GS1BR - Malas", layout="centered")
st.title("Cadastrador de GTIN - GS1 Brasil")
st.markdown("### Cadastro automático de malas e bolsas")

with st.form("cadastro_gtin"):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome do Produto *", placeholder="Mala de Viagem 360º Preta")
        sku = st.text_input("SKU *", placeholder="MLA-001-PP")
        marca = st.text_input("Marca *", value="WBS", placeholder="WBS")
    with col2:
        ncm = st.text_input("NCM *", value="4202.12.10", placeholder="4202.12.10")
        tamanho = st.selectbox("Tamanho (Padrão Mala) *", options=list(padroes_malas.keys()))
        imagem_url = st.text_input("URL da Imagem *", placeholder="https://seusite.com/imagens/mala-pp.jpg")

    submitted = st.form_submit_button("GERAR E CADASTRAR GTIN", type="primary", use_container_width=True)

    if submitted:
        # Validação básica
        if not all([nome, sku, marca, ncm, imagem_url]):
            st.error("Preencha todos os campos obrigatórios!")
        else:
            with st.spinner("Obtendo token de acesso..."):
                token = get_token()
            if not token:
                st.stop()

            payload = gerar_payload(nome, sku, marca, ncm, tamanho, imagem_url)

            with st.spinner("Enviando para GS1BR..."):
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                try:
                    response = requests.post(CONFIG['product_url'], json=payload, headers=headers, timeout=30)
                    if response.status_code in (200, 201):
                        dados = response.json()
                        gtin = dados.get("gtin") or dados.get("gs1TradeItemIdentificationKey", {}).get("gtin")
                        st.success(f"GTIN cadastrado com sucesso!")
                        st.balloons()
                        st.subheader("GTIN Gerado:")
                        st.code(gtin, language=None)
                        st.json(dados, expanded=False)
                    else:
                        st.error(f"Erro {response.status_code} ao cadastrar")
                        st.code(response.text)
                except Exception as e:
                    st.error("Erro de conexão com a API GS1")
                    st.exception(e)

# Footer
st.markdown("---")
st.caption("App criado para agilizar cadastro de malas na GS1 Brasil • 2025")