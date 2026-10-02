import time
from pyngrok import ngrok
from src.app import app


HOST = 'localhost'
PORT = 5000
DEBUG = True

if __name__ == '__main__':
    # Configure seu authtoken aqui (obtenha em https://dashboard.ngrok.com/get-started/your-authtoken)
    ngrok.set_auth_token('3AK3HraB1ZTFDqIgrJD67oyFXrP_5DEPrTowmdaPfgjGKbJPE')
    
    # Matar processos ngrok existentes primeiro
    ngrok.kill()
    time.sleep(1)  # Esperar um momento
    print("🔴 Processos ngrok finalizados")
    
    # Desconectar todos os túneis existentes
    try:
        tunnels = ngrok.get_tunnels()
        for tunnel in tunnels:
            ngrok.disconnect(tunnel.public_url)
            print(f"🔴 Túnel desconectado: {tunnel.public_url}")
    except Exception as e:
        print(f"Erro ao desconectar túneis: {e}")
    
    time.sleep(1)  # Esperar um momento
    
    # Abre o túnel ngrok na porta 5000
    public_url = ngrok.connect(PORT)
    print(f"\n✅ URL pública: {public_url}\n")
    
    # Desabilita o reloader para evitar múltiplos túneis ngrok
    app.run(host=HOST, port=PORT, debug=DEBUG, use_reloader=False)
