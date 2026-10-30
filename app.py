import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import paho.mqtt.client as paho
import json
import platform

# Configuración de la página
st.set_page_config(
    page_title="Interfaces Multimodales - Control por Voz",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Estilos CSS personalizados con paleta de tonos azules modernos
st.markdown("""
    <style>
    .stApp {
        background-color: #F8FAFC;
        color: #1E293B;
    }
    h1, h2, h3 {
        color: #0F172A !important;
        font-family: 'Inter', sans-serif;
    }
    [data-testid="stSidebar"] {
        background-color: #1E293B;
        color: #FFFFFF;
    }
    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] span, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label {
        color: #E2E8F0 !important;
    }
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
    }
    .response-box {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #3B82F6;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# Callbacks MQTT
def on_publish(client, userdata, result):
    print("El dato ha sido publicado con éxito \n")

def on_message(client, userdata, message):
    try:
        message_received = str(message.payload.decode("utf-8"))
        st.info(f"Mensaje del Broker: {message_received}")
    except Exception as e:
        st.error(f"Error al leer mensaje: {e}")

# Configuración del Broker MQTT
broker = "broker.mqttdashboard.com"
port = 1883

# Sidebar de información y entorno
with st.sidebar:
    st.subheader("⚙️ Configuración")
    st.markdown(f"**Broker:** `{broker}`")
    st.markdown(f"**Puerto:** `{port}`")
    st.markdown(f"**Python:** `{platform.python_version()}`")
    st.markdown("---")
    st.info("💡 **Tip:** Asegúrate de dar permisos de micrófono en tu navegador al hacer clic en el botón de inicio.")

# Título y presentación (Modificado para quitar "mediante MQTT")
st.title("🎙️ Interfaces Multimodales")
st.subheader("Control por Voz")

# Carga de imagen segura (evita que se rompa si el archivo no existe en GitHub)
try:
    image = Image.open('voice_ctrl.jpg')
    st.image(image, width=250)
except Exception:
    st.warning("⚠️ No se encontró la imagen 'voice_ctrl.jpg' en el repositorio.")

st.markdown("---")
st.write("### 🗣️ Asistente de Voz")
st.write("Haz clic en el botón inferior, habla claro y tu comando se enviará automáticamente al broker MQTT.")

# Botón Bokeh para reconocimiento de voz del navegador
stt_button = Button(label="🎙️ Iniciar Reconocimiento", width=220, button_type="success")

stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = "es-ES";
 
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
    """))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

# Procesar resultado de la voz y publicar en MQTT
if result:
    if "GET_TEXT" in result:
        spoken_text = result.get("GET_TEXT")
        st.markdown(f'<div class="response-box"><b>Texto reconocido:</b> "{spoken_text}"</div>', unsafe_allow_html=True)
        
        try:
            # Inicializar cliente MQTT con versión de API compatible
            client1 = paho.Client(client_id="GIT-HUBC-VOICE", callback_api_version=paho.CallbackAPIVersion.VERSION1)
            client1.on_message = on_message
            client1.on_publish = on_publish
            
            client1.connect(broker, port, 60)
            client1.loop_start()
            
            payload = json.dumps({"Act1": spoken_text.strip()})
            client1.publish("voice_ctrl", payload)
            
            time.sleep(1)
            client1.loop_stop()
            client1.disconnect()
            
            st.success("✅ ¡Comando de voz publicado exitosamente en el tópico `voice_ctrl`!")
        except Exception as e:
            st.error(f"❌ Error al conectar o publicar en MQTT: {e}")

# Crear directorio temporal

# Crear directorio temporal de forma segura
try:
    os.mkdir("temp")
except Exception:
    pass
