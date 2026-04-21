import os
import ccxt
from groq import Groq

# Configurazione
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
exchange = ccxt.bitget({
    'apiKey': os.environ.get("BINANCE_API_KEY"),
    'secret': os.environ.get("BINANCE_SECRET_KEY"),
    'password': os.environ.get("BITGET_PASSWORD"),
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(True)

def get_history():
    """Scarica le ultime 24 candele da 1 ora per dare il 'grafico' all'IA."""
    print("Scarico i dati del grafico...")
    # '1h' significa candele orarie, limit=24 sono le ultime 24 ore
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=24)
    
    # Formattiamo i dati per renderli leggibili all'IA
    history_str = "Prezzi delle ultime 24 ore (Chiusura, Volume):\n"
    for candle in ohlcv:
        history_str += f"Prezzo: {candle[4]} USD, Vol: {candle[5]}\n"
    return history_str

def get_ai_decision(history, current_price):
    prompt = f"""
    Sei un trader professionista. Ecco il grafico (dati storici) di Bitcoin delle ultime 24 ore:
    {history}
    
    Il prezzo ATTUALE è: {current_price} USD.
    
    Analizza il trend: il prezzo sta salendo o scendendo? C'è molto volume?
    Basandoti su questo 'grafico' testuale, decidi la prossima mossa per il nostro fondo da 10.000$.
    Rispondi SOLO con una parola: COMPRA, VENDI o ATTENDI.
    """
    
    chat = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama3-70b-8192",
    )
    return chat.choices[0].message.content.strip().upper()

def main():
    try:
        exchange.load_markets()
        
        # 1. Otteniamo il prezzo attuale
        ticker = exchange.fetch_ticker('BTC/USDT')
        current_price = ticker['last']
        
        # 2. Otteniamo lo storico (il "grafico")
        chart_data = get_history()
        
        print(f"--- Analisi Avanzata ---")
        print(f"Prezzo Attuale: ${current_price}")

        # 3. Decisione basata sul grafico
        decision = get_ai_decision(chart_data, current_price)
        print(f"L'IA ha analizzato il grafico e deciso di: {decision}")

        # 4. Esecuzione (Esempio 100$ di operazione)
        if "COMPRA" in decision:
            amount = 100 / current_price
            order = exchange.create_market_buy_order('BTC/USDT', amount)
            print(f"ORDINE DI ACQUISTO ESEGUITO! ID: {order['id']}")
        elif "VENDI" in decision:
            amount = 100 / current_price
            order = exchange.create_market_sell_order('BTC/USDT', amount)
            print(f"ORDINE DI VENDITA ESEGUITO! ID: {order['id']}")
        else:
            print("L'IA consiglia di non operare basandosi sul trend attuale.")

    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
