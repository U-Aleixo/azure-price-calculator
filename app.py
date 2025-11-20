import streamlit as st
import pandas as pd
import datetime
import requests  # Para buscar o dólar
from get_prices import fetch_prices 

# ==============================================================================
# 1. CONFIGURAÇÃO E ESTADO (SESSION STATE)
# ==============================================================================
st.set_page_config(page_title="Calculadora Azure", page_icon="☁️", layout="wide")

# Garante que as variáveis existam na memória ao abrir o app
if "dados_azure" not in st.session_state:
    st.session_state["dados_azure"] = None

if "contexto_busca" not in st.session_state:
    st.session_state["contexto_busca"] = {}

# ==============================================================================
# 2. FUNÇÕES AUXILIARES (Cotação e Filtros)
# ==============================================================================

@st.cache_data(ttl=3600) # Cache de 1 hora para não chamar a API toda hora
def get_dolar_rate():
    """Busca a cotação atual do Dólar (USD-BRL) na AwesomeAPI."""
    try:
        # API pública e gratuita focada no mercado brasileiro
        url = "https://economia.awesomeapi.com.br/last/USD-BRL"
        response = requests.get(url, timeout=5)
        data = response.json()
        # 'bid' é o valor de compra.
        rate = float(data['USDBRL']['bid'])
        return rate
    except Exception as e:
        st.error(f"Erro ao buscar dólar: {e}")
        return 6.0 # Valor de fallback de segurança se a API falhar

def find_most_recent_price(items):
    """Filtra a lista de preços para achar o mais recente que já está ativo."""
    today = datetime.datetime.now(datetime.timezone.utc)
    active_items = []
    
    for item in items:
        start_date_str = item.get('effectiveStartDate')
        if start_date_str and start_date_str.endswith('Z'):
            start_date_str = start_date_str[:-1] + '+00:00'
        try:
            start_date = datetime.datetime.fromisoformat(start_date_str)
            if start_date <= today:
                active_items.append(item)
        except (ValueError, TypeError):
            continue 

    if not active_items:
        return None 
        
    active_items.sort(
        key=lambda x: datetime.datetime.fromisoformat(x.get('effectiveStartDate').replace('Z', '+00:00')), 
        reverse=True
    )
    return active_items[0]

# ==============================================================================
# 3. INTERFACE - CABEÇALHO E FILTROS
# ==============================================================================
# Busca o dólar logo no início
dolar_hoje = get_dolar_rate()

col_header1, col_header2 = st.columns([3, 1])
with col_header1:
    st.title("Calculadora de Preços Azure ☁️")
with col_header2:
    # Mostra o indicador do Dólar no topo
    st.metric(label="Cotação Dólar (Hoje)", value=f"R$ {dolar_hoje:.3f}")

regioes_map = {
    'Leste (EUA)': 'eastus',
    'Oeste (Europa)': 'westeurope',
    'Leste (Ásia)': 'eastasia',
    'Sul (Brasil)': 'brazilsouth',
    'Central (Índia)': 'centralindia'
}

col_top1, col_top2 = st.columns(2)
with col_top1:
    region_display = st.selectbox("Escolha uma Região do Azure:", regioes_map.keys())
    region_choice = regioes_map[region_display]

with col_top2:
    servicos_azure = ['Cognitive Services', 'Virtual Machines', 'Storage', 'SQL Database', 'Azure Cosmos DB']
    service_choice = st.selectbox("Escolha um Serviço do Azure:", servicos_azure)

# ==============================================================================
# 4. BOTÃO DE BUSCA
# ==============================================================================
if st.button("Buscar Preços Agora", type="primary"):
    with st.spinner(f"Consultando API do Azure para '{service_choice}'..."):
        items_api = fetch_prices(region_choice, service_choice)
        if items_api:
            st.session_state["dados_azure"] = items_api
            st.session_state["contexto_busca"] = {"service": service_choice, "region": region_display}
        else:
            st.error("A API não retornou dados. Verifique sua conexão ou os filtros.")
            st.session_state["dados_azure"] = None

# ==============================================================================
# 5. LÓGICA DE EXIBIÇÃO
# ==============================================================================
items = st.session_state["dados_azure"]
contexto = st.session_state["contexto_busca"]

if items:
    # --- CASO 1: SERVIÇOS COGNITIVOS (IA) ---
    if contexto.get("service") == 'Cognitive Services':
        st.divider()
        
        base_items = [i for i in items if 'OpenAI' in i.get('productName', '') or 'gpt' in i.get('skuName', '').lower()]
        st.info(f"Base carregada: {len(base_items)} itens de IA encontrados em {contexto.get('region')}.")

        st.markdown("### 🔍 Encontre seu Modelo")
        search_term = st.text_input("Digite o nome do modelo para filtrar (ex: gpt 4o, gpt-35, mini):")
        
        if search_term:
            filtered_items = [i for i in base_items if search_term.lower() in str(i).lower()]
        else:
            filtered_items = base_items

        st.write(f"Mostrando {len(filtered_items)} itens:")
        
        if filtered_items:
            df_show = pd.DataFrame(filtered_items)
            cols_final = [c for c in ['productName', 'skuName', 'retailPrice', 'unitOfMeasure', 'effectiveStartDate'] if c in df_show.columns]
            st.dataframe(df_show[cols_final], use_container_width=True)
        else:
            st.warning("Nenhum item corresponde à sua busca.")

        # --- CALCULADORA INTELIGENTE ---
        st.markdown("---")
        st.subheader("🧮 Calculadora de Custo (Tokens)")
        st.caption("Selecione abaixo quais modelos usar para preencher os preços automaticamente.")

        # Cria lista amigável para o dropdown
        opcoes_modelos = {f"{item['skuName']} | $ {item['retailPrice']}": item['retailPrice'] for item in filtered_items}
        lista_opcoes = ["-- Digitar Manualmente --"] + list(opcoes_modelos.keys())

        col_sel1, col_sel2 = st.columns(2)
        val_input_default = 0.0050
        val_output_default = 0.0150

        with col_sel1:
            sel_input = st.selectbox("Selecionar Modelo de Entrada (Input):", lista_opcoes, key="sel_in")
            if sel_input != "-- Digitar Manualmente --":
                val_input_default = opcoes_modelos[sel_input]

        with col_sel2:
            sel_output = st.selectbox("Selecionar Modelo de Saída (Output):", lista_opcoes, key="sel_out")
            if sel_output != "-- Digitar Manualmente --":
                val_output_default = opcoes_modelos[sel_output]

        st.markdown("") 

        c1, c2 = st.columns(2)
        with c1:
            # O campo inicia com o valor selecionado no dropdown
            price_input = st.number_input("Preço 1K Tokens Entrada ($):", value=float(val_input_default), format="%.6f")
            qtd_input = st.number_input("Qtd. Tokens Entrada:", value=1000, step=100)
        
        with c2:
            price_output = st.number_input("Preço 1K Tokens Saída ($):", value=float(val_output_default), format="%.6f")
            qtd_output = st.number_input("Qtd. Tokens Saída:", value=500, step=100)
        
        custo_input = (qtd_input / 1000) * price_input
        custo_output = (qtd_output / 1000) * price_output
        total_usd = custo_input + custo_output
        total_brl = total_usd * dolar_hoje
        
        st.markdown("---")
        cr1, cr2 = st.columns(2)
        with cr1:
            st.metric(label="Custo Total (USD)", value=f"$ {total_usd:.6f}")
        with cr2:
            st.metric(
                label="Estimativa (BRL)", 
                value=f"R$ {total_brl:.4f}", 
                delta=f"Cotação usada: R$ {dolar_hoje:.3f}"
            )

    # --- OUTROS SERVIÇOS ---
    else:
        st.divider()
        most_recent_item = find_most_recent_price(items)
        if most_recent_item:
            st.success(f"Sucesso! {len(items)} preços encontrados.")
            
            price_usd = most_recent_item.get('retailPrice')
            price_brl = price_usd * dolar_hoje
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                st.metric(
                    label=f"{most_recent_item.get('productName')}",
                    value=f"$ {price_usd}",
                    delta=f"por {most_recent_item.get('unitOfMeasure')}"
                )
            with col_res2:
                st.metric(
                    label="Preço Aproximado (BRL)",
                    value=f"R$ {price_brl:.4f}",
                    delta=f"Cotação: R$ {dolar_hoje:.3f}"
                )
                
            st.dataframe(pd.DataFrame(items))
        else:
            st.warning("Dados encontrados, mas nenhum preço válido hoje.")

elif st.session_state.get("contexto_busca"):
    st.warning("Nenhum dado carregado.")

# ==============================================================================
# 6. RODAPÉ E FONTES (CREDIBILIDADE)
# ==============================================================================
st.markdown("---")
with st.container():
    st.markdown("### 📚 Fontes de Dados e Transparência")
    
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        st.markdown("**☁️ Preços de Nuvem**")
        st.caption("Os valores são obtidos em tempo real diretamente da [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices).")
    
    with col_f2:
        st.markdown("**💲 Cotação do Dólar**")
        st.caption("Conversão baseada na taxa PTAX/Comercial fornecida pela [AwesomeAPI](https://docs.awesomeapi.com.br/api-de-moedas).")
        
    with col_f3:
        st.markdown("**⚠️ Aviso Legal**")
        st.caption("Os valores apresentados são **estimativas** e não incluem impostos locais (IOF, ISS) ou descontos de contrato Enterprise (EA).")
