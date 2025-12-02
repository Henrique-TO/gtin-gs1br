# auth.py (versão anti-Akamai, testada em cenários similares)
import requests
import base64
import json
import time

class AuthManager:
    def __init__(self, config_path='config.json'):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        # ← MUDANÇA: Force HTTPS
        self.config["auth_url"] = self.config["auth_url"].replace("http://", "https://")

        self.token = None
        self.expiry = 0

    def _is_token_valid(self):
        return self.token and time.time() < self.expiry

    def _generate_auth_header(self):
        raw = f"{self.config['client_id']}:{self.config['client_secret']}"
        return base64.b64encode(raw.encode()).decode()

    def get_token(self):
        if self._is_token_valid():
            return self.token

        # ← MUDANÇA PRINCIPAL: Headers anti-bloqueio Akamai
        headers = {
            "Authorization": f"Basic {self._generate_auth_header()}",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",  # Browser real
            "Accept": "application/json, text/plain, */*",  # Aceita JSON
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",  # Linguagem BR
            "Accept-Encoding": "gzip, deflate, br",  # Compressão
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        }

        body = {
            "grant_type": "password",
            "username": self.config["username"],
            "password": self.config["password"]  # Gs1@Mudar#123
        }

        try:
            # Debug: Print URL final
            print(f"Chamando: {self.config['auth_url']}")
            response = requests.post(self.config["auth_url"], headers=headers, data=body, timeout=15)

            if response.status_code in [200, 201]:
                data = response.json()
                self.token = data["access_token"]
                self.expiry = time.time() + int(data["expires_in"]) - 60
                print("Token OK!")  # Para debug no console
                return self.token
            else:
                error_msg = f"Erro {response.status_code}: {response.text[:300]}..."
                if "Access Denied" in response.text or "edgesuite" in response.text:
                    error_msg += "\n\n🔥 BLOQUEIO AKAMAI DETECTADO! Adicione User-Agent ou libere IP."
                raise Exception(error_msg)
        except Exception as e:
            raise Exception(f"Erro de conexão: {e}")