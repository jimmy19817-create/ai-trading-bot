import os
import ccxt
from groq import Groq
from tavily import TavilyClient

# Configurazione Clienti
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
exchange = ccxt.bitget({
    'apiKey': os.environ.get("BINANCE_API_KEY"),
    'secret': os.environ.get("BINANCE_SECRET_KEY"),
    'password': os.environ.get("BITGET_PASSWORD"),
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(True)

def get_market_context():
    """Scarica il grafico e le news/social in un colpo solo."""
    print("Analizzando grafico e trend su X/News...")
    # 1. Grafico
    ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1h', limit=12)
    chart = "\n".join([f"Prezzo: {c[4]} USD" for c in ohlcv])
    
    # 2. Social/News (Il tocco di Grok)
    search = tavily.search(query="Bitcoin price sentiment X twitter news latest", search_depth="advanced", max_results=3)
    context = "\n".join([f"- {r['content'][:200]}" for r in search['results']])
    
    return chart, context

def get_ai_decision(chart, news, price):
    prompt = f"""
    SEI UN TRADER AGGRESSIVO TIPO GROK.
    PREZZO ATTUALE: {price} USD.
    
    GRAFICO ULTIME 12H:
    {chart}
    
    NEWS E SENTIMENT SOCIAL (X):
    {news}
    
    Basandoti su questi dati, devi decidere la mossa per il nostro fondo da 10.000$.
    Sii proattivo: se le news sono eccitanti, COMPRA. Se c'è paura, VENDI.
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
        price = exchange.fetch_ticker('BTC/USDT')['last']
        chart, news = get_market_context()
        
        print(f"--- Report Strategico Integrato ---")
        decision = get_ai_decision(chart, news, price)
        print(f"L'IA ha deciso: {decision}")

        if "COMPRA" in decision:
            order = exchange.create_market_buy_order('BTC/USDT', 0.002) # Circa 150$ di test
            print(f"🚀 ORDINE ESEGUITO: {order['id']}")
        elif "VENDI" in decision:
            order = exchange.create_market_sell_order('BTC/USDT', 0.002)
            print(f"📉 VENDITA ESEGUITA: {order['id']}")
        else:
            print("💤 L'IA non vede opportunità né nei grafici né nei social.")

    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    main()
