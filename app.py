import streamlit as st
from get_prices import fetch_prices 
import datetime # <-- Solução para o Preço Correto

# -----------------------------------------------------------------
# FUNÇÃO PARA ACHAR O PREÇO MAIS RECENTE (PROBLEMA 2)
# -----------------------------------------------------------------
def find_most_recent_price(items):
    """
    Filtra a lista de preços para achar o mais recente que já está ativo.
    """
    
    # Pega a data e hora de "agora", em formato UTC (o mesmo da API)
    today = datetime.datetime.now(datetime.timezone.utc)
    
    active_items = []
    
    for item in items:
        start_date_str = item.get('effectiveStartDate')
        
        # Converte a data (string) para um objeto de data
        # Substitui o 'Z' por '+00:00' para o Python entender
        if start_date_str.endswith('Z'):
            start_date_str = start_date_str[:-1] + '+00:00'
        
        try:
            start_date = datetime.datetime.fromisoformat(start_date_str)
            
            # Se a data de início já passou (é menor ou igual a hoje)
            if start_date <= today:
                active_items.append(item)
        except (ValueError, TypeError):
            continue # Ignora datas em formato inválido

    if not active_items:
        return None # Se não achamos nenhum preço ativo
        
    # DAS ATIVAS, ORDENAMOS PELA MAIS RECENTE
    active_items.sort(key=lambda x: datetime.datetime.fromisoformat(x.get('effectiveStartDate').replace('Z', '+00:00')), reverse=True)
    
    # Retorna o primeiro da lista (o mais recente)
    return active_items[0]

# -----------------------------------------------------------------
# O RESTO DO APP
# -----------------------------------------------------------------

st.title("Calculadora de Preços (Estimativa) - Azure ☁️")

# --- FILTRO 1: REGIÃO ---
regioes_azure = [
    'eastus', 'westeurope', 'eastasia', 'brazilsouth', 'centralindia'
]
region_choice = st.selectbox(
    label="Escolha uma Região do Azure:",
    options=regioes_azure
)

# --- FILTRO 2: SERVIÇO ---
# *** AQUI ESTÁ A CORREÇÃO PARA O PROBLEMA 1 ***
# Usando os nomes corretos da API
servicos_azure = [
    'Virtual Machines', 
    'Storage',       # O nome correto para Armazenamento
    'SQL Database',       # O nome correto para o Banco de Dados SQL
    'Azure Cosmos DB'
]
service_choice = st.selectbox(
    label="Escolha um Serviço do Azure:",
    options=servicos_azure
)

st.write(f"Você selecionou: **{service_choice}** em **{region_choice}**")


if st.button("Buscar Preços Agora"):
    
    with st.spinner(f"Buscando dados para '{service_choice}' em '{region_choice}'..."):
        items = fetch_prices(region_choice, service_choice) 

    if items:
        # *** AQUI ESTÁ A CORREÇÃO PARA O PROBLEMA 2 ***
        # Em vez de 'primeiro_item = items[0]'
        most_recent_item = find_most_recent_price(items)
        
        if most_recent_item:
            st.success(f"Sucesso! {len(items)} preços encontrados.")
            
            st.metric(
                label=f"{most_recent_item.get('productName')}",
                value=f"$ {most_recent_item.get('retailPrice')}",
                delta="por " + most_recent_item.get('unitOfMeasure')
            )
            
            # Mostra a data do preço que estamos vendo
            st.write(f"Preço ativo desde: {most_recent_item.get('effectiveStartDate')}")
            
            st.write("Amostra de todos os dados (incluindo antigos):")
            st.dataframe(items[:10]) 
        else:
            st.warning("Dados encontrados, mas nenhum preço parece estar ativo para hoje.")

    else:
        st.error(f"Não foi possível buscar dados para '{service_choice}' em '{region_choice}'.")

