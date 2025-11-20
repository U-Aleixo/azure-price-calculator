import streamlit as st
import pandas as pd
import datetime
import requests  # Para buscar o dólar
from get_prices import fetch_prices 

# ==============================================================================
# 1. CONFIGURAÇÃO E ESTADO
# ==============================================================================
st.set_page_config(page_title="Calculadora Azure", page_icon="☁️", layout="wide")

if "dados_azure" not in st.session_state:
    st.session_state["dados_azure"] = None

if "contexto_busca" not in st.session_state:
    st.session_state["contexto_busca"] = {}

# ==============================================================================
# 2. FUNÇÕES AUXILIARES
# ==============================================================================

@st.cache_data(ttl=3600)
def get_dolar_rate():
    """Busca cotação do dólar ou retorna 6.0 em caso de erro."""
    try:
        url = "https://economia.awesomeapi.com.br/last/USD-BRL"
        response = requests.get(url, timeout=5)
        data = response.json()
        return float(data['USDBRL']['bid'])
    except:
        return 6.0

def find_most_recent_price(items):
    """Encontra o preço ativo mais recente."""
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
        except:
            continue 
    if not active_items: return None 
    active_items.sort(key=lambda x: x.get('effectiveStartDate'), reverse=True)
    return active_items[0]

# ==============================================================================
# 3. INTERFACE E FILTROS
# ==============================================================================
dolar_hoje = get_dolar_rate()

col_head1, col_head2 = st.columns([3, 1])
with col_head1:
    st.title("Calculadora de Preços Azure ☁️")
with col_head2:
    st.metric("Dólar Hoje (PTAX)", f"R$ {dolar_hoje:.3f}")

regioes_map = {
    'Leste (EUA)': 'eastus', 'Oeste (Europa)': 'westeurope',
    'Leste (Ásia)': 'eastasia', 'Sul (Brasil)': 'brazilsouth',
    'Central (Índia)': 'centralindia'
}

c1, c2 = st.columns(2)
region_choice = regioes_map[c1.selectbox("Região:", regioes_map.keys())]
service_choice = c2.selectbox("Serviço:", [
    'Cognitive Services', 'Virtual Machines', 'Storage', 
    'SQL Database', 'Azure Cosmos DB'
])

if st.button("Buscar Preços Agora", type="primary"):
    with st.spinner("Consultando API..."):
        data = fetch_prices(region_choice, service_choice)
        if data:
            st.session_state["dados_azure"] = data
            st.session_state["contexto_busca"] = {"svc": service_choice, "reg": region_choice}
        else:
            st.error("Erro ao buscar dados.")

# ==============================================================================
# 4. EXIBIÇÃO DOS DADOS
# ==============================================================================
items = st.session_state["dados_azure"]
ctx = st.session_state["contexto_busca"]

if items:
    # Lógica específica para AI (Cognitive Services)
    if ctx.get("svc") == 'Cognitive Services':
        st.divider()
        # Filtro base para limpar itens irrelevantes
        base = [i for i in items if 'OpenAI' in i.get('productName','') or 'gpt' in i.get('skuName','').lower()]
        
        st.markdown("### 🔍 Filtrar Modelo")
        filtro = st.text_input("Digite o nome (ex: gpt-4, mini):")
        filtered = [i for i in base if filtro.lower() in str(i).lower()] if filtro else base
        
        st.write(f"Encontrados: {len(filtered)} itens")
        
        if filtered:
            df = pd.DataFrame(filtered)
            cols = [c for c in ['skuName', 'retailPrice', 'unitOfMeasure'] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True)
            
            # CALCULADORA
            st.markdown("---")
            st.subheader("🧮 Calculadora de Tokens")
            
            opts = {f"{i['skuName']} ($ {i['retailPrice']})": i['retailPrice'] for i in filtered}
            list_opts = ["-- Manual --"] + list(opts.keys())
            
            cc1, cc2 = st.columns(2)
            # Inputs com seletores
            sel_in = cc1.selectbox("Modelo de Entrada:", list_opts, key='in')
            v_in = opts[sel_in] if sel_in != "-- Manual --" else 0.005
            p_in = cc1.number_input("Preço Entrada ($):", value=float(v_in), format="%.6f")
            q_in = cc1.number_input("Qtd Entrada:", value=1000, step=100)
            
            sel_out = cc2.selectbox("Modelo de Saída:", list_opts, key='out')
            v_out = opts[sel_out] if sel_out != "-- Manual --" else 0.015
            p_out = cc2.number_input("Preço Saída ($):", value=float(v_out), format="%.6f")
            q_out = cc2.number_input("Qtd Saída:", value=500, step=100)
            
            total_usd = ((q_in/1000)*p_in) + ((q_out/1000)*p_out)
            
            st.divider()
            cm1, cm2 = st.columns(2)
            cm1.metric("Total (USD)", f"$ {total_usd:.6f}")
            cm2.metric("Estimativa (BRL)", f"R$ {total_usd * dolar_hoje:.4f}", f"Dólar: {dolar_hoje:.3f}")

    # Lógica para outros serviços
    else:
        st.divider()
        recent = find_most_recent_price(items)
        if recent:
            usd = recent.get('retailPrice', 0)
            st.metric(recent.get('productName'), f"$ {usd}", f"R$ {usd * dolar_hoje:.4f}")
            st.dataframe(pd.DataFrame(items))
        else:
            st.warning("Nenhum preço ativo encontrado.")

# ==============================================================================
# 5. RODAPÉ (Fora de todos os 'ifs' para aparecer sempre)
# ==============================================================================
st.markdown("<br><br><hr>", unsafe_allow_html=True) # Espaço extra e linha
with st.container():
    st.markdown("### 📚 Fontes e Referências")
    f1, f2, f3 = st.columns(3)
    f1.info("**Azure API**\n\nDados oficiais da Microsoft Retail Prices.")
    f2.info(f"**Dólar PTAX**\n\nCotação via AwesomeAPI: R$ {dolar_hoje:.3f}")
    f3.warning("**Aviso**\n\nValores estimados. Não inclui impostos.")
