import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

# --- CONFIGURACIÓN DE SEGURIDAD ---
# Nota: Reemplaza con tu Token real solo en tu computador local. 
# No subas tu Token real a repositorios públicos.
TOKEN = 'TU_TOKEN_DE_TELEGRAM_AQUI' 
bot = telebot.TeleBot(TOKEN)

# Configuración de Google Sheets API
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
cliente = gspread.authorize(creds)
doc = cliente.open("BaseDatos_Finanzas")

# Variable para confirmar el borrado de datos
esperando_confirmacion = {}

def obtener_hoja_mes():
    """Obtiene o crea la pestaña del mes actual (ej: 03-2026)"""
    nombre_mes = datetime.now().strftime("%m-%Y")
    try:
        return doc.worksheet(nombre_mes)
    except:
        nueva = doc.add_worksheet(title=nombre_mes, rows="1000", cols="5")
        nueva.append_row(["Fecha", "Categoría", "Concepto", "Valor"])
        return nueva

@bot.message_handler(commands=['utilidades', 'resumen'])
def comando_utilidades(message):
    """Calcula el balance financiero real leyendo los datos de Google Sheets"""
    try:
        hoja = obtener_hoja_mes()
        registros = hoja.get_all_values()
        jhon, des, gas = 0, 0, 0
        
        for fila in registros[1:]:
            if len(fila) < 4: continue
            try:
                val = float(fila[3].replace(',', '.'))
                cat = fila[1]
                if val < 0: gas += abs(val)
                elif cat == "JHON": jhon += val
                elif cat == "DESIGNTER": des += val
            except: continue
            
        total_ing = jhon + des
        utilidad = total_ing - gas
        
        resumen = (
            f"📊 *BALANCE DESIGNTER*\n\n"
            f"👤 *Jhon:* `${jhon:,.0f}`\n"
            f"🚀 *Designter:* `${des:,.0f}`\n"
            f"🔻 *Gastos:* `${gas:,.0f}`\n"
            f"──────────────────\n"
            f"📈 *Utilidad Neta:* `${utilidad:,.0f}`"
        )
        bot.reply_to(message, resumen, parse_mode='Markdown')
    except Exception as e:
        bot.reply_to(message, "❌ Error al calcular los datos.")

@bot.message_handler(func=lambda m: True)
def procesar_texto(message):
    """Procesamiento de Lenguaje Natural para extraer montos y categorías"""
    if message.text.startswith('/'): return
    
    try:
        texto = message.text.lower()
        # Extraer solo números usando RegEx
        numeros = re.findall(r'\d+', texto.replace('.', ''))
        if not numeros: return
        valor = float(numeros[0])
        
        # Lógica de categorización automática
        if "gasto" in texto or "gaste" in texto:
            cat = "GASTO"
            valor_final = -valor
        elif "designter" in texto:
            cat = "DESIGNTER"
            valor_final = valor
        else:
            cat = "JHON"
            valor_final = valor

        hoja = obtener_hoja_mes()
        hoja.append_row([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), cat, message.text, valor_final])
        bot.reply_to(message, f"✅ *{cat}* guardado: `${valor:,.0f}`")
    except Exception as e:
        print(f"Error en registro: {e}")

# Comandos de mantenimiento (Borrado seguro)
@bot.message_handler(commands=['borrartodo'])
def solicitar_borrado(message):
    esperando_confirmacion[message.chat.id] = True
    bot.reply_to(message, "⚠️ *ADVERTENCIA:* ¿Borrar los datos del mes?\nEscribe /confirmar.")

@bot.message_handler(commands=['confirmar'])
def confirmar_borrado(message):
    if esperando_confirmacion.get(message.chat.id):
        hoja = obtener_hoja_mes()
        hoja.batch_clear(['A2:E1000'])
        bot.reply_to(message, "✅ Datos borrados. Balance en ceros.")
        esperando_confirmacion[message.chat.id] = False

print("Bot de Designter: Versión para Repositorio Lista.")
bot.infinity_polling()
