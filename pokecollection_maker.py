import sqlite3
import requests
import os

# Configuración
API_KEY = "65ff04ff-0d3c-44a9-bae9-f9572fba9576"  # Tu clave API
BASE_URL = "https://api.pokemontcg.io/v2/cards"
HEADERS = {"X-Api-Key": API_KEY}
IMAGE_FOLDER = "card_images"  # Carpeta donde se guardarán las imágenes

# Crear la carpeta si no existe
if not os.path.exists(IMAGE_FOLDER):
    os.makedirs(IMAGE_FOLDER)

# Lista de tus cartas
my_cards = [
    {"card_id": "sv6-65", "quantity": 1},
    {"card_id": "sv6-80", "quantity": 1},
    {"card_id": "sv6-135", "quantity": 1},
    {"card_id": "sv6-136", "quantity": 1},
    {"card_id": "sv6-154", "quantity": 1},
    {"card_id": "sv7-2", "quantity": 1},
    {"card_id": "sv7-3", "quantity": 2},
    {"card_id": "sv7-8", "quantity": 1},
    {"card_id": "sv7-45", "quantity": 1},
    {"card_id": "sv7-57", "quantity": 1},
    {"card_id": "sv7-58", "quantity": 2},
    {"card_id": "sv7-60", "quantity": 1},
    {"card_id": "sv7-66", "quantity": 1},
    {"card_id": "sv7-87", "quantity": 1},
    {"card_id": "sv7-101", "quantity": 1},
    {"card_id": "sv7-106", "quantity": 1},
    {"card_id": "sv7-107", "quantity": 1},
    {"card_id": "sv7-115", "quantity": 1},
    {"card_id": "sv7-118", "quantity": 3},
    {"card_id": "sv7-119", "quantity": 1},
    {"card_id": "sv7-132", "quantity": 1},
    {"card_id": "sv7-133", "quantity": 5},
    {"card_id": "sv7-138", "quantity": 4}
]

# Conjuntos Scarlet & Violet hasta el presente
SV_SETS = ["sv1", "sv2", "sv3", "sv3pt5", "sv4", "sv4pt5", "sv5", "sv6", "sv6pt5", "sv7"]

# Conectar a la base de datos
conn = sqlite3.connect("pokemon_collection.db")
cursor = conn.cursor()

# Crear tablas
cursor.execute('''
CREATE TABLE IF NOT EXISTS cards (
    card_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    set_id TEXT NOT NULL,
    set_name TEXT NOT NULL,
    number TEXT NOT NULL,
    rarity TEXT,
    type TEXT,
    image_url TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS my_collection (
    card_id TEXT PRIMARY KEY,
    quantity INTEGER NOT NULL
)
''')

# Función para obtener todas las cartas de un conjunto
def get_cards_by_set(set_id):
    all_cards = []
    page = 1
    while True:
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
for set_id in SV_SETS:
    print(f"Obteniendo cartas del conjunto {set_id}...")
    set_cards = get_cards_by_set(set_id)
    
    # Procesar todas las cartas del conjunto
    for card in set_cards:
        card_id = card["id"]
        matching_card = next((c for c in my_cards if c["card_id"] == card_id), None)
        quantity = matching_card["quantity"] if matching_card else 0
        
        # Insertar en 'cards'
        image_url = card["images"]["small"]
        cursor.execute('''
        INSERT OR IGNORE INTO cards (card_id, name, set_id, set_name, number, rarity, type, image_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            card["id"],
            card["name"],
            card["set"]["id"],
            card["set"]["name"],
            card["number"],
            card.get("rarity", ""),
            card["types"][0] if card.get("types") else "",
            image_url
        ))

        # Insertar en 'my_collection'
        cursor.execute('''
        INSERT OR REPLACE INTO my_collection (card_id, quantity)
        VALUES (?, ?)
        ''', (card_id, quantity))

        # Descargar la imagen para todas las cartas
        download_image(card_id, image_url)

# Guardar cambios y cerrar
conn.commit()
conn.close()

print("Base de datos creada exitosamente y todas las imágenes descargadas!")