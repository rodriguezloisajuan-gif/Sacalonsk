from flask import Flask, send_file, render_template_string, abort, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import secrets
import os
import io
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

TOKEN = "8854497322:AAE1IsRJRInUo2EDpWkZNxOoby3B--4cWq0"
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")  # Cambiar en producción
UPLOAD_FOLDER = Path("videos_temp")
UPLOAD_FOLDER.mkdir(exist_ok=True)

# ============ BASE DE DATOS ============

class FileDatabase:
    def __init__(self):
        self.files = {}
    
    def create_file(self, file_id, file_name, file_size, duration=None):
        """Crea entrada para el archivo"""
        token = secrets.token_hex(12)  # Token de 24 caracteres
        
        self.files[token] = {
            'file_id': file_id,
            'file_name': file_name,
            'file_size': file_size,
            'duration': duration,
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24),
            'downloads': 0,
            'views': 0
        }
        logger.info(f"Archivo creado: {token} - {file_name}")
        return token
    
    def get_file(self, token):
        """Obtiene archivo si es válido"""
        if token not in self.files:
            return None
        
        file_info = self.files[token]
        
        # Verificar expiración
        if datetime.now() > file_info['expires_at']:
            self.delete_file(token)
            return None
        
        return file_info
    
    def delete_file(self, token):
        """Elimina archivo expirado"""
        if token in self.files:
            del self.files[token]
            logger.info(f"Archivo eliminado: {token}")
    
    def cleanup_expired(self):
        """Limpia archivos expirados"""
        expired = [
            token for token, info in self.files.items()
            if datetime.now() > info['expires_at']
        ]
        for token in expired:
            self.delete_file(token)
        
        if expired:
            logger.info(f"Limpieza: {len(expired)} archivos expirados eliminados")
    
    @staticmethod
    def get_human_size(bytes_size):
        """Convierte bytes a formato legible"""
        for unit in ['B', 'KiB', 'MiB', 'GiB']:
            if bytes_size < 1024:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024
        return f"{bytes_size:.1f} TiB"

db = FileDatabase()
tg_app = None

# ============ TELEGRAM BOT ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start"""
    args = context.args
    
    # Si viene de compartir archivo
    if args and args[0].startswith('file_'):
        token = args[0].replace('file_', '')
        file_info = db.get_file(token)
        
        if not file_info:
            await update.message.reply_text("❌ Enlace expirado o no encontrado")
            return
        
        await show_file_info(update, token, file_info)
        return
    
    # Mensaje de bienvenida
    welcome_text = """
🎬 *Sacalonsk - Bot de Descargas* 

Envía un **video o archivo** y recibirás:
✅ Enlace de descarga directo
✅ Reproductor online
✅ Link para compartir en Telegram

_Los archivos se eliminan en 24 horas_

Soportados: Videos (MP4, MKV, WebM), Audio (MP3, WAV, M4A), Documentos
    """
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /help"""
    help_text = """
📚 *Comandos Disponibles*

/start - Inicia el bot
/help - Muestra esta ayuda
/stats - Estadísticas del bot

*Cómo usar:*
1️⃣ Envía un archivo o video
2️⃣ Recibe los enlaces
3️⃣ Descarga o reproduce online
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa archivos y videos"""
    message = update.message
    
    # Determinar tipo de archivo
    file_obj = None
    file_name = None
    file_size = None
    duration = None
    
    if message.video:
        file_obj = message.video
        file_name = message.video.file_name or f"video_{message.video.file_id}.mp4"
        file_size = message.video.file_size
        duration = message.video.duration
    elif message.document:
        file_obj = message.document
        file_name = message.document.file_name
        file_size = message.document.file_size
    elif message.audio:
        file_obj = message.audio
        file_name = message.audio.file_name or f"audio_{message.audio.file_id}.mp3"
        file_size = message.audio.file_size
        duration = message.audio.duration
    else:
        await message.reply_text("❌ Tipo de archivo no soportado")
        return
    
    # Validar tamaño
    if file_size > 2.5 * 1024 * 1024 * 1024:  # 2.5GB
        await message.reply_text("❌ Archivo muy grande (máximo 2.5 GB)")
        return
    
    # Mensaje de procesamiento
    processing_msg = await message.reply_text("⏳ Procesando archivo...")
    
    try:
        # Crear entrada en base de datos
        token = db.create_file(
            file_id=file_obj.file_id,
            file_name=file_name,
            file_size=file_size,
            duration=duration
        )
        
        # Mensajes de enlace
        download_link = f"{BASE_URL}/dl/{token}"
        watch_link = f"{BASE_URL}/watch/{token}"
        share_link = f"https://t.me/Sacalonsk_bot?start=file_{token}"
        
        # Formato de respuesta
        response_text = f"""
📂 Fɪʟᴇ ɴᴀᴍᴇ : {file_name}

📦 Fɪʟᴇ ꜱɪᴢᴇ : {db.get_human_size(file_size)}

📥 Dᴏᴡɴʟᴏᴀᴅ : {download_link}

🖥 Wᴀᴛᴄʜ : {watch_link}

🔗 Sʜᴀʀᴇ : {share_link}
        """
        
        # Botones interactivos
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("📥 Descargar", url=download_link),
                InlineKeyboardButton("🖥 Ver", url=watch_link)
            ],
            [
                InlineKeyboardButton("🔗 Compartir", url=share_link)
            ]
        ])
        
        await processing_msg.delete()
        await message.reply_text(response_text, reply_markup=keyboard)
        
    except Exception as e:
        logger.error(f"Error procesando archivo: {str(e)}")
        await processing_msg.delete()
        await message.reply_text(f"❌ Error: {str(e)}")

async def show_file_info(update, token, file_info):
    """Muestra info del archivo compartido"""
    response_text = f"""
📂 Fɪʟᴇ ɴᴀᴍᴇ : {file_info['file_name']}

📦 Fɪʟᴇ ꜱɪᴢᴇ : {db.get_human_size(file_info['file_size'])}

📥 Dᴏᴡɴʟᴏᴀᴅ : {BASE_URL}/dl/{token}

🖥 Wᴀᴛᴄʜ : {BASE_URL}/watch/{token}
    """
    
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📥 Descargar", url=f"{BASE_URL}/dl/{token}"),
            InlineKeyboardButton("🖥 Ver", url=f"{BASE_URL}/watch/{token}")
        ]
    ])
    
    await update.message.reply_text(response_text, reply_markup=keyboard)

# ============ SERVIDOR FLASK ============

@app.route('/')
def index():
    """Página principal"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sacalonsk - Bot de Descargas</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; }
            body { font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; }
            .container { background: white; padding: 40px; border-radius: 10px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.2); max-width: 500px; }
            h1 { color: #333; margin-bottom: 20px; }
            p { color: #666; margin-bottom: 15px; }
            .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 10px 5px; }
            .button:hover { background: #764ba2; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Sacalonsk</h1>
            <p>Bot de descargas para Telegram</p>
            <p>Envía videos, audios o archivos y obtén enlaces temporales</p>
            <a href="https://t.me/Sacalonsk_bot" class="button">Abrir Bot</a>
            <a href="/stats" class="button">Estadísticas</a>
        </div>
    </body>
    </html>
    """

@app.route('/dl/<token>')
def download_file(token):
    """Descarga directo del archivo"""
    file_info = db.get_file(token)
    
    if not file_info:
        return """
        <html>
        <body style="text-align:center; padding:50px; font-family:Arial;">
            <h1>❌ Enlace Expirado</h1>
            <p>Este enlace ha caducado. Solicita uno nuevo al bot.</p>
        </body>
        </html>
        """, 404
    
    try:
        # Descargar de Telegram bajo demanda
        file = asyncio.run(tg_app.bot.get_file(file_info['file_id']))
        file_bytes = asyncio.run(file.download_as_bytearray())
        
        # Actualizar contador
        file_info['downloads'] += 1
        logger.info(f"Descarga: {token} - Descargas: {file_info['downloads']}")
        
        return send_file(
            io.BytesIO(file_bytes),
            as_attachment=True,
            download_name=file_info['file_name'],
            mimetype='application/octet-stream'
        )
    
    except Exception as e:
        logger.error(f"Error descargando: {str(e)}")
        return f"❌ Error al descargar: {str(e)}", 500

@app.route('/watch/<token>')
def watch_file(token):
    """Reproductor online"""
    file_info = db.get_file(token)
    
    if not file_info:
        return """
        <html>
        <body style="text-align:center; padding:50px; font-family:Arial;">
            <h1>❌ Enlace Expirado</h1>
        </body>
        </html>
        """, 404
    
    file_info['views'] += 1
    logger.info(f"Vista: {token} - Vistas: {file_info['views']}")
    
    # Detectar tipo de archivo
    file_name = file_info['file_name'].lower()
    
    # Para videos
    if file_name.endswith(('.mp4', '.mkv', '.webm', '.avi', '.mov')):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{file_info['file_name']}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                * {{ margin: 0; padding: 0; }}
                body {{ background: #000; font-family: Arial; }}
                .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
                video {{ width: 100%; border-radius: 8px; }}
                .info {{ color: #fff; margin-top: 20px; padding: 20px; background: rgba(255,255,255,0.1); border-radius: 8px; }}
                .info h2 {{ margin-bottom: 10px; }}
                .button {{ 
                    display: inline-block; 
                    margin-top: 10px; 
                    padding: 10px 20px; 
                    background: #0088cc; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px; 
                    margin-right: 10px;
                }}
                .button:hover {{ background: #0066aa; }}
            </style>
        </head>
        <body>
            <div class="container">
                <video controls autoplay>
                    <source src="/stream/{token}" type="video/mp4">
                    Tu navegador no soporta video HTML5
                </video>
                
                <div class="info">
                    <h2>📹 {file_info['file_name']}</h2>
                    <p>📦 Tamaño: {db.get_human_size(file_info['file_size'])}</p>
                    <a href="/dl/{token}" class="button">📥 Descargar</a>
                    <a href="https://t.me/Sacalonsk_bot" class="button">🤖 Bot</a>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    # Para audio
    elif file_name.endswith(('.mp3', '.wav', '.m4a', '.aac', '.flac')):
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{file_info['file_name']}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: Arial; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }}
                .container {{ max-width: 500px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }}
                audio {{ width: 100%; margin: 20px 0; }}
                .info {{ color: #333; }}
                .button {{ 
                    display: inline-block; 
                    padding: 10px 20px; 
                    background: #667eea; 
                    color: white; 
                    text-decoration: none; 
                    border-radius: 5px;
                    margin-right: 10px;
                }}
                .button:hover {{ background: #764ba2; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🎵 {file_info['file_name']}</h2>
                <audio controls>
                    <source src="/stream/{token}" type="audio/mpeg">
                </audio>
                <div class="info">
                    <p>📦 Tamaño: {db.get_human_size(file_info['file_size'])}</p>
                    <a href="/dl/{token}" class="button">📥 Descargar</a>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    else:
        return f"""
        <html>
        <body style="padding:20px; font-family:Arial;">
            <h2>📄 {file_info['file_name']}</h2>
            <p>Este tipo de archivo no se puede reproducir online.</p>
            <a href="/dl/{token}">📥 Descargar archivo</a>
        </body>
        </html>
        """

@app.route('/stream/<token>')
def stream_file(token):
    """Streaming del archivo"""
    file_info = db.get_file(token)
    
    if not file_info:
        abort(404)
    
    try:
        file = asyncio.run(tg_app.bot.get_file(file_info['file_id']))
        file_bytes = asyncio.run(file.download_as_bytearray())
        
        return send_file(
            io.BytesIO(file_bytes),
            mimetype='video/mp4'
        )
    except Exception as e:
        logger.error(f"Error en streaming: {str(e)}")
        abort(500)

@app.route('/stats')
def stats():
    """Estadísticas del bot"""
    total_files = len(db.files)
    total_downloads = sum(f['downloads'] for f in db.files.values())
    total_views = sum(f['views'] for f in db.files.values())
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Estadísticas - Sacalonsk</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: Arial; padding: 20px; background: #f0f0f0; }}
            .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 5px 15px rgba(0,0,0,0.1); }}
            h1 {{ color: #333; margin-bottom: 30px; text-align: center; }}
            .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
            .stat-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
            .stat-number {{ font-size: 32px; font-weight: bold; }}
            .stat-label {{ font-size: 14px; margin-top: 10px; opacity: 0.8; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Estadísticas de Sacalonsk</h1>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-number">{total_files}</div>
                    <div class="stat-label">Archivos Activos</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{total_downloads}</div>
                    <div class="stat-label">Descargas Totales</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">{total_views}</div>
                    <div class="stat-label">Vistas Online</div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/api/stats')
def api_stats():
    """API de estadísticas en JSON"""
    return jsonify({
        'total_files': len(db.files),
        'total_downloads': sum(f['downloads'] for f in db.files.values()),
        'total_views': sum(f['views'] for f in db.files.values()),
        'timestamp': datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return """
    <html>
    <body style="text-align:center; padding:50px; font-family:Arial;">
        <h1>404 - No Encontrado</h1>
        <p>El recurso que buscas no existe.</p>
        <a href="/">Volver al inicio</a>
    </body>
    </html>
    """, 404

# ============ INICIALIZACIÓN ============

def init_telegram():
    """Inicializa el bot de Telegram"""
    global tg_app
    
    tg_app = Application.builder().token(TOKEN).build()
    
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("help", help_command))
    tg_app.add_handler(MessageHandler(filters.VIDEO | filters.Document.ALL | filters.AUDIO, handle_file))
    
    # Limpiar archivos expirados cada hora
    job_queue = tg_app.job_queue
    job_queue.run_repeating(
        lambda ctx: db.cleanup_expired(),
        interval=3600,
        first=0
    )
    
    # Ejecutar bot en thread
    import threading
    bot_thread = threading.Thread(target=tg_app.run_polling, daemon=True)
    bot_thread.start()
    logger.info("Bot de Telegram iniciado")

if __name__ == "__main__":
    init_telegram()
    logger.info(f"Servidor iniciado en {BASE_URL}")
    app.run(host='0.0.0.0', port=int(os.getenv("PORT", 5000)), debug=False)
