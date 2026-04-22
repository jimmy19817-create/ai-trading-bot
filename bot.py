import os
import ccxt
import pandas as pd
import pandas_ta as ta
import requests
from groq import Groq
from tavily import TavilyClient

groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
tavily = TavilyClient(api_key=os.environ.get("TAVILY_API_KEY"))
# Telegram Config
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

exchange = ccxt.bitget({
    'apiKey': os.environ.get("BINANCE_API_KEY"),
    'secret': os.environ.get("BINANCE_SECRET_KEY"),
    'password': os.environ.get("BITGET_PASSWORD"),
    'enableRateLimit': True,
    'options': {'createMarketBuyOrderRequiresPrice': False}
})
exchange.set_sandbox_mode(True)

def send_telegram_message(message):
    """Invia una notifica su Telegram."""
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except Exception as e:
            print(f"Errore invio Telegram: {e}")

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
        decision = get_ai_decision(price, news, banker_flow)
        
        log_msg = f"--- *Report Strategico* ---\n💰 Prezzo: ${price}\n📊 MCDX: {banker_flow:.2f}\n🧠 Decisione: *{decision}*"
        
        if "COMPRA" in decision:
            order = exchange.create_market_buy_order('BTC/USDT', 500)
            msg = f"🚀 *ORDINE ACQUISTO ESEGUITO*\nID: `{order['id']}`\nInvestito: $500\n\n{log_msg}"
            send_telegram_message(msg)
            print(msg)
        elif "VENDI" in decision:
            order = exchange.create_market_sell_order('BTC/USDT', 0.005)
            msg = f"📉 *VENDITA ESEGUITA*\nID: `{order['id']}`\nQuantità: 0.005 BTC\n\n{log_msg}"
            send_telegram_message(msg)
            print(msg)
        else:
            # Opzionale: invia un messaggio anche se non opera per sapere che è vivo
            # send_telegram_message(f"💤 *Nessuna operazione*\n{log_msg}")
            print("💤 L'IA rimane in attesa.")
            
    except Exception as e:
        error_msg = f"❌ *Errore Bot*: {str(e)}"
        send_telegram_message(error_msg)
        print(error_msg)

if __name__ == "__main__":
    main()
