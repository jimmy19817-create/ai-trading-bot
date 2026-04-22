import os
import ccxt
from groq import Groq
from tavily import TavilyClient

# 1. Inizializzazione Clienti (Le "mani" e il "cervello")
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))

exchange = ccxt.bitget({
    'apiKey': os.environ.get("BINANCE_API_KEY"),
    'secret': os.environ.get("BINANCE_SECRET_KEY"),
    'password': os.environ.get("BITGET_PASSWORD"),
    'enableRateLimit': True,
    'options': {
        'createMarketBuyOrderRequiresPrice': False, # Risolve l'errore Bitget
    }
})
exchange.set_sandbox_mode(True)

def get_market_context():
    """Recupera il grafico e le news/social."""
    print("Analizzando grafico e trend su X/News...")
    # Recupero grafico ultime 12 ore
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=12)
    chart = "\n".join([f"Prezzo: {c[4]} USD" for c in ohlcv])
    
    # Recupero news e sentiment
    search = tavily.search(query="Bitcoin price sentiment X twitter news latest", search_depth="advanced", max_results=3)
    news = "\n".join([f"- {r['content'][:200]}" for r in search['results']])
    
    return chart, news

def get_ai_decision(chart, news, price):
    """L'IA decide la strategia."""
    prompt = f"""
    SEI UN TRADER ESPERTO TIPO GROK.
    PREZZO ATTUALE: {price} USD.
    
    GRAFICO ULTIME 12H:
    {chart}
    
    NEWS E SENTIMENT SOCIAL (X):
    {news}
    
    Analizza i dati e decidi se COMPRARE, VENDI o ATTENDI per il nostro fondo da 10.000$.
    Sii proattivo e basati sul sentiment.
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
        # Otteniamo il prezzo in Dollari come richiesto
        price = exchange.fetch_ticker('BTC/USDT')['last']
        
        chart, news = get_market_context()
        
        print(f"--- Report Strategico Integrato ---")
        print(f"Prezzo attuale: ${price}")
        
        decision = get_ai_decision(chart, news, price)
        print(f"L'IA ha deciso: {decision}")

        if "COMPRA" in decision:
            # Investiamo 500 Dollari (USDT)
            budget_usdt = 500 
            order = exchange.create_market_buy_order('BTC/USDT', budget_usdt)
            print(f"🚀 ORDINE ACQUISTO ESEGUITO: {order['id']} per {budget_usdt} USDT")
            
        elif "VENDI" in decision:
            # Vendiamo una piccola quantità di BTC (0.005 BTC sono circa 375$)
            quantita_btc = 0.005
            order = exchange.create_market_sell_order('BTC/USDT', quantita_btc)
            print(f"📉 VENDITA ESEGUITA: {order['id']} di {quantita_btc} BTC")
            
        else:
            print("💤 L'IA suggerisce di non operare al momento.")

    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
