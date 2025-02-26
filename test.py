import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import json

def fetch_crypto_data():
    # Symboles pour Bitcoin, Ethereum et Solana
    symbols = ['BTC-USD', 'ETH-USD', 'SOL-USD']
    
    # Définition de la période (dernières 24h)
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    
    # Liste pour stocker les données
    all_data = []
    
    for symbol in symbols:
        try:
            # Récupération des données avec yfinance
            crypto = yf.Ticker(symbol)
            df = crypto.history(
                start=start_time,
                end=end_time,
                interval='1h'  # Intervalle de 1 heure
            )
            
            if df.empty:
                print(f"Aucune donnée pour {symbol}")
                continue
                
            # Réinitialisation de l'index pour avoir Datetime comme colonne
            df = df.reset_index()
            
            # Renommage des colonnes pour plus de clarté
            df = df.rename(columns={
                'Datetime': 'datetime',
                'Open': 'open_price',
                'High': 'high_price',
                'Low': 'low_price',
                'Close': 'close_price',
                'Volume': 'volume'
            })
            
            # Ajout de la colonne coin
            df['coin'] = symbol.replace('-USD', '')
            
            # Suppression des colonnes inutiles si elles existent (comme 'Dividends', 'Stock Splits')
            columns_to_keep = ['datetime', 'open_price', 'high_price', 'low_price', 
                             'close_price', 'volume', 'coin']
            df = df[columns_to_keep]
            
            all_data.append(df)
            
        except Exception as e:
            print(f"Erreur lors de la récupération de {symbol}: {e}")
            continue
    
    if not all_data:
        print("Aucune donnée n'a pu être récupérée")
        return None
        
    # Combinaison des données
    final_df = pd.concat(all_data)
    
    # Conversion en JSON
    json_data = final_df.to_json(orient='records', date_format='iso')
    
    # Sauvegarde dans un fichier
    with open('crypto_data.json', 'w') as f:
        json.dump(json.loads(json_data), f, indent=4)
    
    print("Données sauvegardées dans 'crypto_data.json'")
    return final_df

if __name__ == "__main__":
    # Installation de yfinance si nécessaire (décommente si besoin)
    # import sys
    # !{sys.executable} -m pip install yfinance
    
    df = fetch_crypto_data()
    if df is not None:
        print("\nAperçu des données:")
        print(df.head())