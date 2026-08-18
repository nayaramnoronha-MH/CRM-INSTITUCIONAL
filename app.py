import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import os
import datetime
import traceback
import shutil
import re
import urllib.parse
import json
import requests
import plotly.express as px

# Set page config
st.set_page_config(
    page_title="Central de Controle CRM - Mandato",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Standard Responsibles (Nayara removed, Edilson added)
OPERATORS = {
    'CARLOS': {'color': '#FF6B00'},
    'CLARINHA': {'color': '#E6007E'},
    'VERÔNICA': {'color': '#4F46E5'},
    'EDILSON': {'color': '#10B981'},
    'PEDRO': {'color': '#F59E0B'},
    'RAQUIL': {'color': '#06B6D4'}
}

# Predefined coordinates dictionary for SP cities
PREDEFINED_COORDS = {
    'são paulo': [-23.5505, -46.6333], 'sao paulo': [-23.5505, -46.6333],
    'são paulo ': [-23.5505, -46.6333], 'sao paulo ': [-23.5505, -46.6333],
    'são paulo-sp': [-23.5505, -46.6333], 'sao paulo-sp': [-23.5505, -46.6333],
    'bauru': [-22.3145, -49.0587], 'santos': [-23.9608, -46.3331],
    'guarulhos': [-23.4628, -46.5333], 'santo andré': [-23.6666, -46.5322],
    'santo andre': [-23.6666, -46.5322], 'mauá': [-23.6678, -46.4614],
    'maua': [-23.6678, -46.4614], 'rio claro': [-22.4114, -47.5614],
    'rio claro ': [-22.4114, -47.5614], 'itanhaém': [-24.1856, -46.7917],
    'itanhaem': [-24.1856, -46.7917], 'vargem grande do sul': [-21.8317, -46.8903],
    'capão bonito': [-24.0064, -48.3494], 'capao bonito': [-24.0064, -48.3494],
    'guarujá': [-23.9931, -46.2564], 'guaruja': [-23.9931, -46.2564],
    'agudos': [-22.4694, -48.9872], 'itararé': [-24.1169, -49.3314],
    'itarare': [-24.1169, -49.3314], 'piracicaba': [-22.7253, -47.6492],
    'são josé dos campos': [-23.2237, -45.9009], 'sao jose dos campos': [-23.2237, -45.9009],
    'assis': [-22.6617, -50.4189], 'são josé do rio preto': [-20.8113, -49.3758],
    'sao jose do rio preto': [-20.8113, -49.3758], 'franca': [-20.5386, -47.4008],
    'bariri': [-22.0744, -48.7408], 'embu das artes': [-23.6489, -46.8522],
    'caconde': [-21.5294, -46.6439], 'campinas': [-22.9064, -47.0616],
    'peruíbe': [-24.3200, -46.9983], 'peruibe': [-24.3200, -46.9983],
    'cajamar': [-23.3556, -46.8778], 'bertioga': [-23.8542, -46.1386],
    'salto': [-22.9839, -47.2858], 'sorocaba': [-23.5019, -47.4581],
    'ourinhos': [-22.9789, -49.8706], 'socorro': [-22.5892, -46.5222],
    'joanópolis': [-22.9300, -46.2758], 'joanopolis': [-22.9300, -46.2758],
    'santa cruz da esperança': [-21.2883, -47.4394], 'santa cruz da esperanca': [-21.2883, -47.4394],
    'dracena': [-21.4842, -51.5333], 'ferraz de vasconcelos': [-23.5414, -46.3683],
    'pederneiras': [-22.3517, -48.8125], 'dois córregos': [-22.3664, -48.3797],
    'dois corregos': [-22.3664, -48.3797], 'birigui': [-21.2889, -50.3400],
    'taubaté': [-23.0264, -45.5558], 'taubate': [-23.0264, -45.5558],
    'águas da prata': [-21.9367, -46.7169], 'aguas da prata': [-21.9367, -46.7169],
    'valinhos': [-22.9694, -46.9961], 'paraíso': [-20.9258, -48.7831],
    'paraiso': [-20.9258, -48.7831], 'jarinu': [-23.0994, -46.7289],
    'ribeirão preto': [-21.1704, -47.8103], 'ribeirao preto': [-21.1704, -47.8103],
    'ribeirão preto-sp': [-21.1704, -47.8103], 'botucatu': [-22.8858, -48.4450],
    'piracaia': [-23.0542, -46.3586], 'suzano': [-23.5378, -46.3108],
    'casa branca': [-21.7739, -47.0864], 'cotia': [-23.6039, -46.9189],
    'itapevi': [-23.5489, -46.9342], 'jundiaí': [-23.1864, -46.8842],
    'jundiai': [-23.1864, -46.8842], 'são josé do rio pardo': [-21.5956, -46.8906],
    'sao jose do rio pardo': [-21.5956, -46.8906], 'votuporanga': [-20.4244, -49.9725],
    'são carlos': [-22.0175, -47.8908], 'sao carlos': [-22.0175, -47.8908],
    'diadema': [-23.6861, -46.6233], 'santa fé do sul': [-20.2106, -50.9256],
    'santa fe do sul': [-20.2106, -50.9256], 'são caetano do sul': [-23.6181, -46.5703],
    'sao caetano do sul': [-23.6181, -46.5703], 'caraguatatuba': [-23.6225, -45.4125],
    'tapiraí': [-23.9636, -47.5069], 'tapirai': [-23.9636, -47.5069],
    'são sebastião': [-23.7600, -45.4125], 'sao sebastiao': [-23.7600, -45.4125],
    'ubatuba': [-23.4339, -45.0711], 'araraquara': [-21.7944, -48.1756],
    'taquarituba': [-23.5322, -49.2472], 'pardinho': [-23.0811, -48.3739],
    'piacatu': [-21.5794, -50.5964], 'ibiúna': [-23.6558, -47.2239],
    'ibiuna': [-23.6558, -47.2239], 'limeira': [-22.5647, -47.4017],
    'limeira ': [-22.5647, -47.4017], 'cachoeira paulista': [-22.6639, -45.0094],
    'bragança paulista': [-22.9578, -46.5419], 'braganca paulista': [-22.9578, -46.5419],
    'cravinhos': [-21.2383, -47.7297], 'cosmópolis': [-22.6433, -47.1961],
    'cosmopolis': [-22.6433, -47.1961], 'avaré': [-23.1022, -48.9256],
    'avare': [-23.1022, -48.9256], 'ilha solteira': [-20.3853, -51.3414],
    'itapecerica da serra': [-23.7169, -46.8489], 'itapecerica da serra ': [-23.7169, -46.8489],
    'itapeva': [-23.9822, -48.8767], 'osasco': [-23.5325, -46.7917],
    'poá': [-23.5283, -46.3439], 'poa': [-23.5283, -46.3439],
    'cunha': [-23.0789, -44.9592], 'barueri': [-23.5111, -46.8764],
    'itobi': [-21.7372, -46.9744], 'mogi das cruzes': [-23.5225, -46.1883],
    'campos novos paulista': [-22.6028, -50.0089], 'cândido mota': [-22.7475, -50.3878],
    'candido mota': [-22.7475, -50.3878], 'são bento do sapucaí': [-22.6869, -45.7336],
    'sao bento do sapucai': [-22.6869, -45.7336], 'nova odessa': [-22.7817, -47.2944],
    'monte mor': [-22.9464, -47.3075], 'marília': [-22.2139, -49.9458],
    'marilia': [-22.2139, -49.9458], 'capivari': [-22.9983, -47.5078],
    'pindamonhangaba': [-22.9244, -45.4611], 'atibaia': [-23.1189, -46.5583],
    'carapicuíba': [-23.5236, -46.8403], 'carapicuiba': [-23.5236, -46.8403],
    'mairiporã': [-23.3186, -46.5867], 'mairipora': [-23.3186, -46.5867],
    'serrana': [-21.2117, -47.5956], 'amparo': [-22.7011, -46.7642],
    'ilhabela': [-23.7781, -45.3581], 'são bernardo do campo': [-23.6939, -46.5650],
    'sao bernardo do campo': [-23.6939, -46.5650], 'taboão da serra': [-23.6231, -46.7867],
    'taboao da serra': [-23.6231, -46.7867], 'vinhedo': [-23.0294, -46.9744],
    'araçariguama': [-23.4383, -47.0608], 'aracariguama': [-23.4383, -47.0608],
    'itaquaquecetuba': [-23.4861, -46.3483], 'itaporanga': [-23.7083, -49.4900],
    'francisco morato': [-23.2817, -46.7450], 'mogi mirim': [-22.4319, -46.9533],
    'caieiras': [-23.3639, -46.7408], 'votorantim': [-23.5431, -47.4447],
    'itatiba': [-23.0039, -46.8436], 'louveira': [-23.0861, -46.9514],
    'registro': [-24.4875, -47.8436], 'itu': [-23.2642, -47.2992],
    'presidente prudente': [-22.1256, -51.3889], 'franco da rocha': [-23.3283, -46.7267],
    'hortolândia': [-22.8581, -47.2200], 'hortolandia': [-22.8581, -47.2200]
}

CACHE_FILE = "city_coords_cache.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Apply custom styles (Marinas por SP + Mobile Responsive)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}

/* Custom button styles */
div.stButton > button {
    background-color: #FF6B00;
    color: white;
    border-radius: 8px;
    border: none;
    font-weight: 600;
    padding: 0.5rem 1rem;
    transition: background-color 0.2s, transform 0.1s;
    width: 100%;
}

div.stButton > button:hover {
    background-color: #E6007E;
    color: white;
    transform: scale(1.02);
}

div.stButton > button:active {
    transform: scale(0.98);
}

/* Tab styling */
button[data-baseweb="tab"] {
    font-size: 1.1rem;
    font-weight: 600;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: #FF6B00 !important;
    border-color: #FF6B00 !important;
}

/* Mobile Responsive Styling */
@media (max-width: 768px) {
    .stHorizontalBlock {
        flex-direction: column !important;
    }
    div.stColumns {
        display: block !important;
    }
    div.stColumn {
        width: 100% !important;
        margin-bottom: 12px !important;
    }
    .metric-card {
        padding: 10px !important;
        margin-bottom: 8px !important;
    }
    .metric-value {
        font-size: 1.4rem !important;
    }
    .metric-title {
        font-size: 0.75rem !important;
    }
}
</style>
""", unsafe_allow_html=True)

# Coordinates Cache
def load_coords_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_coords_cache(cache):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=4)
    except:
        pass

def get_city_coords(city_name):
    if not isinstance(city_name, str) or not city_name.strip():
        return -23.5505, -46.6333
        
    city_clean = city_name.strip().lower()
    
    # Check predefined dict
    if city_clean in PREDEFINED_COORDS:
        return PREDEFINED_COORDS[city_clean][0], PREDEFINED_COORDS[city_clean][1]
        
    # Check cache
    cache = load_coords_cache()
    if city_clean in cache:
        return cache[city_clean]["lat"], cache[city_clean]["lon"]
        
    # Query Nominatim API as fallback
    try:
        query_str = f"{city_name.strip()}, São Paulo, Brazil"
        url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query_str)}&format=json&limit=1"
        headers = {"User-Agent": "CRM-Institutional-Mandato/1.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                cache[city_clean] = {"lat": lat, "lon": lon}
                save_coords_cache(cache)
                return lat, lon
    except:
        pass
        
    return -23.5505, -46.6333

# Helper function to parse boolean values
def parse_bool(val):
    if pd.isna(val) or val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    val_str = str(val).strip().lower()
    return val_str in ['sim', 's', 'yes', 'y', 'true', '1', '1.0']

# Cardápio Político/Apoio boolean parser (considers everything positive except "Não", empty, False, 0)
def parse_cardapio_bool(val):
    if pd.isna(val) or val is None:
        return False
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return bool(val)
    val_str = str(val).strip().lower()
    if val_str in ['', 'não', 'nao', 'false', '0', '0.0']:
        return False
    return True

# Helper to normalize responsible names
def normalize_responsavel(name):
    if pd.isna(name):
        return 'Outros'
    name_str = str(name).strip().upper()
    if 'CARLOS' in name_str:
        return 'CARLOS'
    elif 'CLARINHA' in name_str or name_str == 'CLARA':
        return 'CLARINHA'
    elif 'VERÔNICA' in name_str or 'VERONICA' in name_str or 'VEÔNICA' in name_str:
        return 'VERÔNICA'
    elif 'EDILSON' in name_str:
        return 'EDILSON'
    elif 'PEDRO' in name_str:
        return 'PEDRO'
    elif 'RAQUIL' in name_str:
        return 'RAQUIL'
    return name_str

# Agenda/Roda temática regex absolute count parser
def parse_agenda_count(val):
    if pd.isna(val) or val is None:
        return 0
    if isinstance(val, bool):
        return 1 if val else 0
    if isinstance(val, (int, float)):
        return int(val)
    val_str = str(val).strip().upper()
    if val_str in ['NÃO', 'FALSE', 'F', '0', '0.0', '']:
        return 0
    if val_str in ['SIM', 'TRUE', 'T', '1', '1.0']:
        return 1
    
    match = re.search(r'SIM\s*-\s*(\d+)', val_str)
    if match:
        return int(match.group(1))
        
    numbers = re.findall(r'\d+', val_str)
    if numbers:
        return int(numbers[0])
        
    if 'SIM' in val_str:
        return 1
    return 0

# Count the number of supports closed in a single row (expanding to 13 frentes)
def get_row_apoios_count(row, col_map):
    count = 0
    if col_map.get('agenda_roda'):
        count += parse_agenda_count(row.get(col_map['agenda_roda']))
        
    cardapio_keys = [
        'kit_materiais', 'video_instagram', 'grupo_whatsapp',
        'grupo_marinas', 'newsletter', 'contribuir_pautas',
        'perfuraid', 'apoio_pf', 'voluntario', 'doacao_financeira',
        'cartinha', 'aniversario_mh'
    ]
    for key in cardapio_keys:
        col_name = col_map.get(key)
        if col_name:
            if parse_cardapio_bool(row.get(col_name)):
                count += 1
    return count

# Alerta de Tempo Sem Contato Calculator
def get_contact_alert(last_contact_date):
    if pd.isna(last_contact_date) or last_contact_date is None:
        return "🔴 +15 dias sem contato"
    
    if isinstance(last_contact_date, (datetime.datetime, datetime.date)):
        contact_date = last_contact_date
        if isinstance(contact_date, datetime.datetime):
            contact_date = contact_date.date()
    else:
        try:
            contact_date = pd.to_datetime(last_contact_date).date()
        except:
            return "🔴 +15 dias sem contato"
            
    today = datetime.date.today()
    days_diff = (today - contact_date).days
    
    if days_diff >= 15:
        return f"🔴 +15 dias sem contato ({days_diff}d)"
    elif 8 <= days_diff <= 14:
        return f"🟡 {days_diff} dias sem contato"
    else:
        return "🟢 Recente (0 a 7 dias)"

# Get Google Credentials & Client
@st.cache_resource
def get_gspread_client():
    if "gcp_service_account" not in st.secrets or st.secrets["gcp_service_account"]["project_id"] == "insira-project-id":
        return None
        
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "\\n" in creds_dict["private_key"]:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error(f"Erro de autenticação com o Google Sheets: {e}")
        return None

# Clean and load data from Google Sheets API
@st.cache_data(ttl=30)
def load_data_from_sheets():
    client = get_gspread_client()
    if client is None:
        return None, {}, [], None
        
    try:
        spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
        sh = client.open_by_key(spreadsheet_id)
        worksheet = sh.worksheet("CRM INSTITUCIONAL")
        
        # Read all sheet values
        records = worksheet.get_all_values()
        if not records:
            return None, {}, [], None
            
        # Parse data
        original_cols = records[0]
        data = records[1:]
        
        df = pd.DataFrame(data, columns=original_cols)
        
        # Flex column mapping (expanded for all 13 cardapio columns and free-text support fields)
        standard_columns = {
            'instituicao': ['nome da institui', 'institui'],
            'representante': ['nome e sobrenome', 'representante', 'nome do contato'],
            'telefone': ['telefone [', 'telefone do representante', 'telefone_representante', 'telefone do contato'],
            'cargo': ['cargo', 'função do representante', 'funcao'],
            'email': ['email', 'e-mail'],
            'endereco': ['endereço da institui', 'endereco da', 'endereco'],
            'municipio': ['município da institui', 'municipio da', 'cidade', 'município'],
            'zona': ['zona'],
            'historico': ['histórico de contatos', 'historico'],
            'status': ['status'],
            'prioridade': ['prioridade'],
            'responsavel': ['responsável', 'responsavel'],
            'pauta': ['pauta'],
            'agenda_roda': ['agenda / roda tem', 'agenda/roda tem', 'agenda / roda temática', 'agenda / roda tematica'],
            'kit_materiais': ['kit de materiais', 'kits de materiais'],
            'video_instagram': ['vídeo de instagram', 'video de instagram', 'vídeo instagram', 'video instagram'],
            'grupo_whatsapp': ['envio de conteúdo em grupos de whatsapp', 'envio de conteudo em grupos de whatsapp', 'grupo de whatsapp', 'conteúdo no whatsapp'],
            'grupo_marinas': ['entrar no grupo das marinas', 'grupo das marinas', 'grupo marinas'],
            'newsletter': ['newsletter da instituição/região', 'newsletter da instituicao/regiao', 'newsletter'],
            'contribuir_pautas': ['contribuir com pautas', 'contribuir pautas'],
            'perfuraid': ['perfuraid - adesivo de carro', 'perfuraid', 'adesivo de carro'],
            'apoio_pf': ['apoio na pf', 'apoio pf'],
            'voluntario': ['voluntário', 'voluntario'],
            'doacao_financeira': ['doação financeira', 'doacao', 'financeira'],
            'cartinha': ['cartinha'],
            'aniversario_mh': ['aniversário mh', 'aniversario mh', 'aniversário m.h.', 'aniversario m.h.'],
            'outros_apoios': ['outros apoios', 'outro apoio'],
            'endereco_kit_cartinha': ['endereço para receber o kit/cartinha', 'endereco para receber o kit/cartinha', 'endereço para receber', 'endereco kit/cartinha'],
            'data_ultimo_contato': ['data do último contato', 'ultimo contato'],
            'data_roda_conversa': ['data da roda'],
            'instagram': ['instagram'],
            'origem': ['origem da instituição', 'origem da instituicao', 'origem']
        }
        
        col_map = {}
        for key, patterns in standard_columns.items():
            found = None
            for p in patterns:
                for col in df.columns:
                    if p.lower() in str(col).lower():
                        found = col
                        break
                if found:
                    break
            col_map[key] = found
            
        # Clean Types in DataFrame
        # Convert checklists to boolean
        cardapio_keys = [
            'kit_materiais', 'video_instagram', 'grupo_whatsapp',
            'grupo_marinas', 'newsletter', 'contribuir_pautas',
            'perfuraid', 'apoio_pf', 'voluntario', 'doacao_financeira',
            'cartinha', 'aniversario_mh'
        ]
        for key in cardapio_keys:
            col_name = col_map.get(key)
            if col_name and col_name in df.columns:
                df[col_name] = df[col_name].apply(parse_bool)
                
        # Convert dates
        for key in ['data_ultimo_contato', 'data_roda_conversa']:
            col_name = col_map.get(key)
            if col_name and col_name in df.columns:
                df[col_name] = df[col_name].replace('', None)
                df[col_name] = pd.to_datetime(df[col_name], errors='coerce', dayfirst=True)
                
        return df, col_map, original_cols, worksheet
        
    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Sheets: {e}")
        st.text(traceback.format_exc())
        return None, {}, [], None

# Custom metric card rendering with HTML/CSS
def render_metric_card(title, value, color="#FF6B00", subtitle=""):
    st.markdown(f"""
    <div class="metric-card" style="
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
        border-top: 4px solid {color};
        text-align: center;
        margin-bottom: 12px;
    ">
        <div class="metric-title" style="font-size: 0.8rem; font-weight: 500; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">{title}</div>
        <div class="metric-value" style="font-size: 1.8rem; font-weight: 700; color: #111827; margin-bottom: 2px;">{value}</div>
        <div style="font-size: 0.7rem; color: #9CA3AF;">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

# Helper function to get contacts made in the current week
def get_contacts_this_week(df, operator, date_col, resp_col):
    if not date_col or not resp_col:
        return 0
    op_mask = df[resp_col].apply(normalize_responsavel) == operator
    op_df = df[op_mask]
    
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=today.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    
    start_dt = pd.to_datetime(start_of_week)
    end_dt = pd.to_datetime(end_of_week) + pd.Timedelta(hours=23, minutes=59, seconds=59)
    
    valid_dates = pd.to_datetime(op_df[date_col]).dropna()
    contacts_count = valid_dates[(valid_dates >= start_dt) & (valid_dates <= end_dt)].count()
    return contacts_count

# Write updates to Google Sheets securely in a single batch call (update_cells)
def update_google_sheet_row(worksheet, row_idx, updates, col_map, original_cols):
    from gspread.cell import Cell
    
    excel_row = int(row_idx) + 2
    
    try:
        headers = [str(val).strip() for val in worksheet.row_values(1)]
    except Exception as e:
        headers = [str(col).strip() for col in original_cols]
        
    cells_to_update = []
    max_cols = len(headers)
    
    for key, val in updates.items():
        col_name = col_map.get(key)
        if col_name:
            col_name_strip = col_name.strip()
            if col_name_strip in headers:
                col_idx = headers.index(col_name_strip) + 1
                
                # Safety check: ensure column index is within header range
                if col_idx < 1 or col_idx > max_cols:
                    continue
                    
                # format value
                formatted_val = ""
                if key == 'agenda_roda':
                    formatted_val = str(val)
                elif key in ['kit_materiais', 'video_instagram', 'grupo_whatsapp', 'grupo_marinas', 'newsletter', 'contribuir_pautas', 'perfuraid', 'apoio_pf', 'voluntario', 'doacao_financeira', 'cartinha', 'aniversario_mh']:
                    formatted_val = "sim" if parse_bool(val) else "não"
                elif key in ['data_ultimo_contato', 'data_roda_conversa']:
                    if val is None or pd.isna(val):
                        formatted_val = ""
                    else:
                        if isinstance(val, (datetime.datetime, datetime.date)):
                            formatted_val = val.strftime('%d/%m/%Y')
                        else:
                            try:
                                formatted_val = pd.to_datetime(val).strftime('%d/%m/%Y')
                            except:
                                formatted_val = str(val)
                else:
                    formatted_val = "" if (pd.isna(val) or val is None) else str(val)
                    
                cells_to_update.append(Cell(row=excel_row, col=col_idx, value=formatted_val))
                
    if cells_to_update:
        try:
            worksheet.update_cells(cells_to_update)
            st.cache_data.clear()
        except Exception as e:
            raise Exception(f"Erro ao salvar alterações no Google Sheets: {e}")

# Add a brand new record to the Google Sheet
def append_google_sheet_row(worksheet, new_record, col_map, original_cols):
    try:
        headers = [str(val).strip() for val in worksheet.row_values(1)]
    except Exception as e:
        headers = [str(col).strip() for col in original_cols]
        
    row_values = [""] * len(headers)
    
    for key, val in new_record.items():
        col_name = col_map.get(key)
        if col_name:
            col_name_strip = col_name.strip()
            if col_name_strip in headers:
                col_idx = headers.index(col_name_strip)
                
                if key == 'agenda_roda':
                    row_values[col_idx] = str(val)
                elif key in ['kit_materiais', 'video_instagram', 'grupo_whatsapp', 'grupo_marinas', 'newsletter', 'contribuir_pautas', 'perfuraid', 'apoio_pf', 'voluntario', 'doacao_financeira', 'cartinha', 'aniversario_mh']:
                    row_values[col_idx] = "sim" if parse_bool(val) else "não"
                else:
                    row_values[col_idx] = "" if (pd.isna(val) or val is None) else str(val)
                    
    # Find the last row containing actual data (ignoring empty lines with formatting)
    try:
        all_values = worksheet.get_all_values()
        last_row = 1
        for idx, row in enumerate(all_values):
            if any(cell.strip() for cell in row):
                last_row = idx + 1
        next_row = last_row + 1
        
        # Write to the first truly empty row (next_row) using A1 notation
        worksheet.update(f"A{next_row}", [row_values])
    except Exception as e:
        # Fallback to standard append_row if there is any issue with get_all_values or update
        worksheet.append_row(row_values)
        
    st.cache_data.clear()

# Load dataset from Google Sheets
result = load_data_from_sheets()

if result[0] is not None:
    df, col_map, original_cols, worksheet = result
    
    # Prepare header / branding
    st.markdown("<h1 style='color: #FF6B00; margin-bottom: 2px;'>🍊 CRM Institucional da Campanha 2026</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='color: #E6007E; font-weight: 500; margin-top: 0px;'>Central de Controle Digital do Time</h3>", unsafe_allow_html=True)
    st.divider()

    # --- SIDEBAR FILTERS ---
    st.sidebar.markdown("<h2 style='color: #FF6B00; text-align: center;'>🔍 Filtros do Mandato</h2>", unsafe_allow_html=True)
    st.sidebar.divider()

    # Operator filter (sidebar - roster updated)
    unique_responsibles_clean = list(OPERATORS.keys()) + ["Outros"]
    
    op_filter = st.sidebar.multiselect(
        "Responsável",
        options=unique_responsibles_clean,
        default=None,
        placeholder="Todos os responsáveis"
    )
    
    # Cardápio de Apoio filter (expanded for all 13 frentes)
    SUPPORT_FILTER_MAP = {
        "Agenda / Roda Temática": "agenda_roda",
        "Kit de Materiais": "kit_materiais",
        "Vídeo de instagram": "video_instagram",
        "Envio de conteúdo em grupos de whatsapp": "grupo_whatsapp",
        "ENTRAR NO GRUPO DAS MARINAS": "grupo_marinas",
        "Newsletter da instituição/região": "newsletter",
        "Contribuir com pautas": "contribuir_pautas",
        "Perfuraid - adesivo de carro": "perfuraid",
        "Apoio na PF": "apoio_pf",
        "Voluntário": "voluntario",
        "Doação Financeira": "doacao_financeira",
        "Cartinha": "cartinha",
        "Aniversário MH": "aniversario_mh"
    }
    
    selected_supports = st.sidebar.multiselect(
        "Cardápio de Apoio",
        options=list(SUPPORT_FILTER_MAP.keys()),
        default=None,
        placeholder="Filtrar por apoios..."
    )

    # Municipalities and regions filter
    muni_col = col_map.get('municipio')
    muni_options = sorted(df[muni_col].dropna().unique()) if muni_col else []
    muni_filter = st.sidebar.multiselect(
        "Município da Instituição",
        options=muni_options,
        placeholder="Todos os municípios"
    )

    # Pauta / Topic filter
    pauta_col = col_map.get('pauta')
    pauta_options = sorted(df[pauta_col].dropna().unique()) if pauta_col else []
    pauta_filter = st.sidebar.multiselect(
        "Pauta",
        options=pauta_options,
        placeholder="Todas as pautas"
    )

    # Status filter
    status_col = col_map.get('status')
    status_options = ["Não Contatado", "Em contato", "Apoio fechado", "Recusou Apoio", "Problemas Técnicos"]
    sheet_statuses = list(df[status_col].dropna().unique()) if status_col else []
    for s in sheet_statuses:
        s_clean = str(s).strip()
        # Case-insensitive exists check to avoid duplicates in the options list
        if s_clean and not any(s_clean.lower() == x.lower() for x in status_options):
            status_options.append(s_clean)
            
    status_filter = st.sidebar.multiselect(
        "Status",
        options=status_options,
        placeholder="Todos os status"
    )
    
    # 🔍 Caixa de Busca Rápida por Texto Livre (EXACT LABEL REQUESTED)
    search_query = st.sidebar.text_input("Ou procure pelo nome do representante/instituição:")

    # Apply Filters to dataframe
    filtered_df = df.copy()
    
    if op_filter:
        filtered_df = filtered_df[filtered_df[col_map['responsavel']].apply(normalize_responsavel).isin(op_filter)]
    
    if muni_filter and muni_col:
        filtered_df = filtered_df[filtered_df[muni_col].isin(muni_filter)]
        
    if pauta_filter and pauta_col:
        filtered_df = filtered_df[filtered_df[pauta_col].isin(pauta_filter)]
        
    if status_filter and status_col:
        filtered_df = filtered_df[filtered_df[status_col].isin(status_filter)]
        
    if selected_supports:
        for support_name in selected_supports:
            key = SUPPORT_FILTER_MAP[support_name]
            col_name = col_map.get(key)
            if col_name and col_name in filtered_df.columns:
                if key == 'agenda_roda':
                    filtered_df = filtered_df[filtered_df[col_name].apply(parse_agenda_count) > 0]
                else:
                    filtered_df = filtered_df[filtered_df[col_name].apply(parse_cardapio_bool) == True]
        
    if search_query.strip():
        q = search_query.strip().lower()
        inst_match = filtered_df[col_map['instituicao']].astype(str).str.lower().str.contains(q, na=False)
        rep_match = filtered_df[col_map['representante']].astype(str).str.lower().str.contains(q, na=False)
        filtered_df = filtered_df[inst_match | rep_match]
        
    if status_col:
        filtered_df[status_col] = filtered_df[status_col].fillna("Não contatado")

    # Tabs
    tab_dashboard, tab_operacional, tab_mapa, tab_cadastro = st.tabs([
        "📊 Painel de Controle", 
        "🔍 Tabela e Detalhes", 
        "🗺️ Mapa do Estado de SP",
        "➕ Cadastrar Nova Instituição"
    ])

    # ------------------ TAB 1: DASHBOARD & METRICS (STRICTLY READ-ONLY) ------------------
    with tab_dashboard:
        st.subheader("📈 Visão Geral Superior e KPIs")
        
        # Define status_col and date_col keys first to prevent NameError
        status_col = col_map.get('status')
        date_col = col_map.get('data_ultimo_contato')
        
        # Define Mapeadas as total lines dynamically
        total_mapeadas = len(df)
        
        # Calculate Contatadas: Status in "em contato", "apoio fechado", "recusou apoio" (stripping and lowercase)
        if status_col and status_col in df.columns:
            status_series = df[status_col].astype(str).str.strip().str.lower()
            is_contacted_series = status_series.isin(["em contato", "apoio fechado", "recusou apoio"])
            total_contatadas = is_contacted_series.sum()
        else:
            is_contacted_series = pd.Series([False] * len(df))
            total_contatadas = 0
            
        progress_ratio = total_contatadas / total_mapeadas if total_mapeadas > 0 else 0.0
        
        # Checklists metrics (recalculated for all 13 cardapio frentes)
        roda_conversa_count = df[col_map['agenda_roda']].apply(parse_agenda_count).sum() if col_map.get('agenda_roda') else 0
        kit_count = df[col_map['kit_materiais']].apply(parse_cardapio_bool).sum() if col_map.get('kit_materiais') else 0
        video_count = df[col_map['video_instagram']].apply(parse_cardapio_bool).sum() if col_map.get('video_instagram') else 0
        whatsapp_count = df[col_map['grupo_whatsapp']].apply(parse_cardapio_bool).sum() if col_map.get('grupo_whatsapp') else 0
        grupo_marinas_count = df[col_map['grupo_marinas']].apply(parse_cardapio_bool).sum() if col_map.get('grupo_marinas') else 0
        newsletter_count = df[col_map['newsletter']].apply(parse_cardapio_bool).sum() if col_map.get('newsletter') else 0
        pautas_count = df[col_map['contribuir_pautas']].apply(parse_cardapio_bool).sum() if col_map.get('contribuir_pautas') else 0
        perfuraid_count = df[col_map['perfuraid']].apply(parse_cardapio_bool).sum() if col_map.get('perfuraid') else 0
        pf_count = df[col_map['apoio_pf']].apply(parse_cardapio_bool).sum() if col_map.get('apoio_pf') else 0
        voluntario_count = df[col_map['voluntario']].apply(parse_cardapio_bool).sum() if col_map.get('voluntario') else 0
        doacao_count = df[col_map['doacao_financeira']].apply(parse_cardapio_bool).sum() if col_map.get('doacao_financeira') else 0
        cartinha_count = df[col_map['cartinha']].apply(parse_cardapio_bool).sum() if col_map.get('cartinha') else 0
        aniversario_mh_count = df[col_map['aniversario_mh']].apply(parse_cardapio_bool).sum() if col_map.get('aniversario_mh') else 0
        
        col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
        with col_kpi1:
            render_metric_card(
                "Mapeadas vs. Contatadas", 
                f"{total_contatadas} / {total_mapeadas}", 
                color="#FF6B00", 
                subtitle=f"Progresso: {progress_ratio*100:.1f}%"
            )
        with col_kpi2:
            render_metric_card(
                "Agendas / Rodas", 
                f"{int(roda_conversa_count)} Agendas", 
                color="#E6007E", 
                subtitle="Soma absoluta (Agenda/Roda temática)"
            )
        with col_kpi3:
            render_metric_card(
                "Kits de Materiais", 
                f"{kit_count} Solicitados", 
                color="#FF6B00", 
                subtitle="Kit de Materiais = SIM"
            )
        with col_kpi4:
            render_metric_card(
                "Apoio PF", 
                f"{pf_count} Confirmados", 
                color="#E6007E", 
                subtitle="Apoio na PF = SIM"
            )
 
        st.write(f"**Progresso Geral ({progress_ratio*100:.1f}%)**")
        st.progress(progress_ratio)
        
        # LOCKED / READ-ONLY SECTION
        st.markdown("### 🔒 Acompanhamento de Produção da Equipe (Apenas Leitura)")
        
        op_names = list(OPERATORS.keys())
        contacts_week = [get_contacts_this_week(df, op, date_col, col_map['responsavel']) for op in op_names]
        
        total_contacts_hist = []
        apoios_fechados_list = []
        for op in op_names:
            op_mask = df[col_map['responsavel']].apply(normalize_responsavel) == op
            op_df = df[op_mask]
            
            op_contacted = is_contacted_series[op_mask].sum()
            total_contacts_hist.append(op_contacted)
            
            apoios_sum = 0
            for _, row in op_df.iterrows():
                apoios_sum += get_row_apoios_count(row, col_map)
            apoios_fechados_list.append(apoios_sum)
            
        metas_df = pd.DataFrame({
            'Responsável': op_names,
            'Contatos Realizados nesta Semana': contacts_week,
            'Número de Apoios Fechados': apoios_fechados_list,
            'Total Contatos (Histórico)': total_contacts_hist
        })
        
        st.dataframe(
            metas_df,
            hide_index=True,
            use_container_width=True
        )
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.markdown("#### Apoios Fechados por Responsável")
            chart_apoios = pd.DataFrame({'Apoios Fechados': apoios_fechados_list}, index=op_names)
            st.bar_chart(chart_apoios, color="#FF6B00")
        with col_c2:
            st.markdown("#### Contatos Realizados na Semana")
            chart_contacts = pd.DataFrame({'Contatos Realizados': contacts_week}, index=op_names)
            st.bar_chart(chart_contacts, color="#E6007E")
        
        st.markdown("### 📊 Volumes do Cardápio Político (Histórico)")
        
        # Plotly horizontal bar chart for the 13 frentes (High-End UX)
        frentes_labels = [
            "Agendas/Rodas", "Kits de Materiais", "Vídeos Instagram", "Grupos WhatsApp",
            "Grupo das Marinas", "Newsletter", "Contribuir Pautas", "Perfuraid (Adesivos)",
            "Apoios PF", "Voluntários", "Doações Financeiras", "Cartinha", "Aniversário MH"
        ]
        frentes_volumes = [
            int(roda_conversa_count), int(kit_count), int(video_count), int(whatsapp_count),
            int(grupo_marinas_count), int(newsletter_count), int(pautas_count), int(perfuraid_count),
            int(pf_count), int(voluntario_count), int(doacao_count), int(cartinha_count), int(aniversario_mh_count)
        ]
        df_volumes = pd.DataFrame({
            'Frente': frentes_labels,
            'Volume': frentes_volumes
        }).sort_values(by='Volume', ascending=True)
        
        fig_frentes = px.bar(
            df_volumes,
            x='Volume',
            y='Frente',
            orientation='h',
            color='Volume',
            color_continuous_scale=['#FF6B00', '#E6007E'],
            text='Volume',
            title='Volume Total por Frente do Cardápio de Apoio'
        )
        fig_frentes.update_layout(
            height=460,
            margin=dict(l=0, r=0, t=30, b=0),
            coloraxis_showscale=False
        )
        st.plotly_chart(fig_frentes, use_container_width=True)
        
        st.markdown("#### Detalhamento das 13 Frentes")
        row1_cols = st.columns(7)
        with row1_cols[0]:
            render_metric_card("Agendas/Rodas", f"{int(roda_conversa_count)}", "#FF6B00")
        with row1_cols[1]:
            render_metric_card("Kits Materiais", f"{kit_count}", "#E6007E")
        with row1_cols[2]:
            render_metric_card("Vídeos Insta", f"{video_count}", "#FF6B00")
        with row1_cols[3]:
            render_metric_card("Grupos Zap", f"{whatsapp_count}", "#E6007E")
        with row1_cols[4]:
            render_metric_card("Grupo Marinas", f"{grupo_marinas_count}", "#FF6B00")
        with row1_cols[5]:
            render_metric_card("Newsletters", f"{newsletter_count}", "#E6007E")
        with row1_cols[6]:
            render_metric_card("Cartinha", f"{cartinha_count}", "#FF6B00")
            
        row2_cols = st.columns(6)
        with row2_cols[0]:
            render_metric_card("Aniversário MH", f"{aniversario_mh_count}", "#E6007E")
        with row2_cols[1]:
            render_metric_card("Contribuir Pautas", f"{pautas_count}", "#FF6B00")
        with row2_cols[2]:
            render_metric_card("Perfuraid", f"{perfuraid_count}", "#E6007E")
        with row2_cols[3]:
            render_metric_card("Apoios PF", f"{pf_count}", "#FF6B00")
        with row2_cols[4]:
            render_metric_card("Voluntários", f"{voluntario_count}", "#E6007E")
        with row2_cols[5]:
            render_metric_card("Doações", f"{doacao_count}", "#FF6B00")

        # WhatsApp Summary Generator (read-only trigger)
        st.divider()
        st.markdown("### 💬 Gerador de Resumo para WhatsApp")
        selected_wa_op = st.selectbox("Selecione o Responsável para gerar o balanço semanal:", options=op_names, key="wa_op_selectbox")
        
        if st.button("Gerar Relatório WhatsApp", key="wa_report_btn"):
            today = datetime.date.today()
            start_of_week = today - datetime.timedelta(days=today.weekday())
            end_of_week = start_of_week + datetime.timedelta(days=6)
            
            op_mask = df[col_map['responsavel']].apply(normalize_responsavel) == selected_wa_op
            op_df = df[op_mask]
            
            valid_dates = pd.to_datetime(op_df[date_col]).dropna()
            this_week_mask = (valid_dates.dt.date >= start_of_week) & (valid_dates.dt.date <= end_of_week)
            op_df_week = op_df.loc[valid_dates[this_week_mask].index]
            
            contatos_semana = len(op_df_week)
            
            agendas_sem = op_df_week[col_map['agenda_roda']].apply(parse_agenda_count).sum() if col_map.get('agenda_roda') else 0
            kits_sem = op_df_week[col_map['kit_materiais']].apply(parse_cardapio_bool).sum() if col_map.get('kit_materiais') else 0
            videos_sem = op_df_week[col_map['video_instagram']].apply(parse_cardapio_bool).sum() if col_map.get('video_instagram') else 0
            wa_sem = op_df_week[col_map['grupo_whatsapp']].apply(parse_cardapio_bool).sum() if col_map.get('grupo_whatsapp') else 0
            marinas_sem = op_df_week[col_map['grupo_marinas']].apply(parse_cardapio_bool).sum() if col_map.get('grupo_marinas') else 0
            news_sem = op_df_week[col_map['newsletter']].apply(parse_cardapio_bool).sum() if col_map.get('newsletter') else 0
            pautas_sem = op_df_week[col_map['contribuir_pautas']].apply(parse_cardapio_bool).sum() if col_map.get('contribuir_pautas') else 0
            perfuraid_sem = op_df_week[col_map['perfuraid']].apply(parse_cardapio_bool).sum() if col_map.get('perfuraid') else 0
            pf_sem = op_df_week[col_map['apoio_pf']].apply(parse_cardapio_bool).sum() if col_map.get('apoio_pf') else 0
            voluntario_sem = op_df_week[col_map['voluntario']].apply(parse_cardapio_bool).sum() if op_df_week.get(col_map.get('voluntario')) is not None else 0
            doacao_sem = op_df_week[col_map['doacao_financeira']].apply(parse_cardapio_bool).sum() if col_map.get('doacao_financeira') else 0
            cartinha_sem = op_df_week[col_map['cartinha']].apply(parse_cardapio_bool).sum() if col_map.get('cartinha') else 0
            aniversario_sem = op_df_week[col_map['aniversario_mh']].apply(parse_cardapio_bool).sum() if col_map.get('aniversario_mh') else 0
            
            apoios_sem_sum = (agendas_sem + kits_sem + videos_sem + wa_sem + marinas_sem + 
                              news_sem + pautas_sem + perfuraid_sem + pf_sem + voluntario_sem + doacao_sem + cartinha_sem + aniversario_sem)
            
            total_op_mapeadas = len(op_df)
            total_op_contatadas = is_contacted_series[op_mask].sum()
            total_op_apoios = sum(get_row_apoios_count(row, col_map) for _, row in op_df.iterrows())
            
            summary_text = f"""*🍊 Relatório Semanal - CRM Campanha 2026*
*Responsável:* {selected_wa_op}
*Período:* {start_of_week.strftime('%d/%m/%Y')} a {end_of_week.strftime('%d/%m/%Y')}

*📈 Balanço de Produção:*
- Contatos realizados nesta semana: {contatos_semana}
- Total de apoios fechados nesta semana: {int(apoios_sem_sum)}

*📋 Detalhamento dos Apoios da Semana:*
- Agendas/Rodas temáticas: {int(agendas_sem)}
- Kits de Materiais: {kits_sem}
- Gravação de Vídeos: {videos_sem}
- Grupos de WhatsApp: {wa_sem}
- Entrar no grupo das Marinas: {marinas_sem}
- Newsletters da região: {news_sem}
- Contribuir com pautas: {pautas_sem}
- Perfuraid (Adesivos): {perfuraid_sem}
- Apoios PF: {pf_sem}
- Voluntários: {voluntario_sem}
- Doações: {doacao_sem}
- Cartinhas: {cartinha_sem}
- Aniversário MH: {aniversario_sem}

*📊 Produção Histórica:*
- Total de Instituições Mapeadas: {total_op_mapeadas}
- Total de Instituições Contatadas: {total_op_contatadas}
- Total de Apoios Fechados (Histórico): {int(total_op_apoios)}"""
            
            st.text_area("Copiável:", value=summary_text, height=300)
            st.info("💡 Copie o texto acima e envie no grupo do mandato!")


    # ------------------ TAB 2: OPERATIONAL TABLE & DETAIL CARD (CENTRALIZED EDITING) ------------------
    with tab_operacional:
        filtered_df["Alerta de Contato"] = filtered_df[col_map['data_ultimo_contato']].apply(get_contact_alert)
        
        display_columns = [
            col_map['instituicao'],
            col_map['representante'],
            col_map['telefone'],
            col_map['municipio'],
            col_map['endereco'],
            col_map['responsavel'],
            col_map['status'],
            col_map['pauta'],
            col_map['data_ultimo_contato'],
            col_map['data_roda_conversa'],
            "Alerta de Contato"
        ]
        display_columns = [c for c in display_columns if c is not None]
        
        st.markdown("### 📋 Planilha Operacional")
        
        col_grid_ctrl1, col_grid_ctrl2 = st.columns([1, 1])
        with col_grid_ctrl1:
            bulk_mode = st.checkbox("Ativar Modo Edição Direta na Grade (st.data_editor)", value=False, key="operacional_bulk_mode")
        with col_grid_ctrl2:
            towrite = io_bytes = None
            try:
                import io
                towrite = io.BytesIO()
                with pd.ExcelWriter(towrite, engine='openpyxl') as writer:
                    filtered_df[display_columns].to_excel(writer, index=False, sheet_name='Filtro_CRM')
                io_bytes = towrite.getvalue()
                
                st.download_button(
                    label="📥 Baixar Planilha Filtrada (.xlsx)",
                    data=io_bytes,
                    file_name="CRM_Filtrado.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="operacional_download"
                )
            except Exception as e:
                st.write("Erro ao preparar download:", e)

        if not bulk_mode:
            col_table, col_details = st.columns([3, 2])
            
            with col_table:
                st.info("💡 Clique em uma linha na tabela para carregar os detalhes do registro no painel lateral.")
                
                selection = st.dataframe(
                    filtered_df[display_columns],
                    on_select="rerun",
                    selection_mode="single-row",
                    use_container_width=True,
                    hide_index=False,
                    key="crm_dataframe_v3"
                )
                
                selected_idx = None
                rows_selected = selection.get("selection", {}).get("rows", [])
                if rows_selected:
                    selected_idx = filtered_df.index[rows_selected[0]]
                    
                selected_idx_alt = st.selectbox(
                    "Selecione um registro para detalhamento:",
                    options=filtered_df.index,
                    format_func=lambda idx: f"{filtered_df.loc[idx, col_map['instituicao']]} - {filtered_df.loc[idx, col_map['representante']]}",
                    index=None,
                    placeholder="Buscar registro...",
                    key="operacional_selectbox_v3"
                )
                
                if selected_idx_alt is not None:
                    selected_idx = selected_idx_alt
                    
            with col_details:
                st.markdown("### 📇 Painel de Detalhes da Instituição")
                if selected_idx is not None:
                    record = df.loc[selected_idx]
                    
                    st.markdown(f"""
                    <div style="
                        background-color: #F9FAFB;
                        border-radius: 12px;
                        padding: 16px;
                        border: 1px solid #E5E7EB;
                    ">
                        <h4 style="color: #FF6B00; margin-bottom: 5px;">{record[col_map['instituicao']]}</h4>
                        <span style="font-size: 0.8rem; color: #6B7280;">Representante: {record[col_map['representante']]}</span>
                        <br/>
                        <span style="font-size: 0.8rem; font-weight: bold; color: #E6007E;">Alert: {get_contact_alert(record[col_map['data_ultimo_contato']])}</span>
                    </div>
                    """, unsafe_allow_html=True)
                    st.write("")
                    
                    with st.form("detalhes_registro_form_v3"):
                        st.subheader("Informações Básicas")
                        new_rep = st.text_input("Nome do contato (Nome e Sobrenome)", value=str(record[col_map['representante']]) if not pd.isna(record[col_map['representante']]) else "")
                        new_phone = st.text_input("Telefone do contato", value=str(record[col_map['telefone']]) if not pd.isna(record[col_map['telefone']]) else "")
                        new_muni = st.text_input("Município", value=str(record[col_map['municipio']]) if not pd.isna(record[col_map['municipio']]) else "")
                        new_endereco = st.text_input("Endereço", value=str(record[col_map['endereco']]) if not pd.isna(record[col_map['endereco']]) else "")
                        new_pauta = st.text_input("Pauta", value=str(record[col_map['pauta']]) if not pd.isna(record[col_map['pauta']]) else "")
                        new_instagram = st.text_input("Instagram", value=str(record[col_map['instagram']]) if not pd.isna(record[col_map['instagram']]) else "")
                        
                        orig_col = col_map.get('origem')
                        new_origem = st.text_input("Origem da Instituição", value=str(record[orig_col]) if orig_col and not pd.isna(record[orig_col]) else "")
                        
                        st.divider()
                        st.subheader("Filtros e Responsável")
                        
                        status_default_idx = 0
                        try:
                            status_default_idx = status_options.index(record[col_map['status']])
                        except:
                            status_default_idx = 0
                        new_status = st.selectbox("Status", options=status_options, index=status_default_idx)
                        
                        resp_options = list(OPERATORS.keys()) + ["Outros"]
                        current_resp = normalize_responsavel(record[col_map['responsavel']])
                        resp_default_idx = 0
                        try:
                            resp_default_idx = resp_options.index(current_resp)
                        except:
                            resp_default_idx = len(resp_options) - 1
                        new_resp = st.selectbox("Responsável", options=resp_options, index=resp_default_idx)
                        
                        curr_date = record[col_map['data_ultimo_contato']]
                        default_date = None
                        if not pd.isna(curr_date):
                            default_date = pd.to_datetime(curr_date).date()
                        new_date = st.date_input("Data do Último Contato", value=default_date)
                        
                        curr_roda_date = record[col_map['data_roda_conversa']]
                        default_roda_date = None
                        if not pd.isna(curr_roda_date):
                            default_roda_date = pd.to_datetime(curr_roda_date).date()
                        new_roda_date = st.date_input("Data da Roda de Conversa", value=default_roda_date)
                        
                        st.divider()
                        st.subheader("Histórico de Contatos")
                        curr_hist = str(record[col_map['historico']]) if not pd.isna(record[col_map['historico']]) else ""
                        st.text_area("Histórico Completo", value=curr_hist, disabled=True, height=100)
                        
                        new_log_text = st.text_area("Adicionar novo contato ao Histórico:")
                        append_log = st.checkbox("Confirmar adição de histórico")
                        
                        st.divider()
                        st.subheader("Checklist do Cardápio Político")
                        
                        agenda_options = ["NÃO", "SIM", "SIM - 1 agenda", "SIM - 2 agendas", "SIM - 3 agendas", "SIM - 4 agendas"]
                        curr_agenda_val = str(record.get(col_map['agenda_roda'], "")).strip()
                        agenda_default_idx = 0
                        for idx, opt in enumerate(agenda_options):
                            if opt.upper() == curr_agenda_val.upper():
                                agenda_default_idx = idx
                                break
                            elif idx == 1 and curr_agenda_val.upper() in ['TRUE', '1', '1.0']:
                                agenda_default_idx = 1
                            elif idx == 0 and curr_agenda_val.upper() in ['FALSE', '0', '0.0']:
                                agenda_default_idx = 0
                                
                        new_agenda_val = st.selectbox("1. Agenda / Roda Temática (AC)", options=agenda_options, index=agenda_default_idx)
                        
                        chk_kit = st.checkbox("2. Kit de Materiais (AD)", value=parse_cardapio_bool(record.get(col_map.get('kit_materiais'))))
                        chk_video = st.checkbox("3. Vídeo de instagram (AE)", value=parse_cardapio_bool(record.get(col_map.get('video_instagram'))))
                        chk_whatsapp = st.checkbox("4. Envio de conteúdo em grupos de whatsapp (AF)", value=parse_cardapio_bool(record.get(col_map.get('grupo_whatsapp'))))
                        chk_marinas = st.checkbox("5. ENTRAR NO GRUPO DAS MARINAS (AG)", value=parse_cardapio_bool(record.get(col_map.get('grupo_marinas'))))
                        chk_newsletter = st.checkbox("6. Newsletter da instituição/região (AH)", value=parse_cardapio_bool(record.get(col_map.get('newsletter'))))
                        chk_pautas = st.checkbox("7. Contribuir com pautas (AI)", value=parse_cardapio_bool(record.get(col_map.get('contribuir_pautas'))))
                        chk_perfuraid = st.checkbox("8. Perfuraid - adesivo de carro (AJ)", value=parse_cardapio_bool(record.get(col_map.get('perfuraid'))))
                        chk_pf = st.checkbox("9. Apoio na PF (AK)", value=parse_cardapio_bool(record.get(col_map.get('apoio_pf'))))
                        chk_voluntario = st.checkbox("10. Voluntário (AL)", value=parse_cardapio_bool(record.get(col_map.get('voluntario'))))
                        chk_doacao = st.checkbox("11. Doação Financeira (AM)", value=parse_cardapio_bool(record.get(col_map.get('doacao_financeira'))))
                        chk_cartinha = st.checkbox("12. Cartinha (AN)", value=parse_cardapio_bool(record.get(col_map.get('cartinha'))))
                        chk_aniversario = st.checkbox("13. Aniversário MH (AO)", value=parse_cardapio_bool(record.get(col_map.get('aniversario_mh'))))
                        
                        prev_addr_val = str(record.get(col_map.get('endereco_kit_cartinha'), "")).strip() if col_map.get('endereco_kit_cartinha') and not pd.isna(record.get(col_map.get('endereco_kit_cartinha'))) else ""
                        has_prev_address = prev_addr_val != ""
                        
                        new_addr_kit_cartinha = ""
                        if chk_kit or chk_cartinha or has_prev_address:
                            new_addr_kit_cartinha = st.text_input(
                                "Endereço para Receber o Kit/Cartinha",
                                value=prev_addr_val,
                                placeholder="Ex: Rua/Avenida, número, Complemento/Apto, Bairro, CEP, Cidade - UF",
                                help="Preencha o endereço completo para o envio de Kits ou Cartinhas"
                            )
                            
                        new_outros_apoios = st.text_input(
                            "Outros Apoios (AP)",
                            value=str(record.get(col_map.get('outros_apoios'), "")) if col_map.get('outros_apoios') and not pd.isna(record.get(col_map.get('outros_apoios'))) else ""
                        )
                        
                        submit_btn = st.form_submit_button("💾 Salvar Alterações no Registro")
                        
                        if submit_btn:
                            updates = {
                                'representante': new_rep,
                                'telefone': new_phone,
                                'municipio': new_muni,
                                'endereco': new_endereco,
                                'pauta': new_pauta,
                                'instagram': new_instagram,
                                'status': new_status,
                                'responsavel': new_resp if new_resp != "Outros" else record[col_map['responsavel']],
                                'data_ultimo_contato': new_date,
                                'data_roda_conversa': new_roda_date,
                                'agenda_roda': new_agenda_val,
                                'kit_materiais': chk_kit,
                                'video_instagram': chk_video,
                                'grupo_whatsapp': chk_whatsapp,
                                'grupo_marinas': chk_marinas,
                                'newsletter': chk_newsletter,
                                'contribuir_pautas': chk_pautas,
                                'perfuraid': chk_perfuraid,
                                'apoio_pf': chk_pf,
                                'voluntario': chk_voluntario,
                                'doacao_financeira': chk_doacao,
                                'cartinha': chk_cartinha,
                                'aniversario_mh': chk_aniversario,
                                'outros_apoios': new_outros_apoios,
                                'endereco_kit_cartinha': new_addr_kit_cartinha
                            }
                            
                            if col_map.get('origem'):
                                updates['origem'] = new_origem
                            
                            if append_log and new_log_text.strip() != "":
                                today_str = datetime.date.today().strftime("%d/%m/%y")
                                log_entry = f"{today_str} - {new_log_text.strip()}"
                                if curr_hist:
                                    updates['historico'] = f"{log_entry} | {curr_hist}"
                                else:
                                    updates['historico'] = log_entry
                                    
                            try:
                                update_google_sheet_row(worksheet, selected_idx, updates, col_map, original_cols)
                                st.success("Registro atualizado com sucesso no Google Sheets!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao salvar: {e}")
                else:
                    st.info("Selecione uma linha na tabela ao lado para visualizar e editar os detalhes no formulário.")

        else:
            # Bulk edit mode in st.data_editor
            st.warning("⚠️ Modo de Edição Direta na Grade. Edite os valores e clique no botão abaixo para salvar no Google Sheets.")
            
            editable_cols_grid = [
                col_map['instituicao'],
                col_map['representante'],
                col_map['telefone'],
                col_map['municipio'],
                col_map['endereco'],
                col_map['responsavel'],
                col_map['status'],
                col_map['pauta'],
                col_map['data_ultimo_contato'],
                col_map['data_roda_conversa'],
                col_map['agenda_roda'],
                col_map['kit_materiais'],
                col_map['video_instagram'],
                col_map['grupo_whatsapp'],
                col_map['grupo_marinas'],
                col_map['newsletter'],
                col_map['contribuir_pautas'],
                col_map['perfuraid'],
                col_map['apoio_pf'],
                col_map['voluntario'],
                col_map['doacao_financeira'],
                col_map['cartinha'],
                col_map['aniversario_mh'],
                col_map['outros_apoios'],
                col_map['endereco_kit_cartinha']
            ]
            editable_cols_grid = [c for c in editable_cols_grid if c is not None]
            
            agenda_opts = ["NÃO", "SIM", "SIM - 1 agenda", "SIM - 2 agendas", "SIM - 3 agendas", "SIM - 4 agendas"]
            
            # Setup columns configs safely checking if columns mapped exist
            col_configs = {}
            if col_map.get('status'): col_configs[col_map['status']] = st.column_config.SelectboxColumn("Status", options=status_options)
            if col_map.get('responsavel'): col_configs[col_map['responsavel']] = st.column_config.SelectboxColumn("Responsável", options=list(OPERATORS.keys()) + ["Outros"])
            if col_map.get('data_ultimo_contato'): col_configs[col_map['data_ultimo_contato']] = st.column_config.DateColumn("Último Contato")
            if col_map.get('data_roda_conversa'): col_configs[col_map['data_roda_conversa']] = st.column_config.DateColumn("Roda Conversa")
            if col_map.get('agenda_roda'): col_configs[col_map['agenda_roda']] = st.column_config.SelectboxColumn("Agenda/Roda", options=agenda_opts)
            if col_map.get('kit_materiais'): col_configs[col_map['kit_materiais']] = st.column_config.CheckboxColumn("Kits")
            if col_map.get('video_instagram'): col_configs[col_map['video_instagram']] = st.column_config.CheckboxColumn("Vídeo Insta")
            if col_map.get('grupo_whatsapp'): col_configs[col_map['grupo_whatsapp']] = st.column_config.CheckboxColumn("Envio Zap")
            if col_map.get('grupo_marinas'): col_configs[col_map['grupo_marinas']] = st.column_config.CheckboxColumn("Grupo Marinas")
            if col_map.get('newsletter'): col_configs[col_map['newsletter']] = st.column_config.CheckboxColumn("Newsletter")
            if col_map.get('contribuir_pautas'): col_configs[col_map['contribuir_pautas']] = st.column_config.CheckboxColumn("Pautas")
            if col_map.get('perfuraid'): col_configs[col_map['perfuraid']] = st.column_config.CheckboxColumn("Perfuraid")
            if col_map.get('apoio_pf'): col_configs[col_map['apoio_pf']] = st.column_config.CheckboxColumn("Apoio PF")
            if col_map.get('voluntario'): col_configs[col_map['voluntario']] = st.column_config.CheckboxColumn("Voluntário")
            if col_map.get('doacao_financeira'): col_configs[col_map['doacao_financeira']] = st.column_config.CheckboxColumn("Doação")
            if col_map.get('cartinha'): col_configs[col_map['cartinha']] = st.column_config.CheckboxColumn("Cartinha")
            if col_map.get('aniversario_mh'): col_configs[col_map['aniversario_mh']] = st.column_config.CheckboxColumn("Aniversário MH")
            if col_map.get('outros_apoios'): col_configs[col_map['outros_apoios']] = st.column_config.TextColumn("Outros Apoios")
            if col_map.get('endereco_kit_cartinha'): col_configs[col_map['endereco_kit_cartinha']] = st.column_config.TextColumn("Endereço Kit/Cartinha")
            
            edited_df = st.data_editor(
                filtered_df[editable_cols_grid],
                column_config=col_configs,
                use_container_width=True,
                hide_index=False,
                key="crm_grid_editor_v3"
            )
            
            if st.button("💾 Salvar Alterações da Grade no Google Sheets", key="grid_save_btn_v3"):
                changes_made = 0
                error_count = 0
                for idx in edited_df.index:
                    original_row = df.loc[idx]
                    edited_row = edited_df.loc[idx]
                    
                    row_updates = {}
                    for col in editable_cols_grid:
                        val_orig = original_row[col]
                        val_new = edited_row[col]
                        
                        is_diff = False
                        if pd.isna(val_orig) and pd.isna(val_new):
                            is_diff = False
                        elif pd.isna(val_orig) or pd.isna(val_new):
                            is_diff = True
                        elif col in [col_map.get('kit_materiais'), col_map.get('video_instagram'), col_map.get('grupo_whatsapp'), 
                                     col_map.get('grupo_marinas'), col_map.get('newsletter'), col_map.get('contribuir_pautas'), 
                                     col_map.get('perfuraid'), col_map.get('apoio_pf'), col_map.get('voluntario'), col_map.get('doacao_financeira'),
                                     col_map.get('cartinha'), col_map.get('aniversario_mh')]:
                            is_diff = parse_cardapio_bool(val_orig) != parse_cardapio_bool(val_new)
                        elif isinstance(val_orig, (datetime.datetime, datetime.date)) or isinstance(val_new, (datetime.datetime, datetime.date)):
                            is_diff = pd.to_datetime(val_orig) != pd.to_datetime(val_new)
                        else:
                            is_diff = str(val_orig).strip() != str(val_new).strip()
                            
                        if is_diff:
                            std_key = None
                            for k, v in col_map.items():
                                if v == col:
                                    std_key = k
                                    break
                            if std_key:
                                row_updates[std_key] = val_new
                                
                    if row_updates:
                        try:
                            update_google_sheet_row(worksheet, idx, row_updates, col_map, original_cols)
                            changes_made += 1
                        except:
                            error_count += 1
                            
                if changes_made > 0:
                    st.success(f"{changes_made} registro(s) salvo(s) com sucesso no Google Sheets!")
                    if error_count > 0:
                        st.error(f"Erro ao salvar {error_count} registro(s).")
                    st.rerun()
                elif error_count > 0:
                    st.error(f"Erro ao salvar registros.")
                else:
                    st.info("Nenhuma alteração detectada.")


    # ------------------ TAB 3: INTERACTIVE MAP (READ-ONLY) ------------------
    with tab_mapa:
        st.subheader("🗺️ Mapa Interativo do Estado de São Paulo")
        st.info("Pins coloridos por Responsável. Os filtros laterais também se aplicam a esta visualização.")
        
        map_df = filtered_df.copy()
        
        lats = []
        lons = []
        muni_col = col_map['municipio']
        
        for _, row in map_df.iterrows():
            city = row.get(muni_col)
            lat, lon = get_city_coords(city)
            lats.append(lat)
            lons.append(lon)
            
        map_df["lat"] = lats
        map_df["lon"] = lons
        
        map_df["Responsável Oficial"] = map_df[col_map['responsavel']].apply(normalize_responsavel)
        
        px_color_map = {op: OPERATORS[op]['color'] for op in OPERATORS}
        px_color_map['Outros'] = '#9CA3AF'
        
        fig = px.scatter_mapbox(
            map_df,
            lat="lat",
            lon="lon",
            color="Responsável Oficial",
            color_discrete_map=px_color_map,
            hover_name=col_map['instituicao'],
            hover_data={
                col_map['representante']: True,
                col_map['status']: True,
                col_map['pauta']: True,
                'lat': False,
                'lon': False
            },
            zoom=6.5,
            center={"lat": -23.5505, "lon": -46.6333},
            height=600
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend=dict(
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)"
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)


    # ------------------ TAB 4: CADASTRO ------------------
    with tab_cadastro:
        st.subheader("➕ Formulário de Cadastro de Nova Entidade/Liderança")
        
        # Enforce standard status vocabulary for new registrations
        status_select_options = [""] + ["Não Contatado", "Em contato", "Apoio fechado", "Recusou Apoio", "Problemas Técnicos"]
        
        pauta_col = col_map.get('pauta')
        pauta_options_unique = []
        if pauta_col and pauta_col in df.columns:
            pauta_options_unique = sorted(list(set(str(x).strip() for x in df[pauta_col].dropna().unique() if str(x).strip())))
        pauta_select_options = [""] + pauta_options_unique
        
        with st.form("nova_instituicao_form_v3"):
            st.info("Preencha os dados para registrar um novo contato no CRM.")
            new_inst_name = st.text_input("Nome da Instituição", placeholder="Ex: Associação de Bairro")
            new_rep_name = st.text_input("Nome do Representante", placeholder="Ex: João da Silva")
            new_rep_phone = st.text_input("Telefone de Contato", placeholder="Ex: 11987071760")
            new_muni = st.text_input("Município", placeholder="Ex: Campinas")
            
            new_pauta_select = st.selectbox("Pauta de Interesse (Opcional)", options=pauta_select_options, index=0)
            new_status_select = st.selectbox("Status da Instituição (Opcional)", options=status_select_options, index=0)
            new_origem = st.text_input("Origem da Instituição", placeholder="Ex: Evento Municipal")
            
            new_resp_name = st.selectbox(
                "Responsável Atribuído", 
                options=["Não atribuído"] + list(OPERATORS.keys()) + ["Outros"],
                key="cadastro_resp_selectbox"
            )
            
            new_historico = st.text_area("Histórico / Contexto do Primeiro Contato:", placeholder="Ex: 05/08/26 - Conheceu o mandato no evento municipal.")
            
            submit_cadastro = st.form_submit_button("Salvar Nova Instituição")
            
            if submit_cadastro:
                if not new_inst_name.strip() and not new_rep_name.strip():
                    st.error("Erro: Você deve preencher o nome da instituição ou do representante!")
                else:
                    new_record = {
                        'instituicao': new_inst_name.strip(),
                        'representante': new_rep_name.strip(),
                        'telefone': new_rep_phone.strip(),
                        'municipio': new_muni.strip(),
                        'pauta': new_pauta_select.strip() if new_pauta_select else "",
                        'responsavel': new_resp_name if new_resp_name != "Não atribuído" else None,
                        'status': new_status_select.strip() if new_status_select else "",
                        'historico': new_historico.strip(),
                        'agenda_roda': "NÃO",
                        'kit_materiais': False,
                        'video_instagram': False,
                        'grupo_whatsapp': False,
                        'grupo_marinas': False,
                        'newsletter': False,
                        'contribuir_pautas': False,
                        'perfuraid': False,
                        'apoio_pf': False,
                        'voluntario': False,
                        'doacao_financeira': False,
                        'cartinha': False,
                        'aniversario_mh': False,
                        'outros_apoios': "",
                        'endereco_kit_cartinha': ""
                    }
                    if col_map.get('origem'):
                        new_record['origem'] = new_origem.strip()
                    
                    try:
                        append_google_sheet_row(worksheet, new_record, col_map, original_cols)
                        st.success("Nova instituição cadastrada com sucesso no Google Sheets!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao cadastrar: {e}")
                        st.text(traceback.format_exc())
else:
    # ⚠️ Display warning if secrets are not configured (Outstanding UX)
    st.warning("⚠️ Planilha e Credenciais do Google Sheets não configuradas!")
    st.info("Por favor, preencha o arquivo `.streamlit/secrets.toml` com suas credenciais do GCP e ID da Planilha para habilitar o aplicativo.")
    st.markdown("""
    ### ⚙️ Como Configurar as Credenciais:
    1. Crie uma conta de serviço (Service Account) no **Google Cloud Console**.
    2. Crie uma chave JSON para a Service Account e insira os valores no arquivo local `.streamlit/secrets.toml`.
    3. Compartilhe sua planilha do Google Drive com o e-mail da conta de serviço como **Editora**.
    4. Adicione o ID da Planilha na chave `spreadsheet_id` do secrets.
    """)
