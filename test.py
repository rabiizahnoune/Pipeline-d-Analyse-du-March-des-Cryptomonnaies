import happybase
connection = happybase.Connection('hbase', port=9090)
print(connection.tables())  # Devrait afficher ['crypto_prices']
connection.close()