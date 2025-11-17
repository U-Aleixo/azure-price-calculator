import streamlit as st
from get_prices import fetch_prices 
import datetime # <-- 1. IMPORTAMOS A BIBLIOTECA DE DATA

# -----------------------------------------------------------------
# 2. CRIAMOS UMA FUNÇÃO "HELPER" PARA ACHAR O PREÇO CERTO
# -----------------------------------------------------------------
def find_most_recent_price(items):
    """
    Filtra a lista de preços para achar o mais recente que já está ativo.
    """
    
    # Pega a data e hora de "agora", em formato UTC (o mesmo da API)
    today = datetime.datetime.now(datetime.timezone.utc)
    
    active_items = []
    
    for item in items:
        # Pega a data de início do item
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
            # Ignora itens com formato de data inválido
            continue

    # Se não achamos nenhum preço ativo
    if not active_items:
        return None
        
    # 3. DAS ATIVAS, ORDENAMOS PELA MAIS RECENTE
    # Ordena a lista de itens ativos pela data (do mais novo para o mais velho)
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
servicos_azure = [
    'Virtual Machines', 'Storage', 'Azure SQL Database', 'Azure Cosmos DB'
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
        # 4. CHAMAMOS NOSSA NOVA FUNÇÃO!
        # Em vez de 'primeiro_item = items[0]'
        most_recent_item = find_most_recent_price(items)
        
        if most_recent_item:
            st.success(f"Sucesso! {len(items)} preços encontrados.")
            
            # E usamos o 'most_recent_item' para o card
            st.metric(
                label=f"{most_recent_item.get('productName')}",
                value=f"$ {most_recent_item.get('retailPrice')}",
                delta="por " + most_recent_item.get('unitOfMeasure')
            )
            
            st.write(f"Preço ativo desde: {most_recent_item.get('effectiveStartDate')}")
            
            st.write("Amostra de todos os dados encontrados (incluindo antigos):")
            st.dataframe(items[:10]) 
        else:
            st.warning("Dados encontrados, mas nenhum preço parece estar ativo para hoje.")

    else:
        st.error(f"Não foi possível buscar dados para '{service_choice}' em '{region_choice}'.")
