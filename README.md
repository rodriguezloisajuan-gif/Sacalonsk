# 🎬 Sacalonsk - Bot de Descargas para Telegram

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-v6.0-blue.svg)](https://core.telegram.org/bots/api)

Bot de Telegram que permite descargar videos, audios y archivos generando enlaces temporales con tokens únicos. Perfecto para compartir archivos grandes de forma segura y temporal.

## ✨ Características

✅ **Descarga de Videos** - Soporta MP4, MKV, WebM, AVI, MOV
✅ **Reproducción Online** - Reproduce videos y audios directamente en el navegador
✅ **Audio Streaming** - Soporta MP3, WAV, M4A, AAC, FLAC
✅ **Documentos** - Cualquier tipo de archivo (hasta 2.5 GB)
✅ **Enlaces Temporales** - Tokens únicos que caducan en 24 horas
✅ **Compartible** - Genera enlaces para compartir en Telegram
✅ **Sin Almacenamiento Permanente** - Los archivos se eliminan automáticamente
✅ **Estadísticas** - Panel de estadísticas en tiempo real

## 🚀 Inicio Rápido

### Requisitos
- Python 3.8+
- pip (gestor de paquetes de Python)
- Token de Bot de Telegram

### Instalación Local

1. **Clona el repositorio:**
   ```bash
   git clone https://github.com/rodriguezloisajuan-gif/Sacalonsk.git
   cd Sacalonsk
   ```

2. **Crea un ambiente virtual:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instala las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configura las variables de entorno:**
   ```bash
   cp .env.example .env
   # Edita .env con tus valores
   ```

5. **Ejecuta el bot:**
   ```bash
   python app.py
   ```

   El servidor estará disponible en `http://localhost:5000`

## 🌐 Despliegue en Heroku

### Paso 1: Crea una aplicación en Heroku
```bash
heroku login
heroku create tu-app-name
```

### Paso 2: Configura las variables de entorno
```bash
heroku config:set TOKEN="tu-token-aqui"
heroku config:set BASE_URL="https://tu-app-name.herokuapp.com"
```

### Paso 3: Deploy
```bash
git push heroku main
```

### Paso 4: Ver logs
```bash
heroku logs --tail
```

## 📱 Cómo Usar el Bot

1. **Inicia conversación con el bot:**
   - Abre Telegram y busca: `@Sacalonsk_bot`
   - O usa `/start`

2. **Envía un archivo:**
   - Envía un video, audio o documento al bot
   - El bot procesará el archivo

3. **Recibe los enlaces:**
   ```
   📂 Nombre del archivo
   📦 Tamaño
   📥 Enlace de descarga
   🖥 Enlace para reproducir
   🔗 Enlace para compartir
   ```

4. **Comparte o descarga:**
   - Usa el enlace de descarga directo en Chrome
   - O reproduce online sin descargar
   - Comparte el enlace con otros usuarios

## 🔧 Comandos del Bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Inicia el bot y muestra instrucciones |
| `/help` | Muestra la ayuda y comandos disponibles |
| `/stats` | Muestra estadísticas del bot |

## 📋 Estructura del Proyecto

```
Sacalonsk/
├── app.py                 # Aplicación principal (Telegram + Flask)
├── requirements.txt       # Dependencias de Python
├── Procfile              # Configuración para Heroku
├── .env.example          # Variables de entorno de ejemplo
├── .gitignore            # Archivos a ignorar en Git
├── config.py             # Configuración centralizada
├── LICENSE               # Licencia MIT
├── README.md             # Este archivo
└── videos_temp/          # Carpeta de archivos temporales (creada automáticamente)
```

## 🌍 Endpoints Disponibles

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/` | GET | Página principal |
| `/dl/<token>` | GET | Descarga directo del archivo |
| `/watch/<token>` | GET | Reproductor online |
| `/stream/<token>` | GET | Stream del archivo |
| `/stats` | GET | Panel de estadísticas HTML |
| `/api/stats` | GET | API de estadísticas JSON |

## 🔐 Seguridad

- ✅ Tokens únicos y seguros (32 caracteres)
- ✅ Expiración automática de enlaces (24 horas)
- ✅ Sin almacenamiento permanente de archivos
- ✅ Límite de tamaño de archivo (2.5 GB)
- ✅ Limpieza automática de expirados
- ✅ Uso directo de la API de Telegram (sin servidores intermedios)

## 📊 Características Técnicas

- **Framework:** Flask (servidor web minimalista)
- **Bot:** python-telegram-bot (API oficial)
- **Async:** Soporte para operaciones asincrónicas
- **Streaming:** Descarga bajo demanda de Telegram
- **Base de datos:** En memoria (fácil migración a Redis)
- **Logging:** Sistema de logs integrado

## 🔄 Flujo de Funcionamiento

```
┌────────────────────────────────────────────┐
│  Usuario envía archivo a Telegram          │
└────────────────────┬───────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│  Bot recibe y procesa el archivo           │
└────────────────────┬───────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│  Genera token único (24 caracteres)        │
└────────────────────┬───────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│  Crea entrada en base de datos             │
│  (Expira en 24 horas)                      │
└────────────────────┬───────────────────────┘
                     │
                     ▼
┌────────────────────────────────────────────┐
│  Envía 3 enlaces al usuario:               │
│  - Descarga                                │
│  - Ver/Reproducir                          │
│  - Compartir en Telegram                   │
└────────────────────────────────────────────┘
```

## 🛠️ Configuración Avanzada

### Usar Redis para persistencia

En `app.py`, reemplaza `FileDatabase` con `FileDatabase Redis`:

```python
import redis

class FileDatabase:
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        # ... resto del código
```

### Variables de entorno

Crea un archivo `.env` con:

```env
TOKEN=tu_token_aqui
BASE_URL=https://tu-dominio.com
PORT=5000
```

## 📝 Logs

El bot genera logs automáticamente:

```
INFO:__main__:Archivo creado: a1b2c3d4e5f6 - video.mp4
INFO:__main__:Descarga: a1b2c3d4e5f6 - Descargas: 1
INFO:__main__:Vista: a1b2c3d4e5f6 - Vistas: 5
```

## 🐛 Troubleshooting

### El bot no responde
- Verifica que el token sea correcto
- Revisa que el servidor esté corriendo
- Chequea los logs: `heroku logs --tail`

### Error al descargar
- El enlace puede estar expirado (24 horas)
- Solicita un nuevo enlace al bot

### Archivo muy grande
- El límite es 2.5 GB
- Los videos se descargan bajo demanda desde Telegram

## 📞 Soporte

Para reportar bugs o sugerencias:
- Abre un [issue](https://github.com/rodriguezloisajuan-gif/Sacalonsk/issues)
- O contáctame en Telegram

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver archivo `LICENSE` para más detalles.

## 🙏 Agradecimientos

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Flask](https://flask.palletsprojects.com/)
- La comunidad de desarrolladores 🚀

---

**Hecho con ❤️ por [@rodriguezloisajuan-gif](https://github.com/rodriguezloisajuan-gif)**
