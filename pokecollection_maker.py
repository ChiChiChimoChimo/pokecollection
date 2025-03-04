import sqlite3
import requests
import os
import time

# Configuración
API_KEY = "65ff04ff-0d3c-44a9-bae9-f9572fba9576"  # Tu clave API
BASE_URL = "https://api.pokemontcg.io/v2/cards"
HEADERS = {"X-Api-Key": API_KEY}
IMAGE_FOLDER = "card_images"  # Carpeta donde se guardarán las imágenes
DB_PATH = "pokemon_collection.db"

# Conjuntos Scarlet & Violet hasta el presente
SV_SETS = ["sv1", "sv2", "sv3", "sv3pt5", "sv4", "sv4pt5", "sv5", "sv6", "sv6pt5", "sv7", "sv8", "sv8pt5", "sve"]

# Crear la carpeta si no existe
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# Conectar a la base de datos (esto sobrescribirá si ya existe)
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Crear tablas con todos los campos necesarios
cursor.execute('''
CREATE TABLE IF NOT EXISTS cards (
    card_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    set_id TEXT NOT NULL,
    set_name TEXT NOT NULL,
    number TEXT NOT NULL,
    rarity TEXT,
    type TEXT,
    supertype TEXT,
    image_url TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS my_collection (
    card_id TEXT PRIMARY KEY,
    quantity INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (card_id) REFERENCES cards(card_id)
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS decks (
    deck_id INTEGER PRIMARY KEY AUTOINCREMENT,
    deck_name TEXT NOT NULL,
    deck_text TEXT NOT NULL
)
''')

# Función para obtener todas las cartas de un conjunto
def get_cards_by_set(set_id):
    all_cards = []
    page = 1
    while True:
        print(f"Obteniendo página {page} del conjunto {set_id}...")
        url = f"{BASE_URL}?q=set.id:{set_id}&page={page}&pageSize=250"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            print(f"Error al obtener {set_id}, página {page}: {response.status_code}")
            break
        data = response.json()
        cards = data["data"]
        all_cards.extend(cards)
        if len(cards) < 250:  # Última página
            break
        page += 1
        time.sleep(0.2)  # Pausa para respetar límites de la API
    return all_cards

# Función para descargar la imagen
def download_image(card_id, image_url):
    image_path = os.path.join(IMAGE_FOLDER, f"{card_id}.png")
    if not os.path.exists(image_path):  # Evitar descargar si ya existe
        response = requests.get(image_url)
        if response.status_code == 200:
            with open(image_path, "wb") as f:
                f.write(response.content)
            print(f"Descargada imagen para {card_id}")
        else:
            print(f"Error al descargar imagen de {card_id}: {response.status_code}")
    else:
        print(f"Imagen de {card_id} ya existe, omitiendo descarga")

# Procesar todos los conjuntos SV
total_cards = 0
for set_id in SV_SETS:
    print(f"Obteniendo cartas del conjunto {set_id}...")
    set_cards = get_cards_by_set(set_id)
    
    # Procesar todas las cartas del conjunto
    for card in set_cards:
        card_id = card["id"]
        
        # Insertar en 'cards'
        cursor.execute('''
        INSERT OR IGNORE INTO cards (card_id, name, set_id, set_name, number, rarity, type, supertype, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            card["id"],
            card["name"],
            card["set"]["id"],
            card["set"]["name"],
            card["number"],
            card.get("rarity", "Unknown"),
            card["types"][0] if card.get("types") else "",
            card["supertype"],
            card["images"]["small"]
        ))

        # Insertar en 'my_collection' con cantidad 0 si no existe
        cursor.execute('''
        INSERT OR IGNORE INTO my_collection (card_id, quantity)
        VALUES (?, 0)
        ''', (card_id,))

        # Descargar la imagen
        download_image(card_id, card["images"]["small"])
        total_cards += 1

# Guardar cambios y cerrar
conn.commit()
conn.close()

print(f"Base de datos creada con éxito! Total de cartas procesadas: {total_cards}")