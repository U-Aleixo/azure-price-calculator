import streamlit as st
import pandas as pd
import datetime
from get_prices import fetch_prices 

# ==============================================================================
# 1. CONFIGURAÇÃO E ESTADO (SESSION STATE)
# ==============================================================================
st.set_page_config(page_title="Calculadora Azure", page_icon="☁️", layout="wide")

# Garante que as variáveis existam na memória ao abrir o app
if "dados_azure" not in st.session_state:
    st.session_state["dados_azure"] = None # Guarda a lista crua da API

if "contexto_busca" not in st.session_state:
    st.session_state["contexto_busca"] = {} # Guarda o que foi pesquisado (Região/Serviço)

# ==============================================================================
# 2. FUNÇÕES AUXILIARES
# ==============================================================================
def find_most_recent_price(items):
    """
    Filtra a lista de preços para achar o mais recente que já está ativo.
    """
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
        
    # Ordena pela data mais recente
    active_items.sort(
        key=lambda x: datetime.datetime.fromisoformat(x.get('effectiveStartDate').replace('Z', '+00:00')), 
        reverse=True
    )
    
    return active_items[0]

# ==============================================================================
# 3. INTERFACE - BARRA LATERAL E TÍTULO
# ==============================================================================
st.title("Calculadora de Preços (Estimativa) - Azure ☁️")

# Mapeamento de Regiões
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
    servicos_azure = [
        'Cognitive Services',
        'Virtual Machines', 
        'Storage',
        'SQL Database',
        'Azure Cosmos DB'
    ]
    service_choice = st.selectbox("Escolha um Serviço do Azure:", servicos_azure)

# ==============================================================================
# 4. BOTÃO DE BUSCA (AÇÃO)
# ==============================================================================
if st.button("Buscar Preços Agora", type="primary"):
    
    with st.spinner(f"Consultando API do Azure para '{service_choice}'..."):
        # Busca os dados reais
        items_api = fetch_prices(region_choice, service_choice)
        
        if items_api:
            # SUCESSO: Salva no Session State
            st.session_state["dados_azure"] = items_api
            # Salva o contexto para sabermos como exibir depois
            st.session_state["contexto_busca"] = {
                "service": service_choice,
                "region": region_display
            }
        else:
            st.error("A API não retornou dados. Verifique sua conexão ou os filtros.")
            st.session_state["dados_azure"] = None # Limpa se der erro

# ==============================================================================
# 5. LÓGICA DE EXIBIÇÃO (PERSISTENTE)
# ==============================================================================
# Esta parte roda sempre, mesmo quando você aperta Enter no filtro de texto,
# porque ela lê o que está salvo na memória (session_state), não depende do botão.

items = st.session_state["dados_azure"]
contexto = st.session_state["contexto_busca"]

if items:
    
    # --- CASO 1: SERVIÇOS COGNITIVOS (IA) ---
    if contexto.get("service") == 'Cognitive Services':
        
        st.divider()
        
        # 1. Filtro Inicial (Limpeza)
        base_items = [
            item for item in items 
            if 'OpenAI' in item.get('productName', '') or 'gpt' in item.get('skuName', '').lower()
        ]
        
        st.info(f"Base carregada: {len(base_items)} itens de IA encontrados em {contexto.get('region')}.")

        # 2. BARRA DE PESQUISA INTERATIVA
        st.markdown("### 🔍 Encontre seu Modelo")
        search_term = st.text_input("Digite o nome do modelo para filtrar (ex: gpt 4o, gpt-35, mini):")
        
        # Aplica o filtro se houver texto
        if search_term:
            filtered_items = [
                item for item in base_items 
                if search_term.lower() in str(item).lower()
            ]
        else:
            filtered_items = base_items

        st.write(f"Mostrando {len(filtered_items)} itens:")
        
        # Mostra tabela
        if filtered_items:
            df_show = pd.DataFrame(filtered_items)
            # Seleciona colunas mais úteis para exibir, se existirem
            cols_to_show = ['productName', 'skuName', 'retailPrice', 'unitOfMeasure', 'effectiveStartDate']
            cols_final = [c for c in cols_to_show if c in df_show.columns]
            st.dataframe(df_show[cols_final], use_container_width=True)
        else:
            st.warning("Nenhum item corresponde à sua busca.")

        # 3. CALCULADORA
        st.markdown("---")
        st.subheader("🧮 Calculadora de Custo (Tokens)")
        st.caption("Use os valores da tabela acima ('retailPrice') para simular.")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Entrada (Input)**")
            price_input = st.number_input("Preço por 1K Tokens Entrada ($):", value=0.0050, format="%.6f")
            qtd_input = st.number_input("Qtd. Tokens Entrada:", value=1000, step=100)
        
        with col2:
            st.markdown("**Saída (Output)**")
            price_output = st.number_input("Preço por 1K Tokens Saída ($):", value=0.0150, format="%.6f")
            qtd_output = st.number_input("Qtd. Tokens Saída:", value=500, step=100)
        
        custo_input = (qtd_input / 1000) * price_input
        custo_output = (qtd_output / 1000) * price_output
        total = custo_input + custo_output
        
        st.markdown("---")
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.metric(label="Custo Total (USD)", value=f"$ {total:.6f}")
        with col_res2:
            st.metric(label="Estimativa (BRL)", value=f"R$ {total * 6.0:.4f}", delta="Dólar R$ 6.00")

    # --- CASO 2: OUTROS SERVIÇOS (VM, STORAGE, ETC) ---
    else:
        st.divider()
        most_recent_item = find_most_recent_price(items)
        
        if most_recent_item:
            st.success(f"Sucesso! {len(items)} preços encontrados para {contexto.get('service')}.")
            
            st.metric(
                label=f"{most_recent_item.get('productName')} ({most_recent_item.get('skuName')})",
                value=f"$ {most_recent_item.get('retailPrice')}",
                delta=f"por {most_recent_item.get('unitOfMeasure')}"
            )
            st.write(f"**Vigência:** {most_recent_item.get('effectiveStartDate')}")
            
            with st.expander("Ver tabela completa de preços"):
                st.dataframe(pd.DataFrame(items))
        else:
            st.warning("Dados encontrados, mas nenhum preço parece estar ativo/válido para hoje.")

elif st.session_state.get("contexto_busca"):
    # Caso raro onde o contexto existe mas a lista está vazia
    st.warning("Nenhum dado carregado.")