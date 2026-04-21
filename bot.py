import os
import ccxt
from groq import Groq

# Configurazione Groq
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Configurazione Bitget (Molto più stabile su GitHub Actions)
exchange = ccxt.bitget({
    'apiKey': os.environ.get("BINANCE_API_KEY"),
    'secret': os.environ.get("BINANCE_SECRET_KEY"),
    'password': os.environ.get("BITGET_PASSWORD"), # Bitget richiede la passphrase
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(True) # Modalità Testnet (Soldi finti)

def get_ai_decision(price):
    prompt = f"Il prezzo attuale di Bitcoin è {price} USD. Rispondi solo con una parola: COMPRA, VENDI o ATTENDI."
    try:
        chat = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-70b-8192",
        )
        return chat.choices[0].message.content.strip().upper()
    except:
        return "ATTENDI"

def main():
    try:
        # Carichiamo i mercati e leggiamo il prezzo
        exchange.load_markets()
        ticker = exchange.fetch_ticker('BTC/USDT')
        price = ticker['last']
        
        print(f"--- Analisi Bitget ---")
        print(f"Prezzo BTC: ${price}")

        decision = get_ai_decision(price)
        print(f"Decisione IA: {decision}")

        # Esecuzione ordine (usiamo piccoli importi per test)
        if "COMPRA" in decision:
            order = exchange.create_market_buy_order('BTC/USDT', 0.0001)
            print(f"Acquisto simulato eseguito! ID: {order['id']}")
        elif "VENDI" in decision:
            order = exchange.create_market_sell_order('BTC/USDT', 0.0001)
            print(f"Vendita simulata eseguita! ID: {order['id']}")
        else:
            print("Nessun ordine inviato.")

    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
