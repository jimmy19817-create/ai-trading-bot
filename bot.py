import os
import ccxt
from groq import Groq

# Configurazione Client Groq e Bybit
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Usiamo Bybit perché non blocca i server di GitHub
exchange = ccxt.bybit({
    'apiKey': os.environ.get("BINANCE_API_KEY"), # Qui stiamo usando i segreti che hai già
    'secret': os.environ.get("BINANCE_SECRET_KEY"),
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(True) # Attiva la Testnet

def get_ai_decision(price):
    prompt = f"Il prezzo attuale di Bitcoin (BTC) è di {price} USD. Cosa dovremmo fare? Rispondi SOLO con una parola: COMPRA, VENDI o ATTENDI."
    
    chat_completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
    )
    return chat_completion.choices[0].message.content.strip().upper()

def main():
    try:
        # Prendi il prezzo da Bybit
        ticker = exchange.fetch_ticker('BTC/USDT')
        current_price = ticker['last']
        print(f"--- Analisi Bybit Iniziata ---")
        print(f"Prezzo attuale BTC: ${current_price}")

        decision = get_ai_decision(current_price)
        print(f"L'IA ha deciso di: {decision}")

        # Esempio di ordine su Bybit (Spot)
        if "COMPRA" in decision:
            order = exchange.create_market_buy_order('BTC/USDT', 0.001) # Compra una piccola frazione
            print(f"Ordine ACQUISTO effettuato! ID: {order['id']}")
        elif "VENDI" in decision:
            order = exchange.create_market_sell_order('BTC/USDT', 0.001)
            print(f"Ordine VENDITA effettuato! ID: {order['id']}")
        else:
            print("L'IA suggerisce di attendere.")

    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")

if __name__ == "__main__":
    main()
