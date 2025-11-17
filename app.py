import streamlit as st
from get_prices import fetch_prices 

st.title("Calculadora de Preços (Estimativa) - Azure ☁️")

# --- FILTRO 1: REGIÃO ---
regioes_azure = [
    'eastus', 
    'westeurope', 
    'eastasia', 
    'brazilsouth', 
    'centralindia'
]
region_choice = st.selectbox(
    label="Escolha uma Região do Azure:",
    options=regioes_azure
)

# --- FILTRO 2: SERVIÇO ---
# (Você pode adicionar mais serviços a esta lista!)
servicos_azure = [
    'Virtual Machines',
    'Storage',
    'Azure SQL Database',
    'Azure Cosmos DB'
]
service_choice = st.selectbox(
    label="Escolha um Serviço do Azure:",
    options=servicos_azure
)

st.write(f"Você selecionou: **{service_choice}** em **{region_choice}**")


if st.button("Buscar Preços Agora"):
    
    with st.spinner(f"Buscando dados para '{service_choice}' em '{region_choice}'..."):
        
        # 3. PASSAMOS AS DUAS ESCOLHAS para a função
        items = fetch_prices(region_choice, service_choice) 

    if items:
        st.success(f"Sucesso! Encontramos {len(items)} itens.")
        
        primeiro_item = items[0]
        
        st.metric(
            label=f"{primeiro_item.get('productName')}",
            value=f"$ {primeiro_item.get('retailPrice')}",
            delta="por " + primeiro_item.get('unitOfMeasure')
        )
        
        st.write("Amostra dos dados encontrados:")
        st.dataframe(items[:10]) 

    else:
        st.error(f"Não foi possível buscar dados para '{service_choice}' em '{region_choice}'.")