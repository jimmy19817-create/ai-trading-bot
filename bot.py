import os
import ccxt
import pandas as pd
import pandas_ta as ta
from groq import Groq
from tavily import TavilyClient

# Inizializzazione
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
exchange = ccxt.bitget({
    'apiKey': os.environ.get("BINANCE_API_KEY"),
    'secret': os.environ.get("BINANCE_SECRET_KEY"),
    'password': os.environ.get("BITGET_PASSWORD"),
    'enableRateLimit': True,
    'options': {'createMarketBuyOrderRequiresPrice': False}
})
exchange.set_sandbox_mode(True)

def calculate_mcdx_proxy(df):
    """Simula l'MCDX: calcola il flusso dei grandi capitali (Bankers)."""
    rsi = ta.rsi(df['close'], length=14)
    # Calcolo semplificato del Banker Flow (Barre Rosse)
    banker_energy = (rsi - 50).apply(lambda x: max(0, x * 2))
    return banker_energy.iloc[-1]

def get_market_data():
    print("Analizzando Grafico, News e Flusso Capitali (MCDX)...")
    # Scarichiamo 50 candele per calcolare bene gli indicatori
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=50)
    df = pd.DataFrame(ohlcv, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
    
    banker_flow = calculate_mcdx_proxy(df)
    
    # News/Social
    search = tavily.search(query="Bitcoin bullish sentiment institutional buying X", max_results=3)
    news = "\n".join([r['content'][:200] for r in search['results']])
    
    return df['close'].iloc[-1], news, banker_flow

def get_ai_decision(price, news, banker_flow):
    # Definiamo il livello di "forza" delle balene
    banker_status = "FORTE ACCUMULO (Balene attive)" if banker_flow > 15 else "DEBOLE (Solo retail)"
    
    prompt = f"""
    SEI UN TRADER AGGRESSIVO. 
    Prezzo attuale: {price} USD.
    Sentiment Social: {news}
    Indicatore MCDX (Banker Flow): {banker_flow:.2f} -> {banker_status}
    
    Se vedi 'FORTE ACCUMULO' dell'MCDX, ignora la prudenza e COMPRA.
    Se il sentiment è negativo e il Banker Flow è basso, VENDI.
    Rispondi SOLO con: COMPRA, VENDI o ATTENDI.
    """
    chat = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat.choices[0].message.content.strip().upper()

def main():
    try:
        exchange.load_markets()
        price, news, banker_flow = get_market_data()
        
        print(f"--- Report Strategico v3.0 (MCDX) ---")
        print(f"Banker Flow: {banker_flow:.2f} ({'Balene' if banker_flow > 15 else 'Retail'})")
        
        decision = get_ai_decision(price, news, banker_flow)
        print(f"Decisione Finale: {decision}")

        if "COMPRA" in decision:
            order = exchange.create_market_buy_order('BTC/USDT', 500)
            print(f"🚀 ORDINE ESEGUITO: {order['id']}")
        elif "VENDI" in decision:
            order = exchange.create_market_sell_order('BTC/USDT', 0.005)
            print(f"📉 VENDITA ESEGUITA: {order['id']}")
        else:
            print("💤 L'IA rimane cauta.")
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
