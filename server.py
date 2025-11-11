from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras

app = Flask(__name__)

# ✅ URL de tu base de datos PostgreSQL en Render
DB_URL = "postgresql://mi_base_de_datos_7ap6_user:6bOxgNN8k3NJf1ZNJCMT8yebHbWdI4PC@dpg-d49ioivgi27c73ccefq0-a.oregon-postgres.render.com/mi_base_de_datos_7ap6"


# ✅ Función para obtener conexión por request
def get_db():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    return conn, cur


# ✅ Crear tabla una sola vez al iniciar
def init_db():
    conn, cur = get_db()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id SERIAL PRIMARY KEY,
            rol TEXT NOT NULL,
            contenido TEXT,
            imagen TEXT,
            timestamp TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    conn.close()


init_db()  # ✅ Solo una vez, al inicio del servidor


# ✅ Guardar mensaje en la BD
def guardar_mensaje(rol, contenido, imagen=None):
    conn, cur = get_db()
    cur.execute(
        "INSERT INTO mensajes (rol, contenido, imagen) VALUES (%s, %s, %s)",
        (rol, contenido, imagen)
    )
    conn.commit()
    conn.close()


# ✅ Cargar historial completo desde la BD
def cargar_historial():
    conn, cur = get_db()
    cur.execute("SELECT rol, contenido, imagen FROM mensajes ORDER BY id ASC")
    rows = cur.fetchall()
    conn.close()

    historial = []
    for r in rows:
        if r["imagen"]:  # Si tiene imagen guardada
            historial.append({
                "role": r["rol"],
                "image": r["imagen"]
            })
        else:
            historial.append({
                "role": r["rol"],
                "content": r["contenido"]
            })

    return historial


# ✅ Gemini analiza imágenes (versión falsa para pruebas)
def gemini_describe_image(base64_img, prompt):
    return f"[Análisis de Gemini]: {prompt}"


# ✅ Groq responde (falso para pruebas)
def groq_chat(messages):
    texto = "\n".join([m.get("content", "") for m in messages])
    return "Groq respondió según historial:\n\n" + texto


# ✅ Ruta principal del chat
@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()

    base64_img = data.get("image")
    user_text = data.get("message", "")

    # ✅ Cargar historial desde base de datos
    history = cargar_historial()

    groq_messages = []

    # ✅ Convertir historial al formato Groq
    for h in history:
        if "content" in h:
            groq_messages.append({
                "role": h["role"],
                "content": h["content"]
            })

        elif "image" in h:
            gemini_analysis = gemini_describe_image(
                h["image"], "Describe esta imagen."
            )
            groq_messages.append({
                "role": h["role"],
                "content": f"[Imagen previa analizada]: {gemini_analysis}"
            })

    # ✅ Si el usuario envía imagen
    if base64_img:
        gemini_analysis = gemini_describe_image(
            base64_img,
            user_text if user_text else "Analiza la imagen enviada."
        )

        groq_messages.append({
            "role": "user",
            "content": f"Nueva imagen del usuario:\n{gemini_analysis}"
        })

        # ✅ Guardar imagen y análisis
        guardar_mensaje("user", None, base64_img)
        guardar_mensaje("system", gemini_analysis)

        final = groq_chat(groq_messages)

        guardar_mensaje("assistant", final)

        return jsonify({"reply": final})

    # ✅ Si es solo texto
    groq_messages.append({
        "role": "user",
        "content": user_text
    })

    guardar_mensaje("user", user_text)

    final = groq_chat(groq_messages)

    guardar_mensaje("assistant", final)

    return jsonify({"reply": final})


@app.route("/")
def home():
    return "Servidor funcionando con historial permanente ✅"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
