import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import csv
import re

# Configuración
DB_PATH = "pokemon_collection.db"
IMAGE_FOLDER = "card_images"

# Mapeo de rarezas y tipos
RARITY_MAPPING = {
    "Todos": None,
    "● Común": "Common",
    "♦ Poco Común": "Uncommon",
    "★ Rara": "Rare",
    "★★ Double Rare": "Double Rare",
    "★★★ Ultra Rara": "Ultra Rare",
    "ACE SPEC": "ACE SPEC"
}

TYPE_MAPPING = {
    "Todos": None,
    "Fuego": "Fire",
    "Agua": "Water",
    "Planta": "Grass",
    "Eléctrico": "Lightning",
    "Psíquico": "Psychic",
    "Lucha": "Fighting",
    "Oscuridad": "Darkness",
    "Metal": "Metal",
    "Entrenador": ""
}

# Mapeo de códigos de set a códigos de la API
SET_MAPPING = {
    "SVI": "sv1",    # Scarlet & Violet
    "PAL": "sv2",    # Paldea Evolved
    "OBF": "sv3",    # Obsidian Flames
    "PAR": "sv4",    # Paradox Rift
    "TEF": "sv5",    # Temporal Forces
    "TWM": "sv6",    # Twilight Masquerade
    "SCR": "sv7",    # Stellar Crown
    "SSP": "sv8",    # Surging Sparks 
    "SVE": "sve",    # Energías básicas
    "151": "sv3pt5", # 151
    "PAF": "sv4pt5", # Paldean Fates
    "SFA": "sv6pt5", # Shrouded Fable
    "PRE": "sv8pt5"  # Prismatic Evolutions
}

# Cargar las cartas desde la base de datos con orden numérico
def load_cards():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    SELECT c.card_id, c.name, c.set_name, m.quantity, c.rarity, c.type, c.supertype
    FROM cards c
    JOIN my_collection m ON c.card_id = m.card_id
    ORDER BY c.set_id, CAST(c.number AS INTEGER)
    """)
    cards = cursor.fetchall()
    conn.close()
    return cards

# Actualizar la cantidad en la base de datos
def update_quantity(card_id, new_quantity):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE my_collection
    SET quantity = ?
    WHERE card_id = ?
    """, (new_quantity, card_id))
    conn.commit()
    conn.close()

# Guardar un mazo en la base de datos
def save_deck(deck_name, deck_text):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO decks (deck_name, deck_text) VALUES (?, ?)", (deck_name, deck_text))
    conn.commit()
    conn.close()

# Cargar mazos desde la base de datos
def load_decks():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT deck_id, deck_name, deck_text FROM decks")
    decks = cursor.fetchall()
    conn.close()
    return decks

# Borrar un mazo de la base de datos
def delete_deck(deck_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM decks WHERE deck_id = ?", (deck_id,))
    conn.commit()
    conn.close()

# Aplicación
class CardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Mi Colección de Pokémon TCG")
        
        # Cargar el ícono
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "icon.ico")
            self.root.iconbitmap(icon_path)
            self.root.wm_iconbitmap(icon_path)
        except tk.TclError as e:
            print(f"Error al cargar el ícono: {e}")
        
        self.root.geometry("1100x700")
        self.current_card_id = None

        # Mostrar mensaje de carga
        self.loading_label = ttk.Label(self.root, text="Cargando cartas, por favor espera...")
        self.loading_label.pack(expand=True)
        self.root.update()

        # Cargar las cartas
        self.all_cards = load_cards()
        self.filtered_cards = self.all_cards[:]

        # Eliminar mensaje de carga
        self.loading_label.destroy()

        # Frame principal con pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestaña de Lista
        self.list_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.list_frame, text="Lista")

        # Pestaña de Decks
        self.decks_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.decks_frame, text="Decks")

        # Configuración de las pestañas
        self.setup_list_tab()
        self.setup_decks_tab()

    def setup_list_tab(self):
        # Frame de filtros
        self.filter_frame = ttk.LabelFrame(self.list_frame, text="Filtros", padding="5")
        self.filter_frame.pack(fill="x", pady=5)

        # Filtro por nombre
        ttk.Label(self.filter_frame, text="Nombre:").grid(row=0, column=0, padx=5, pady=2)
        self.name_filter = ttk.Entry(self.filter_frame, width=20)
        self.name_filter.grid(row=0, column=1, padx=5, pady=2)
        self.name_filter.bind("<KeyRelease>", self.apply_filters)

        # Filtro por conjunto
        ttk.Label(self.filter_frame, text="Conjunto:").grid(row=0, column=2, padx=5, pady=2)
        self.set_filter = ttk.Combobox(self.filter_frame, values=["Todos", "Scarlet & Violet", "Paldea Evolved", "Obsidian Flames", "151", "Paradox Rift", "Paldean Fates", "Temporal Forces", "Twilight Masquerade", "Shrouded Fable", "Stellar Crown", "Surging Sparks", "Prismatic Evolutions"], state="readonly")
        self.set_filter.grid(row=0, column=3, padx=5, pady=2)
        self.set_filter.set("Todos")
        self.set_filter.bind("<<ComboboxSelected>>", self.apply_filters)

        # Filtro por cantidad
        ttk.Label(self.filter_frame, text="Cant. mínima:").grid(row=0, column=4, padx=5, pady=2)
        self.quantity_filter = ttk.Spinbox(self.filter_frame, from_=0, to=10, width=5)
        self.quantity_filter.grid(row=0, column=5, padx=5, pady=2)
        self.quantity_filter.set(0)
        self.quantity_filter.bind("<KeyRelease>", self.apply_filters)
        self.quantity_filter.bind("<<Increment>>", self.apply_filters)
        self.quantity_filter.bind("<<Decrement>>", self.apply_filters)

        # Filtro por rareza
        ttk.Label(self.filter_frame, text="Rareza:").grid(row=0, column=6, padx=5, pady=2)
        self.rarity_filter = ttk.Combobox(self.filter_frame, values=list(RARITY_MAPPING.keys()), state="readonly", width=15)
        self.rarity_filter.grid(row=0, column=7, padx=5, pady=2)
        self.rarity_filter.set("Todos")
        self.rarity_filter.bind("<<ComboboxSelected>>", self.apply_filters)

        # Filtro por tipo
        ttk.Label(self.filter_frame, text="Tipo:").grid(row=0, column=8, padx=5, pady=2)
        self.type_filter = ttk.Combobox(self.filter_frame, values=list(TYPE_MAPPING.keys()), state="readonly", width=12)
        self.type_filter.grid(row=0, column=9, padx=5, pady=2)
        self.type_filter.set("Todos")
        self.type_filter.bind("<<ComboboxSelected>>", self.apply_filters)

        # Botón de exportación
        ttk.Button(self.filter_frame, text="Exportar a CSV", command=self.export_to_csv).grid(row=0, column=10, padx=5, pady=2)

        # Botón de borrar filtros
        ttk.Button(self.filter_frame, text="Borrar Filtros", command=self.clear_filters).grid(row=0, column=11, padx=5, pady=2)

        # Frame principal para lista y detalles
        self.list_main_frame = ttk.Frame(self.list_frame)
        self.list_main_frame.pack(fill="both", expand=True)

        # Lista de cartas
        self.listbox = tk.Listbox(self.list_main_frame, width=30, height=20)
        self.listbox.grid(row=0, column=0, padx=5, pady=5, sticky="ns")
        self.update_listbox()
        self.listbox.bind("<<ListboxSelect>>", self.show_card_details)
        self.listbox.bind("<Double-1>", self.edit_quantity)

        # Frame para detalles
        self.details_frame = ttk.LabelFrame(self.list_main_frame, text="Detalles", padding="10")
        self.details_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        # Etiquetas para detalles
        self.card_id_label = ttk.Label(self.details_frame, text="ID: ")
        self.card_id_label.grid(row=0, column=0, sticky="w")
        self.name_label = ttk.Label(self.details_frame, text="Nombre: ")
        self.name_label.grid(row=1, column=0, sticky="w")
        self.set_name_label = ttk.Label(self.details_frame, text="Conjunto: ")
        self.set_name_label.grid(row=2, column=0, sticky="w")
        self.quantity_label = ttk.Label(self.details_frame, text="Cantidad: ")
        self.quantity_label.grid(row=3, column=0, sticky="w")
        self.rarity_label = ttk.Label(self.details_frame, text="Rareza: ")
        self.rarity_label.grid(row=4, column=0, sticky="w")
        self.type_label = ttk.Label(self.details_frame, text="Tipo: ")
        self.type_label.grid(row=5, column=0, sticky="w")
        self.supertype_label = ttk.Label(self.details_frame, text="Supertipo: ")
        self.supertype_label.grid(row=6, column=0, sticky="w")

        # Campo para editar cantidad
        ttk.Label(self.details_frame, text="Nueva Cantidad:").grid(row=7, column=0, sticky="w", pady=5)
        self.quantity_entry = ttk.Spinbox(self.details_frame, from_=0, to=999, width=5)
        self.quantity_entry.grid(row=8, column=0, sticky="w")
        ttk.Button(self.details_frame, text="Actualizar Cantidad", command=self.save_quantity).grid(row=9, column=0, pady=5)

        # Área para la imagen
        self.image_label = ttk.Label(self.details_frame)
        self.image_label.grid(row=10, column=0, pady=10)

        # Configurar el tamaño
        self.list_main_frame.columnconfigure(1, weight=1)
        self.list_main_frame.rowconfigure(0, weight=1)

    def setup_decks_tab(self):
        # Frame principal para la pestaña de mazos
        self.decks_main_frame = ttk.Frame(self.decks_frame)
        self.decks_main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Botones para importar y borrar mazos
        ttk.Button(self.decks_main_frame, text="Importar Nuevo Mazo", command=self.open_import_deck_window).pack(pady=5)
        ttk.Button(self.decks_main_frame, text="Borrar Mazo", command=self.delete_selected_deck).pack(pady=5)

        # Lista de mazos guardados
        ttk.Label(self.decks_main_frame, text="Mazos Guardados:").pack(pady=5)
        self.decks_listbox = tk.Listbox(self.decks_main_frame, width=30, height=20)
        self.decks_listbox.pack(side="left", padx=5, pady=5)
        self.decks_listbox.bind("<<ListboxSelect>>", self.show_deck_cards)

        # Frame derecho para Canvas y resumen
        self.right_frame = ttk.Frame(self.decks_main_frame)
        self.right_frame.pack(side="left", fill="both", expand=True)

        # Canvas para mostrar las cartas del mazo
        self.deck_canvas = tk.Canvas(self.right_frame)
        self.deck_scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.deck_canvas.yview)
        self.deck_canvas.configure(yscrollcommand=self.deck_scrollbar.set)

        self.deck_scrollbar.pack(side="right", fill="y")
        self.deck_canvas.pack(fill="both", expand=True)

        self.deck_inner_frame = ttk.Frame(self.deck_canvas)
        self.deck_canvas.create_window((0, 0), window=self.deck_inner_frame, anchor="nw")

        # Frame para el resumen
        self.summary_frame = ttk.LabelFrame(self.right_frame, text="Resumen del Mazo", padding="5")
        self.summary_frame.pack(fill="x", pady=5)

        self.pokemon_summary = ttk.Label(self.summary_frame, text="Pokémon: 0")
        self.pokemon_summary.pack(anchor="w")
        self.trainer_summary = ttk.Label(self.summary_frame, text="Entrenador: 0")
        self.trainer_summary.pack(anchor="w")
        self.energy_summary = ttk.Label(self.summary_frame, text="Energías: 0")
        self.energy_summary.pack(anchor="w")
        self.energy_details = ttk.Label(self.summary_frame, text="")
        self.energy_details.pack(anchor="w")

        # Configurar el desplazamiento
        self.deck_inner_frame.bind("<Configure>", lambda e: self.deck_canvas.configure(scrollregion=self.deck_canvas.bbox("all")))
        self.deck_canvas.bind_all("<MouseWheel>", lambda e: self.deck_canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Cargar mazos existentes
        self.update_decks_listbox()

    def open_import_deck_window(self):
        import_window = tk.Toplevel(self.root)
        import_window.title("Importar Nuevo Mazo")
        import_window.geometry("400x500")

        ttk.Label(import_window, text="Nombre del Mazo:").pack(pady=5)
        deck_name_entry = ttk.Entry(import_window, width=50)
        deck_name_entry.pack(pady=5)

        ttk.Label(import_window, text="Pega el mazo aquí (formato texto plano):").pack(pady=5)
        deck_text = tk.Text(import_window, height=20, width=50)
        deck_text.pack(pady=5)

        ttk.Button(import_window, text="Importar desde Portapapeles", command=lambda: self.import_from_clipboard(deck_text)).pack(pady=5)
        ttk.Button(import_window, text="Guardar Mazo", command=lambda: self.save_deck_from_window(deck_name_entry, deck_text, import_window)).pack(pady=5)

    def import_from_clipboard(self, text_widget):
        try:
            clipboard_text = self.root.clipboard_get()
            text_widget.delete("1.0", tk.END)
            text_widget.insert("1.0", clipboard_text)
        except tk.TclError:
            messagebox.showerror("Error", "No hay texto en el portapapeles.")

    def save_deck_from_window(self, name_entry, text_widget, window):
        deck_name = name_entry.get().strip()
        deck_text = text_widget.get("1.0", tk.END).strip()

        if not deck_name:
            messagebox.showwarning("Advertencia", "Introduce un nombre para el mazo.")
            return
        if not deck_text:
            messagebox.showwarning("Advertencia", "El texto del mazo está vacío.")
            return

        save_deck(deck_name, deck_text)
        self.update_decks_listbox()
        messagebox.showinfo("Éxito", f"Mazo '{deck_name}' guardado correctamente.")
        window.destroy()

    def delete_selected_deck(self):
        selection = self.decks_listbox.curselection()
        if not selection:
            messagebox.showwarning("Advertencia", "Selecciona un mazo para borrar.")
            return
        
        index = selection[0]
        decks = load_decks()
        deck_id = decks[index][0]
        deck_name = decks[index][1]

        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres borrar el mazo '{deck_name}'?"):
            delete_deck(deck_id)
            self.update_decks_listbox()
            for widget in self.deck_inner_frame.winfo_children():
                widget.destroy()
            self.update_summary(0, 0, 0, {})
            messagebox.showinfo("Éxito", f"Mazo '{deck_name}' borrado.")

    def update_decks_listbox(self):
        self.decks_listbox.delete(0, tk.END)
        decks = load_decks()
        for deck in decks:
            deck_id, deck_name, _ = deck
            self.decks_listbox.insert(tk.END, f"{deck_id}: {deck_name}")

    def show_deck_cards(self, event):
        selection = self.decks_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        decks = load_decks()
        deck = decks[index]
        _, _, deck_text = deck

        # Parsear el texto del mazo
        cards = self.parse_deck_text(deck_text)

        # Contar Pokémon, Entrenadores y Energías
        pokemon_count = 0
        trainer_count = 0
        energy_count = 0
        energy_types = {}

        card_dict = {card[0]: card[6] for card in self.all_cards}  # card_id: supertype

        for qty, name, set_code, number in cards:
            api_set_code = SET_MAPPING.get(set_code.upper(), set_code.lower())
            card_id = f"{api_set_code}-{number}"
            supertype = card_dict.get(card_id, None)

            # Si no está en card_dict, deducir supertype del nombre
            if supertype is None:
                if "Energy" in name:
                    supertype = "Energy"
                elif set_code in SET_MAPPING:  # Aproximación para Pokémon
                    supertype = "Pokémon"
                else:
                    supertype = "Trainer"  # Aproximación para Entrenadores

            if supertype == "Pokémon":
                pokemon_count += qty
            elif supertype == "Trainer":
                trainer_count += qty
            elif supertype == "Energy":
                energy_count += qty
                energy_name = name.split(" Energy")[0] if " Energy" in name else name
                energy_types[energy_name] = energy_types.get(energy_name, 0) + qty

        # Actualizar el resumen
        self.update_summary(pokemon_count, trainer_count, energy_count, energy_types)

        # Mostrar todas las cartas en el Canvas
        for widget in self.deck_inner_frame.winfo_children():
            widget.destroy()
        self.photos = []

        cols = 5
        row = 0
        col = 0
        for qty, name, set_code, number in cards:
            api_set_code = SET_MAPPING.get(set_code.upper(), set_code.lower())
            card_id = f"{api_set_code}-{number}"
            image_path = os.path.join(IMAGE_FOLDER, f"{card_id}.png")
            if os.path.exists(image_path):
                img = Image.open(image_path)
                img = img.resize((120, 168), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.photos.append(photo)

                card_frame = ttk.Frame(self.deck_inner_frame)
                card_frame.grid(row=row, column=col, padx=2, pady=2)

                img_label = ttk.Label(card_frame, image=photo)
                img_label.pack()

                ttk.Label(card_frame, text=f"{name}", wraplength=110).pack()
                ttk.Label(card_frame, text=f"Cant: {qty}").pack()

                col += 1
                if col >= cols:
                    col = 0
                    row += 1
            else:
                print(f"Imagen no encontrada: {image_path}")

    def update_summary(self, pokemon_count, trainer_count, energy_count, energy_types):
        self.pokemon_summary.config(text=f"Pokémon: {pokemon_count}")
        self.trainer_summary.config(text=f"Entrenador: {trainer_count}")
        self.energy_summary.config(text=f"Energías: {energy_count}")
        energy_text = "\n".join([f"  {name}: {qty}" for name, qty in energy_types.items()])
        self.energy_details.config(text=energy_text if energy_text else "  Ninguna")

    def parse_deck_text(self, deck_text):
        cards = []
        lines = deck_text.splitlines()
        for line in lines:
            line = line.strip()
            match = re.match(r"(\d+)\s+(.+?)\s+([A-Za-z0-9]+)\s+(\d+)$", line)
            if match:
                qty, name, set_code, number = match.groups()
                cards.append((int(qty), name, set_code, number))
        return cards

    def apply_filters(self, event=None):
        name_text = self.name_filter.get().lower()
        set_choice = self.set_filter.get()
        min_quantity = int(self.quantity_filter.get())
        rarity_choice = self.rarity_filter.get()
        rarity_value = RARITY_MAPPING[rarity_choice]
        type_choice = self.type_filter.get()
        type_value = TYPE_MAPPING[type_choice]

        self.filtered_cards = []
        for card in self.all_cards:
            card_id, name, set_name, quantity, rarity, card_type, _ = card
            if name_text and name_text not in name.lower():
                continue
            if set_choice != "Todos" and set_choice != set_name:
                continue
            if quantity < min_quantity:
                continue
            if rarity_value and rarity_value != rarity:
                continue
            if type_value is not None and type_value != card_type:
                continue
            self.filtered_cards.append(card)

        self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for i, card in enumerate(self.filtered_cards):
            card_id, name, _, quantity, _, _, _ = card
            display_text = f"{card_id} - {name}"
            self.listbox.insert(tk.END, display_text)
            if quantity == 0:
                self.listbox.itemconfig(i, {'fg': 'gray'})
            else:
                self.listbox.itemconfig(i, {'fg': 'black'})

    def show_card_details(self, event):
        selection = self.listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        card = self.filtered_cards[index]
        self.display_card_details(card)

    def edit_quantity(self, event):
        self.show_card_details(event)

    def display_card_details(self, card):
        card_id, name, set_name, quantity, rarity, card_type, supertype = card
        self.current_card_id = card_id
        self.card_id_label.config(text=f"ID: {card_id}")
        self.name_label.config(text=f"Nombre: {name}")
        self.set_name_label.config(text=f"Conjunto: {set_name}")
        self.quantity_label.config(text=f"Cantidad: {quantity}")
        self.rarity_label.config(text=f"Rareza: {rarity or 'N/A'}")
        
        # Determinar el tipo para energías basado en el nombre
        if supertype == "Energy":
            # Extraer el tipo de energía del nombre
            energy_type = name.split(" Energy")[0] if " Energy" in name else name
            self.type_label.config(text=f"Tipo: {energy_type}")
        else:
            self.type_label.config(text=f"Tipo: {card_type or 'N/A'}")
        
        self.supertype_label.config(text=f"Supertipo: {supertype or 'N/A'}")
        self.quantity_entry.delete(0, tk.END)
        self.quantity_entry.insert(0, quantity)

        image_path = os.path.join(IMAGE_FOLDER, f"{card_id}.png")
        if os.path.exists(image_path):
            img = Image.open(image_path)
            img = img.resize((200, 280), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=photo)
            self.image_label.image = photo
        else:
            self.image_label.config(image="", text="Imagen no encontrada")

    def save_quantity(self):
        if not self.current_card_id:
            messagebox.showwarning("Advertencia", "Selecciona una carta primero.")
            return
        
        try:
            new_quantity = int(self.quantity_entry.get())
            if new_quantity < 0:
                raise ValueError("La cantidad no puede ser negativa.")
            
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT quantity FROM my_collection WHERE card_id = ?", (self.current_card_id,))
            current_quantity = cursor.fetchone()[0]
            conn.close()

            if new_quantity != current_quantity:
                update_quantity(self.current_card_id, new_quantity)
                self.all_cards = [(c[0], c[1], c[2], new_quantity if c[0] == self.current_card_id else c[3], c[4], c[5], c[6]) for c in self.all_cards]
                self.filtered_cards = [(c[0], c[1], c[2], new_quantity if c[0] == self.current_card_id else c[3], c[4], c[5], c[6]) for c in self.filtered_cards]
                self.quantity_label.config(text=f"Cantidad: {new_quantity}")
                self.update_listbox()
                messagebox.showinfo("Éxito", f"Cantidad de {self.current_card_id} actualizada a {new_quantity}.")
            else:
                messagebox.showinfo("Sin cambios", f"La cantidad de {self.current_card_id} ya es {new_quantity}.")
        
        except ValueError as e:
            messagebox.showerror("Error", str(e) if str(e) != "" else "Por favor, ingresa un número válido.")

    def export_to_csv(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        SELECT c.card_id, c.name, c.set_name, m.quantity, c.rarity, c.type
        FROM cards c
        JOIN my_collection m ON c.card_id = m.card_id
        WHERE m.quantity > 0
        ORDER BY c.set_id, CAST(c.number AS INTEGER)
        """)
        cards_to_export = cursor.fetchall()
        conn.close()

        with open("coleccion.csv", "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Nombre", "Conjunto", "Cantidad", "Rareza", "Tipo"])
            for card in cards_to_export:
                writer.writerow(card)
        messagebox.showinfo("Éxito", "Colección exportada a coleccion.csv")

    def clear_filters(self):
        self.name_filter.delete(0, tk.END)
        self.set_filter.set("Todos")
        self.quantity_filter.set(0)
        self.rarity_filter.set("Todos")
        self.type_filter.set("Todos")
        self.apply_filters()

# Iniciar la aplicación
if __name__ == "__main__":
    root = tk.Tk()
    app = CardApp(root)
    root.mainloop()