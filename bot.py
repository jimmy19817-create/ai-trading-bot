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
    """Scarica le ultime 24 candele per dare il contesto del trend all'IA."""
    print("Recupero dati storici per l'analisi del grafico...")
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=24)
    history_str = "Trend delle ultime 24 ore (Chiusura Prezzo):\n"
    for candle in ohlcv:
        history_str += f"{candle[4]} USD\n"
    return history_str

def get_ai_decision(history, current_price):
    # AGGIORNAMENTO: Usiamo il modello più recente disponibile su Groq
    # Se questo dovesse fallire in futuro, controlla i nomi su console.groq.com
    target_model = "llama-3.3-70b-versatile" 
    
    prompt = f"""
    Sei un trader esperto. Analizza questo grafico testuale (ultime 24 ore):
    {history}
    
    Prezzo ATTUALE: {current_price} USD.
    
    Decidi se COMPRARE, VENDERE o ATTENDERE basandoti sul trend.
    Rispondi SOLO con la parola magica: COMPRA, VENDI o ATTENDI.
    """
    
    try:
        chat = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=target_model,
        )
        return chat.choices[0].message.content.strip().upper()
    except Exception as e:
        print(f"Errore chiamata IA: {e}")
        return "ATTENDI"

def main():
    try:
        exchange.load_markets()
        ticker = exchange.fetch_ticker('BTC/USDT')
        current_price = ticker['last']
        chart_data = get_history()
        
        print(f"--- Analisi con Grafico e Nuovo Modello ---")
        print(f"Prezzo: ${current_price}")

        decision = get_ai_decision(chart_data, current_price)
        print(f"L'IA ha analizzato il trend e dice: {decision}")

        # Esecuzione (piccola quota di test: 0.001 BTC)
        if "COMPRA" in decision:
            order = exchange.create_market_buy_order('BTC/USDT', 0.001)
            print(f"✅ ORDINE ACQUISTO: {order['id']}")
        elif "VENDI" in decision:
            order = exchange.create_market_sell_order('BTC/USDT', 0.001)
            print(f"✅ ORDINE VENDITA: {order['id']}")
        else:
            print("💤 Nessuna operazione: l'IA preferisce aspettare un segnale migliore.")

    except Exception as e:
        print(f"Errore critico: {e}")

if __name__ == "__main__":
    main()
