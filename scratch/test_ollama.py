import http.client
import json

conn = http.client.HTTPConnection("localhost", 11434)
payload = json.dumps({
    "model": "deepseek-r1:8b",
    "prompt": "Hola. Di una sola frase corta confirmando que eres DeepSeek R1 8B corriendo en la ASUS ROG.",
    "stream": False
})
headers = {
    'Content-Type': 'application/json'
}

try:
    print("Enviando petición a Ollama (deepseek-r1:8b)...")
    conn.request("POST", "/api/generate", payload, headers)
    res = conn.getresponse()
    data = res.read().decode("utf-8")
    response_json = json.loads(data)
    print("\n--- Respuesta de DeepSeek R1 ---")
    print(response_json.get("response", ""))
except Exception as e:
    print("Error al conectar con Ollama:", e)
