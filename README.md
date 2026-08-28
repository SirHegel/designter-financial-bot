# 🚀 Designter Financial Bot

Asistente de Telegram para registrar ingresos y gastos en Google Sheets, separar
movimientos personales y empresariales y consultar el balance mensual.

## Seguridad primero

El bot no contiene credenciales en el código. Arranca únicamente cuando recibe
por variables de entorno:

- `TELEGRAM_BOT_TOKEN`: token vigente creado en BotFather.
- `TELEGRAM_ALLOWED_CHAT_IDS`: uno o varios IDs de chat autorizados, separados
  por comas. También admite los IDs negativos usados por grupos.
- `GOOGLE_SERVICE_ACCOUNT_JSON`: objeto JSON completo de una cuenta de servicio.
- `GOOGLE_SHEETS_DOCUMENT`: nombre del documento; el valor predeterminado es
  `BaseDatos_Finanzas`.

Los chats que no estén en la lista permitida no pueden leer, registrar ni borrar
datos. Los errores de servicios externos tampoco imprimen credenciales ni el
contenido financiero en los registros del proceso.

> [!IMPORTANT]
> El repositorio conserva una alerta por un token de Telegram publicado en un
> commit histórico. Retirarlo del código actual no invalida la credencial. Su
> propietario debe revocarlo en BotFather, generar otro y guardarlo únicamente
> en el entorno local. La alerta debe permanecer abierta hasta confirmar esa
> rotación.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Completa `.env` en tu equipo. Para servicios desplegados, guarda
`GOOGLE_SERVICE_ACCOUNT_JSON` directamente en el almacén de secretos de la
plataforma. Para una ejecución local puedes cargar un archivo ignorado sin
imprimir su contenido:

```bash
set -a
source .env
set +a
export GOOGLE_SERVICE_ACCOUNT_JSON="$(jq -c . credenciales.json)"
```

La cuenta de servicio debe tener acceso al documento indicado. Arranca el bot
después de cargar la configuración:

```bash
python bot.py
```

Se requiere Python 3.10 o superior. El programa valida primero todas las
variables y el formato JSON. Si falta algo, termina sin conectarse a Telegram o
Google. La representación de la configuración oculta tanto el token como la
cuenta de servicio para evitar filtrarlos accidentalmente en registros.

## Pruebas

Las pruebas usan valores sintéticos y un archivo temporal; no necesitan ninguna
credencial real ni realizan solicitudes de red.

```bash
python -m unittest discover -v
python -m compileall -q bot.py settings.py tests
```

## Funciones

- Categorización de ingresos personales, ingresos de Designter y gastos.
- Registro en una pestaña mensual de Google Sheets.
- Resumen de ingresos, gastos y utilidad neta.
- Borrado mensual con confirmación y limitado a chats autorizados.

## Respuesta a una exposición

1. Revoca el token expuesto desde la conversación autenticada con BotFather.
2. Genera un token nuevo y actualiza solo `TELEGRAM_BOT_TOKEN` en `.env` o en el
   almacén de secretos de tu plataforma.
3. Revisa los registros y sesiones del bot durante el periodo de exposición.
4. Confirma que el token anterior ya no funciona.
5. Solo entonces resuelve la alerta de secret scanning como revocada.

Nunca publiques el token, el JSON de la cuenta de servicio ni capturas que los
contengan en issues, PRs, registros o mensajes de soporte.

---

Proyecto desarrollado por Jhon Steven Alvarez Ruiz — CEO de Designter.
