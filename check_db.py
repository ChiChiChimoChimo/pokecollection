import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect("pokemon_collection.db")
cursor = conn.cursor()

# Consultar y mostrar los resultados
cursor.execute("""
SELECT c.card_id, c.name, c.set_name, m.quantity
FROM cards c
JOIN my_collection m ON c.card_id = m.card_id
""")
for row in cursor.fetchall():
    print(row)

# Cerrar la conexión
conn.close()