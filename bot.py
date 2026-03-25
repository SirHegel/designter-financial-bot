import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

# --- CONFIGURACIÓN ---
TOKEN = '8704256465:AAEmiTFuw5PmZ1PODKDzO3ssLcHA45DN660'
bot = telebot.TeleBot(TOKEN)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credenciales.json", scope)
cliente = gspread.authorize(creds)
doc = cliente.open("BaseDatos_Finanzas")

# Variable temporal para confirmar borrado
esperando_confirmacion = {}

def obtener_hoja_mes():
    nombre_mes = datetime.now().strftime("%m-%Y")
    try:
        return doc.worksheet(nombre_mes)
    except:
        nueva = doc.add_worksheet(title=nombre_mes, rows="1000", cols="5")
        nueva.append_row(["Fecha", "Categoría", "Concepto", "Valor"])
        return nueva

# --- COMANDO PARA REINICIAR TODO ---
@bot.message_handler(commands=['borrartodo'])
def solicitar_borrado(message):
    esperando_confirmacion[message.chat.id] = True
    bot.reply_to(message, "⚠️ *¿ESTÁS SEGURO?*\nEsto borrará TODOS los ingresos y gastos de este mes.\n\nEscribe /confirmar para proceder o cualquier otra cosa para cancelar.", parse_mode='Markdown')

@bot.message_handler(commands=['confirmar'])
def confirmar_borrado(message):
    if esperando_confirmacion.get(message.chat.id):
        try:
            hoja = obtener_hoja_mes()
            # Borra desde la fila 2 hasta la 1000
            range_to_clear = 'A2:E1000'
            hoja.batch_clear([range_to_clear])
            
            bot.reply_to(message, "✅ *Hoja limpiada.* Designter y Jhon empiezan de cero hoy.", parse_mode='Markdown')
            esperando_confirmacion[message.chat.id] = False
        except Exception as e:
            bot.reply_to(message, f"❌ Error al limpiar: {e}")
    else:
        bot.reply_to(message, "No hay ninguna acción de borrado pendiente.")

# --- COMANDO DE UTILIDADES ---
@bot.message_handler(commands=['utilidades', 'resumen'])
def comando_utilidades(message):
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
            f"📊 *BALANCE DE CEROS*\n\n"
            f"👤 *Jhon:* `${jhon:,.0f}`\n"
            f"🚀 *Designter:* `${des:,.0f}`\n"
            f"🔻 *Gastos:* `${gas:,.0f}`\n"
            f"──────────────────\n"
            f"📈 *Utilidad Neta:* `${utilidad:,.0f}`"
        )
        bot.reply_to(message, resumen, parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ Error al calcular.")

# --- PROCESADOR DE TEXTO ---
@bot.message_handler(func=lambda m: True)
def procesar_texto(message):
    if message.text.startswith('/'): return
    try:
        texto = message.text.lower()
        numeros = re.findall(r'\d+', texto.replace('.', ''))
        if not numeros: return
        valor = float(numeros[0])
        
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
    except: pass

print("Bot de Designter: Función de reinicio activada.")
bot.infinity_polling()