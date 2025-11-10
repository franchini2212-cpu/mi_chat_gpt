@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    base64_img = data.get("image")
    user_text = data.get("message", "")

    # ✅ HISTORIAL COMPLETO que te envía tu app
    history = data.get("history", [])

    groq_messages = []

    # -------------------------------------------------
    # ✅ Convertimos historial al formato Groq
    # -------------------------------------------------
    for h in history:

        # ✅ 1) Si es texto, lo pasamos normal
        if "content" in h and h["content"]:
            groq_messages.append({
                "role": h["role"],
                "content": h["content"]
            })

        # ✅ 2) Si es imagen, analizamos con Gemini y
        # guardamos EL ANÁLISIS, no el base64.
        elif "image" in h and h["image"]:
            gemini_analysis = gemini_describe_image(
                h["image"],
                "Describe esta imagen de manera detallada."
            )
            groq_messages.append({
                "role": h["role"],
                "content": f"[Imagen anterior analizada por Gemini]:\n\n{gemini_analysis}"
            })

    # -------------------------------------------------
    # ✅ FLUJO: USUARIO ENVÍA UNA IMAGEN
    # -------------------------------------------------
    if base64_img:

        # 1) Gemini analiza la nueva imagen
        gemini_analysis = gemini_describe_image(
            base64_img,
            user_text if user_text else "Analiza la imagen enviada."
        )

        # 2) Guardamos el resultado detallado en el historial para Groq
        groq_messages.append({
            "role": "user",
            "content": f"El usuario envió una nueva imagen. "
                       f"Análisis de Gemini:\n\n{gemini_analysis}"
        })

        # 3) Groq responde usando TODO el historial, incluído el análisis
        final = groq_chat(groq_messages)
        return jsonify({"reply": final})

    # -------------------------------------------------
    # ✅ FLUJO: SOLO TEXTO
    # -------------------------------------------------
    groq_messages.append({
        "role": "user",
        "content": user_text
    })

    final = groq_chat(groq_messages)
    return jsonify({"reply": final})
