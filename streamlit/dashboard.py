import streamlit as st
import happybase
import pandas as pd
import time

# Titre de l'application
st.title("Crypto Prices Dashboard")

# Connexion à HBase avec retry
def get_hbase_connection():
    max_retries = 5
    retry_delay = 2  # secondes
    for attempt in range(max_retries):
        try:
            connection = happybase.Connection('hbase', port=9090)
            connection.open()  # Ouvre explicitement la connexion
            return connection
        except Exception as e:
            st.warning(f"Tentative {attempt + 1}/{max_retries} - Erreur de connexion HBase : {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                st.error("Impossible de se connecter à HBase après plusieurs tentatives.")
                raise

# Récupérer les données de HBase
def fetch_hbase_data():
    connection = get_hbase_connection()
    try:
        table = connection.table('crypto_prices')
        data = []
        for key, row_data in table.scan():
            coin_date = key.decode('utf-8')
            coin, date = coin_date.split('_', 1)
            record = {
                'coin': coin,
                'date': date,
                'price_min': float(row_data[b'stats:price_min'].decode('utf-8')),
                'price_max': float(row_data[b'stats:price_max'].decode('utf-8')),
                'price_avg': float(row_data[b'stats:price_avg'].decode('utf-8')),
                'volume_sum': float(row_data[b'stats:volume_sum'].decode('utf-8')),
                'daily_variation_percent': float(row_data[b'stats:daily_variation_percent'].decode('utf-8'))
            }
            data.append(record)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erreur lors du scan HBase : {e}")
        return pd.DataFrame()  # Retourne un DataFrame vide en cas d'erreur
    finally:
        connection.close()

# Charger les données avec gestion d'erreur
try:
    # Mettre les données en cache pour éviter de relancer fetch_hbase_data à chaque interaction
    @st.cache_data(ttl=300)  # Cache pendant 5 minutes
    def cached_fetch_hbase_data():
        return fetch_hbase_data()
    
    data = cached_fetch_hbase_data()
    if data.empty:
        st.warning("Aucune donnée trouvée dans HBase.")
    else:
        # Sélectionner un coin
        coins = data['coin'].unique()
        selected_coin = st.selectbox("Sélectionner une crypto", coins)

        # Filtrer les données par coin
        filtered_data = data[data['coin'] == selected_coin]

        # Afficher un tableau
        st.subheader(f"Données pour {selected_coin}")
        st.dataframe(filtered_data)

        # Graphique : Prix moyen par date
        st.subheader("Prix moyen au fil du temps")
        st.line_chart(filtered_data.set_index('date')['price_avg'], use_container_width=True)

        # Graphique : Volume total
        st.subheader("Volume total par date")
        st.bar_chart(filtered_data.set_index('date')['volume_sum'], use_container_width=True)

        # Variation quotidienne
        st.subheader("Variation quotidienne (%)")
        st.line_chart(filtered_data.set_index('date')['daily_variation_percent'], use_container_width=True)
except Exception as e:
    st.error(f"Erreur lors de la récupération des données : {e}")
