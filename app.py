import streamlit as st
import requests
import base64

# ==== CREDENCIAIS (vêm do Render Secrets) ====
client_id = st.secrets["client_id"]
client_secret = st.secrets["client_secret"]
username = st.secrets["username"]
password = st.secrets["password"]

auth_url = "https://api.gs1br.org/oauth/access-token"
product_url = "https://api.gs1br.org/gs1/v2/products"

# ==== PADRÕES DE MALAS ====
padroes_malas = {
    'PP':     {'peso': 2.5, 'altura': 51, 'largura': 32, 'profundidade': 23},
    'P':      {'peso': 3.0, 'altura': 55, 'largura': 35, 'profundidade': 25},
    'M':      {'peso': 5.0, 'altura': 64, 'largura': 41, 'profundidade': 27},
    'G':      {'peso': 6.0, 'altura': 74, 'largura': 48, 'profundidade': 30},
    'KBMOP':  {'peso': 1.0, 'altura': 41, 'largura': 32, 'profundidade': 17},
    'KBMOU':  {'peso': 1.0, 'altura': 45, 'largura': 30, 'profundidade': 23},
    'KBMOE':  {'peso': 1.0, 'altura': 45, 'largura': 30, 'profundidade': 23},
    'KBSHPV': {'peso': 0.3, 'altura': 81, 'largura': 42, 'profundidade': 37},
    'KBSHG':  {'peso': 0.3, 'altura': 17, 'largura': 27, 'profundidade': 8},
    'KBSHR':  {'peso': 0.3, 'altura': 18, 'largura': 11, 'profundidade': 7},
    'NAOSEI': {'peso': 1.0, 'altura': 1,  'largura': 1,  'profundidade': 1}
}

# ==== FUNÇÃO PARA PEGAR TOKEN ====
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
        st.error("Erro ao obter token GS1")
        try:
            st.code(r.text)
        except:
            pass
        return None

# ==== PAYLOAD DO PRODUTO ====
def gerar_payload(nome_produto, sku, marca, ncm, tamanho, imagem_url):
    p = padroes_malas.get(tamanho, padroes_malas["NAOSEI"])
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
            "netContent": {"measurementUnitCode": "LTR", "value": p["peso"]},
            "height": {"value": p["altura"], "measurementUnitCode": "CMT"},
            "width": {"value": p["largura"], "measurementUnitCode": "CMT"},
            "depth": {"value": p["profundidade"], "measurementUnitCode": "CMT"}
        },
        "brandNameInformationLang": [
            {"brandName": marca, "languageCode": "pt-BR", "default": True}
        ],
        "additionalTradeItemIdentifications": [
            {"additionalTradeItemIdentificationTypeCode": "SKU", "additionalTradeItemIdentificationValue": sku}
        ],
        "tradeItemWeight": {
            "grossWeight": {"value": p["peso"], "measurementUnitCode": "KGM"},
            "netWeight": {"value": p["peso"], "measurementUnitCode": "KGM"}
        },
        "tradeItemClassification": {
            "additionalTradeItemClassifications": [
                {
                    "additionalTradeItemClassificationSystemCode": "NCM",
                    "additionalTradeItemClassificationCodeValue": ncm.replace(".", "")
                }
            ],
            "gpcCategoryCode": "10001096"
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

# ==== INTERFACE STREAMLIT ====
st.set_page_config(page_title="GTIN GS1BR – WBS", layout="centered")
st.title("Cadastrador de GTIN – GS1 Brasil")
st.markdown("### Malas & Bolsas • Rodando 24h no Render")

with st.form("cadastro_gtin"):
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome do Produto *", placeholder="Mala de Viagem 360º Preta")
        sku = st.text_input("SKU *", placeholder="MLA-001-PP")
        marca = st.text_input("Marca *", value="WBS")
    with col2:
        ncm = st.text_input("NCM *", value="4202.12.10")
        tamanho = st.selectbox("Tamanho *", options=list(padroes_malas.keys()))
        imagem_url = st.text_input("URL da Imagem *", placeholder="https://seusite.com/foto.jpg")

    submitted = st.form_submit_button("GERAR E CADASTRAR GTIN", type="primary", use_container_width=True)

    if submitted:
        if not all([nome, sku, marca, ncm, imagem_url]):
            st.error("Preencha todos os campos obrigatórios!")
        else:
            with st.spinner("Obtendo token GS1..."):
                token = get_token()
            if not token:
                st.stop()

            payload = gerar_payload(nome, sku, marca, ncm, tamanho, imagem_url)

            with st.spinner("Enviando produto para GS1..."):
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                try:
                    response = requests.post(product_url, json=payload, headers=headers, timeout=30)
                    if response.status_code in [200, 201]:
                        dados = response.json()
                        gtin = dados.get("gtin") or "Consulte a resposta completa"
                        st.success("GTIN cadastrado com sucesso!")
                        st.balloons()
                        st.subheader("GTIN Gerado")
                        st.code(gtin, language=None)
                        st.json(dados, expanded=False)
                    else:
                        st.error(f"Erro {response.status_code}")
                        st.code(response.text)
                except Exception as e:
                    st.error("Erro de conexão com a API")
                    st.exception(e)

st.caption("WBS Services • 2025 • IP liberado no Render")
