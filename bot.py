import os
import ccxt
from groq import Groq

# 1. Configurazione Client Groq e Binance
# Recuperiamo le chiavi segrete che imposterai su GitHub
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
binance = ccxt.binance({
    'apiKey': os.environ.get("BINANCE_API_KEY"),
    'secret': os.environ.get("BINANCE_SECRET_KEY"),
    'enableRateLimit': True,
})
# Indichiamo a CCXT di usare la Testnet (soldi finti)
binance.set_sandbox_mode(True)

def get_ai_decision(price):
    """Chiede a Groq cosa fare basandosi sul prezzo di BTC in Dollari."""
    prompt = f"Il prezzo attuale di Bitcoin (BTC) è di {price} USD. Basandoti solo su questo dato e sulla tua analisi dei mercati crypto del 2026, cosa dovremmo fare? Rispondi ESCLUSIVAMENTE con una di queste tre parole: COMPRA, VENDI, ATTENDI."
    
    chat_completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192", # Usiamo il modello Llama 3 tramite Groq
    )
    return chat_completion.choices[0].message.content.strip().upper()

def main():
    try:
        # Recupera il prezzo di Bitcoin/Dollaro (USDT)
        ticker = binance.fetch_ticker('BTC/USDT')
        current_price = ticker['last']
        print(f"--- Analisi Iniziata ---")
        print(f"Prezzo attuale BTC: ${current_price}")

        # Chiede all'IA cosa fare
        decision = get_ai_decision(current_price)
        print(f"L'IA ha deciso di: {decision}")

        # Esegue l'operazione sulla Testnet
        if "COMPRA" in decision:
            # Esempio: compra 100 dollari di BTC
            amount_to_buy = 100 / current_price
            order = binance.create_market_buy_order('BTC/USDT', amount_to_buy)
            print(f"Ordine di ACQUISTO eseguito! ID: {order['id']}")
        
        elif "VENDI" in decision:
            # Esempio: vendi 100 dollari di BTC
            amount_to_sell = 100 / current_price
            order = binance.create_market_sell_order('BTC/USDT', amount_to_sell)
            print(f"Ordine di VENDITA eseguito! ID: {order['id']}")
        
        else:
            print("Nessuna azione intrapresa.")

    except Exception as e:
        print(f"Errore durante l'esecuzione: {e}")

if __name__ == "__main__":
    main()
