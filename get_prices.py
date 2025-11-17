import requests
import json

# 1. A função agora aceita DOIS argumentos
def fetch_prices(region, service_name):
    """
    Conecta na API da Azure e busca preços do SERVIÇO e REGIÃO escolhidos.
    Retorna a lista de itens encontrados.
    """
    
    api_url = "https://prices.azure.com/api/retail/prices"
    
    # 2. O filtro agora usa as DUAS variáveis
    filtro_dinamico = f"armRegionName eq '{region}' and serviceName eq '{service_name}'"
    
    parametros = {
        '$filter': filtro_dinamico
    }

    print(f"LOG: A função fetch_prices() foi chamada para a região: {region} e serviço: {service_name}")

    try:
        response = requests.get(api_url, params=parametros)
        
        if response.status_code == 200:
            data = response.json()
            items = data.get('Items', [])
            return items
        else:
            print(f"Erro na API: {response.status_code}")
            return []

    except Exception as e:
        print(f"Erro na conexão: {e}")
        return []


# --- Código de Teste (atualizado) ---
if __name__ == "__main__":
    
    print("--- Testando 'get_prices.py' diretamente ---")
    
    # Testamos com uma região e um serviço
    dados = fetch_prices(region='westeurope', service_name='Storage') 
    
    if dados:
        print(f"Encontrados {len(dados)} itens.")
        print(f"Nome do Produto: {dados[0].get('productName')}")
        print(f"Preço (USD): {dados[0].get('retailPrice')}")
    else:
        print("Nenhum dado encontrado no teste.")