import streamlit as st
import requests
from datetime import datetime
from streamlit_geolocation import streamlit_geolocation

# --- CONFIGURAÇÕES DE PÁGINA E CSS ---
st.set_page_config(page_title="WeatherDash Pro", page_icon="🌤️", layout="wide")

st.markdown("""
<style>
    /* Cartão Base Premium */
    .weather-card { padding: 20px; border-radius: 12px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-family: sans-serif; height: 100%; position: relative; overflow: hidden; background-size: 200% 200%; }
    .content-layer { position: relative; z-index: 2; }

    @keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

    .anim-sun { background-image: linear-gradient(-45deg, #00c6ff, #0072ff); color: white; text-shadow: 1px 1px 3px rgba(0,0,0,0.3); animation: gradientShift 8s ease infinite; }
    .anim-night { background-image: linear-gradient(-45deg, #0f2027, #203a43, #2c5364); color: white; text-shadow: 1px 1px 3px rgba(0,0,0,0.8); animation: gradientShift 10s ease infinite; }
    .anim-cloud { background-image: linear-gradient(-45deg, #757f9a, #d7dde8); color: #333; text-shadow: 1px 1px 2px rgba(255,255,255,0.6); animation: gradientShift 10s ease infinite; }
    .anim-rain { background-image: linear-gradient(-45deg, #2b4162, #1a2a6c, #3a4b66); color: white; text-shadow: 1px 1px 3px rgba(0,0,0,0.6); animation: gradientShift 6s ease infinite; }
    .anim-fog { background-image: linear-gradient(-45deg, #bdc3c7, #2c3e50); color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.8); animation: gradientShift 10s ease infinite; }
    .anim-storm { background-image: linear-gradient(-45deg, #141e30, #243b55, #0a0f18); color: white; text-shadow: 1px 1px 3px rgba(0,0,0,0.8); border: 1px solid #ff4b4b; animation: gradientShift 4s ease infinite; }
    .anim-storm::after { content: ''; position: absolute; top: 0; left: 0; right: 0; bottom: 0; background-color: white; opacity: 0; animation: safeFlash 5s infinite; pointer-events: none; z-index: 1; }
    @keyframes safeFlash { 0%, 94%, 98%, 100% { opacity: 0; } 95%, 99% { opacity: 0.4; } }

    .weather-title { font-size: 1.5rem; font-weight: bold; margin-bottom: 10px; }
    .weather-detail { font-size: 1.1rem; margin: 5px 0; display: flex; align-items: center; gap: 8px;}
    .hourly-container { display: flex; overflow-x: auto; gap: 15px; padding: 10px 5px; margin-top: 15px; border-top: 1px solid rgba(255, 255, 255, 0.3); align-items: flex-start;}
    .hourly-container::-webkit-scrollbar { height: 6px; }
    .hourly-container::-webkit-scrollbar-thumb { background-color: rgba(0,0,0,0.2); border-radius: 10px; }
    .hourly-item-details { background: rgba(255, 255, 255, 0.15); border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 10px; padding: 8px 5px; min-width: 70px; cursor: pointer; transition: all 0.2s ease; }
    .hourly-item-details[open] { background: rgba(0, 0, 0, 0.5); min-width: 120px; }
    .hourly-summary { list-style: none; display: flex; flex-direction: column; align-items: center; outline: none; }
    .hourly-summary::-webkit-details-marker { display: none; }
    .hourly-time { font-weight: bold; margin-bottom: 5px; font-size: 0.95rem; }
    .hourly-icon { font-size: 1.5rem; margin-bottom: 5px; }
    .hourly-temp { font-weight: bold; font-size: 0.95rem; }
    .hourly-rain { font-size: 0.8rem; color: #ffeb3b; font-weight: bold; text-shadow: none; background: rgba(0,0,0,0.4); padding: 2px 5px; border-radius: 4px; margin-top: 5px;}
    .hourly-extra { margin-top: 10px; padding-top: 10px; border-top: 1px dashed rgba(255, 255, 255, 0.4); font-size: 0.85rem; display: flex; flex-direction: column; gap: 4px; text-align: center; }
</style>
""", unsafe_allow_html=True)

WEATHER_API_BASE = "https://api.open-meteo.com/v1/forecast"

def get_weather_visuals(code, is_day=True):
    if is_day:
        wmo_map = { 0: ("☀️", "Céu limpo", "anim-sun"), 1: ("🌤️", "Maiormente claro", "anim-sun"), 2: ("⛅", "Parcialmente nublado", "anim-cloud"), 3: ("☁️", "Nublado", "anim-cloud"), 45: ("🌫️", "Neblina", "anim-fog"), 48: ("🌫️", "Neblina com geada", "anim-fog"), 51: ("🌧️", "Chuvisco leve", "anim-rain"), 53: ("🌧️", "Chuvisco moderado", "anim-rain"), 61: ("🌧️", "Chuva leve", "anim-rain"), 63: ("🌧️", "Chuva moderada", "anim-rain"), 65: ("🌧️", "Chuva forte", "anim-rain"), 80: ("🌦️", "Pancadas de chuva", "anim-rain"), 81: ("🌦️", "Pancadas moderadas", "anim-rain"), 82: ("⛈️", "Pancadas violentas", "anim-storm"), 95: ("⛈️", "Tempestade (Alerta)", "anim-storm"), 96: ("🌩️", "Tempestade com granizo", "anim-storm"), 99: ("🌩️", "Tempestade severa", "anim-storm") }
    else:
        wmo_map = { 0: ("🌙", "Céu limpo", "anim-night"), 1: ("☁️", "Maiormente claro", "anim-night"), 2: ("☁️", "Parcialmente nublado", "anim-cloud"), 3: ("☁️", "Nublado", "anim-cloud"), 45: ("🌫️", "Neblina", "anim-fog"), 48: ("🌫️", "Neblina com geada", "anim-fog"), 51: ("🌧️", "Chuvisco leve", "anim-rain"), 53: ("🌧️", "Chuvisco moderado", "anim-rain"), 61: ("🌧️", "Chuva leve", "anim-rain"), 63: ("🌧️", "Chuva moderada", "anim-rain"), 65: ("🌧️", "Chuva forte", "anim-rain"), 80: ("🌧️", "Pancadas de chuva", "anim-rain"), 81: ("🌧️", "Pancadas moderadas", "anim-rain"), 82: ("⛈️", "Pancadas violentas", "anim-storm"), 95: ("⛈️", "Tempestade (Alerta)", "anim-storm"), 96: ("🌩️", "Tempestade com granizo", "anim-storm"), 99: ("🌩️", "Tempestade severa", "anim-storm") }
    return wmo_map.get(code, ("🌡️", "Desconhecido", "anim-cloud" if is_day else "anim-night"))

@st.cache_data(ttl=900)
def get_coordinates(query):
    try:
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"
        headers = {'User-Agent': 'WeatherDashPro/1.0'}
        response = requests.get(url, headers=headers)
        data = response.json()
        if data: return { "latitude": float(data[0]["lat"]), "longitude": float(data[0]["lon"]), "full_address": data[0]["display_name"] }
        return None
    except: return None

@st.cache_data(ttl=900)
def get_address_from_coords(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
        headers = {'User-Agent': 'WeatherDashPro/1.0'}
        response = requests.get(url, headers=headers)
        data = response.json()
        address = data.get("address", {})
        city = address.get("city", address.get("town", address.get("village", address.get("suburb", ""))))
        state = address.get("state", "")
        if city and state: return f"{city} - {state}"
        return data.get("display_name", f"Coordenadas: {lat:.4f}, {lon:.4f}")
    except: return f"Coordenadas: {lat:.4f}, {lon:.4f}"

@st.cache_data(ttl=900)
def get_weather_data(lat, lon):
    try:
        url = f"{WEATHER_API_BASE}?latitude={lat}&longitude={lon}&current_weather=true&hourly=temperature_2m,precipitation_probability,weathercode,windspeed_10m,relative_humidity_2m&daily=temperature_2m_max,temperature_2m_min,weathercode,precipitation_probability_max,windspeed_10m_max&timezone=auto"
        response = requests.get(url)
        return response.json()
    except: return None

# --- UI PRINCIPAL ---
st.title("🌤️ WeatherDash Pro")
st.caption("Dashboard Técnico: Monitoramento Dinâmico de Segurança")
st.markdown("---")

# --- ÁREA DE BUSCA EXPLÍCITA ---
col_search, col_btn = st.columns([3, 1])

with col_search:
    st.write("🔍 **Pesquisa Manual (Bairro, Cidade ou UF):**")
    search_query = st.text_input("Busca", placeholder="Ex: Mangabeira, João Pessoa", label_visibility="collapsed")

with col_btn:
    st.write("🎯 **Capturar GPS Exato:**")
    # O plugin cria o botão logo abaixo deste texto
    geo_data = streamlit_geolocation()

st.markdown("---")
# ------------------------------

lat, lon, full_address = None, None, None

# Lógica de decisão: O GPS tem prioridade se o botão for clicado
if geo_data and geo_data.get('latitude') is not None:
    lat, lon = geo_data['latitude'], geo_data['longitude']
    full_address = f"Meu Local Atual: {get_address_from_coords(lat, lon)}"
elif search_query:
    with st.spinner("Buscando endereço no satélite..."):
        city_data = get_coordinates(search_query)
        if city_data:
            lat, lon, full_address = city_data["latitude"], city_data["longitude"], city_data["full_address"]
        else:
            st.warning("Localização não encontrada pelo texto. Tente usar o botão de GPS.")

# Renderização do Clima
if lat and lon:
    with st.spinner("Sincronizando radares..."):
        weather_data = get_weather_data(lat, lon)
        if weather_data:
            st.success(f"📍 **{full_address}**")
            current, daily = weather_data["current_weather"], weather_data["daily"]
            
            c_is_day = current.get("is_day", 1) == 1
            c_temp, c_wind = round(current["temperature"]), round(current["windspeed"])
            c_icon, c_desc, c_class = get_weather_visuals(current["weathercode"], c_is_day)
            
            col1, col2 = st.columns([1, 1.5])
            with col1:
                current_html = f"""<div class="weather-card {c_class}"><div class="content-layer"><div class="weather-title">Agora: {c_icon} {c_desc}</div><div class="weather-detail">🌡️ Temperatura: {c_temp} °C</div><div class="weather-detail">💨 Vento: {c_wind} km/h</div><br><p style='font-size:0.8rem; border-top: 1px solid rgba(255,255,255,0.3); padding-top:10px;'>Coordenadas: {lat:.4f}, {lon:.4f}</p></div></div>"""
                st.markdown(current_html, unsafe_allow_html=True)
            with col2:
                map_html = f"""<div style='border-radius: 12px; overflow: hidden; border: 2px solid #e2e8f0;'><iframe width='100%' height='260' src='https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=mm&metricTemp=C&metricWind=km/h&zoom=11&overlay=radar&product=radar&level=surface&lat={lat}&lon={lon}&detailLat={lat}&detailLon={lon}&marker=true' frameborder='0'></iframe></div>"""
                st.markdown(map_html, unsafe_allow_html=True)
            
            st.divider()
            st.subheader("📅 Previsão Dinâmica Semanal")
            hourly = weather_data["hourly"]
            
            for i in range(len(daily["time"])):
                date_obj = datetime.strptime(daily["time"][i], "%Y-%m-%d")
                date_str = date_obj.strftime("%d/%m")
                max_t, min_t = round(daily["temperature_2m_max"][i]), round(daily["temperature_2m_min"][i])
                wind_max, rain_prob_daily = round(daily["windspeed_10m_max"][i]), daily["precipitation_probability_max"][i]
                w_icon, w_desc, w_class = get_weather_visuals(daily["weathercode"][i], True)
                
                with st.expander(f"{date_str}  |  {w_icon} {w_desc}  |  Máx: {max_t}°C"):
                    start_idx, end_idx, hourly_items = i * 24, (i * 24) + 24, ""
                    end_idx = min(end_idx, len(hourly["time"])) 
                    
                    for h in range(start_idx, end_idx):
                        t_str = hourly["time"][h].split("T")[1]
                        h_hour = int(t_str.split(":")[0])
                        h_is_day = 6 <= h_hour < 18 
                        
                        h_t, h_r, h_w = round(hourly["temperature_2m"][h]), hourly["precipitation_probability"][h], round(hourly["windspeed_10m"][h])
                        h_hum, (h_ic, h_de, _) = round(hourly["relative_humidity_2m"][h]), get_weather_visuals(hourly["weathercode"][h], h_is_day)
                        r_tag = f'<div class="hourly-rain">💧 {h_r}%</div>' if h_r > 0 else ''
                        
                        hourly_items += f'<details class="hourly-item-details"><summary class="hourly-summary"><div class="hourly-time">{t_str}</div><div class="hourly-icon">{h_ic}</div><div class="hourly-temp">{h_t}°C</div>{r_tag}</summary><div class="hourly-extra"><div><strong>{h_de}</strong></div><div>💨 {h_w} km/h</div><div>💦 {h_hum}% UR</div></div></details>'
                    
                    detail_html = f'<div class="weather-card {w_class}"><div class="content-layer"><div class="weather-title">{w_icon} {w_desc}</div><div class="weather-detail">🌡️ Máx: <b>{max_t}°C</b> | Mín: <b>{min_t}°C</b></div><div class="weather-detail">💨 Rajadas: <b>{wind_max} km/h</b></div><p style="margin-top:15px; font-size:0.9rem; font-weight:bold;">Previsão por Hora (Clique para detalhes):</p><div class="hourly-container">{hourly_items}</div></div></div>'
                    st.markdown(detail_html, unsafe_allow_html=True)
                    
                    if "storm" in w_class or rain_prob_daily > 70: 
                        st.warning("⚠️ Alerta de Segurança Operacional: Evitar trabalho em altura/campo aberto.")
        else: st.error("Erro na comunicação com a API de Clima.")

st.divider()
st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.8rem; padding: 10px;'><strong>🛡️ Monitoramento:</strong> OpenStreetMap, ECMWF & GFS | <strong>📡 Radar:</strong> Windy API.<br><em>Uso Interno - Protocolo de Segurança do Trabalho.</em></div>", unsafe_allow_html=True)