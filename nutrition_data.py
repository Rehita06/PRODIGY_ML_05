"""Approximate nutrition reference for the 101 Food-101 classes.

IMPORTANT: these are rough, typical values for a prepared dish, compiled for this
student project from general nutrition knowledge. They are NOT laboratory values and
recipes vary a lot. Check against USDA FoodData Central (or IFCT for Indian foods)
before relying on them, and say so when you present the project.

Format per class: (kcal, protein_g, carbs_g, fat_g, typical_serving_g)
The first four numbers are per 100 g of the prepared food.
"""

NUTRITION_PER_100G = {
    "apple_pie": (237, 1.9, 34, 11, 125),
    "baby_back_ribs": (290, 22, 5, 20, 250),
    "baklava": (428, 6, 45, 25, 60),
    "beef_carpaccio": (150, 20, 1, 7, 100),
    "beef_tartare": (190, 20, 2, 11, 120),
    "beet_salad": (70, 2, 9, 3, 200),
    "beignets": (360, 6, 43, 18, 80),
    "bibimbap": (140, 6, 20, 3.5, 400),
    "bread_pudding": (190, 5, 28, 6.5, 150),
    "breakfast_burrito": (210, 9, 22, 9, 200),
    "bruschetta": (190, 5, 25, 8, 100),
    "caesar_salad": (120, 4, 6, 9, 200),
    "cannoli": (330, 6, 38, 17, 80),
    "caprese_salad": (140, 8, 3, 11, 150),
    "carrot_cake": (400, 4, 48, 22, 110),
    "ceviche": (100, 15, 5, 2, 150),
    "cheese_plate": (370, 21, 4, 30, 80),
    "cheesecake": (321, 5.5, 26, 23, 120),
    "chicken_curry": (150, 12, 5, 9, 250),
    "chicken_quesadilla": (270, 15, 24, 13, 180),
    "chicken_wings": (300, 24, 3, 21, 150),
    "chocolate_cake": (370, 5, 50, 17, 100),
    "chocolate_mousse": (225, 4, 22, 14, 120),
    "churros": (390, 5, 45, 21, 80),
    "clam_chowder": (100, 4, 9, 5, 250),
    "club_sandwich": (240, 14, 20, 11, 250),
    "crab_cakes": (200, 14, 10, 11, 120),
    "creme_brulee": (290, 4, 24, 20, 130),
    "croque_madame": (270, 15, 20, 14, 250),
    "cup_cakes": (390, 3.5, 55, 17, 80),
    "deviled_eggs": (200, 10, 2, 17, 80),
    "donuts": (410, 5, 49, 22, 70),
    "dumplings": (200, 8, 25, 7, 150),
    "edamame": (120, 11, 9, 5, 150),
    "eggs_benedict": (230, 11, 13, 15, 200),
    "escargots": (180, 12, 3, 13, 100),
    "falafel": (330, 13, 32, 18, 100),
    "filet_mignon": (250, 26, 0, 16, 170),
    "fish_and_chips": (240, 10, 22, 13, 350),
    "foie_gras": (460, 11, 5, 44, 50),
    "french_fries": (310, 3.5, 40, 15, 120),
    "french_onion_soup": (100, 5, 9, 5, 300),
    "french_toast": (230, 8, 25, 11, 130),
    "fried_calamari": (220, 15, 17, 10, 150),
    "fried_rice": (163, 4.5, 25, 5, 250),
    "frozen_yogurt": (160, 4, 30, 3, 120),
    "garlic_bread": (350, 8, 45, 15, 60),
    "gnocchi": (140, 4, 25, 3, 200),
    "greek_salad": (100, 3, 6, 8, 250),
    "grilled_cheese_sandwich": (360, 14, 28, 21, 130),
    "grilled_salmon": (208, 22, 0, 13, 150),
    "guacamole": (160, 2, 9, 15, 60),
    "gyoza": (210, 8, 24, 8, 120),
    "hamburger": (250, 13, 24, 11, 200),
    "hot_and_sour_soup": (45, 3, 5, 1.5, 250),
    "hot_dog": (290, 10, 23, 17, 120),
    "huevos_rancheros": (150, 8, 13, 8, 300),
    "hummus": (166, 8, 14, 10, 60),
    "ice_cream": (207, 3.5, 24, 11, 100),
    "lasagna": (160, 9, 15, 7, 300),
    "lobster_bisque": (100, 5, 6, 6, 250),
    "lobster_roll_sandwich": (210, 14, 19, 9, 200),
    "macaroni_and_cheese": (190, 8, 20, 8, 250),
    "macarons": (400, 7, 60, 16, 30),
    "miso_soup": (40, 3, 5, 1.3, 240),
    "mussels": (100, 13, 5, 3, 150),
    "nachos": (340, 10, 35, 18, 200),
    "omelette": (160, 11, 2, 12, 150),
    "onion_rings": (330, 4, 38, 18, 100),
    "oysters": (70, 8, 5, 2.5, 100),
    "pad_thai": (170, 7, 22, 6, 300),
    "paella": (150, 9, 19, 4, 300),
    "pancakes": (230, 6, 28, 10, 150),
    "panna_cotta": (200, 3, 22, 12, 120),
    "peking_duck": (330, 19, 1, 28, 120),
    "pho": (70, 5, 9, 1.5, 550),
    "pizza": (266, 11, 33, 10, 120),
    "pork_chop": (230, 24, 0, 15, 150),
    "poutine": (220, 6, 23, 12, 300),
    "prime_rib": (280, 24, 0, 20, 200),
    "pulled_pork_sandwich": (230, 15, 23, 8, 220),
    "ramen": (95, 5, 14, 3, 500),
    "ravioli": (190, 8, 26, 6, 200),
    "red_velvet_cake": (380, 4, 50, 19, 110),
    "risotto": (150, 4, 22, 5, 250),
    "samosa": (260, 5, 28, 15, 60),
    "sashimi": (150, 22, 0, 6, 100),
    "scallops": (130, 20, 3, 3, 100),
    "seaweed_salad": (110, 2, 15, 5, 100),
    "shrimp_and_grits": (150, 9, 16, 6, 300),
    "spaghetti_bolognese": (140, 7, 18, 4, 300),
    "spaghetti_carbonara": (190, 8, 22, 8, 300),
    "spring_rolls": (190, 5, 25, 8, 100),
    "steak": (250, 26, 0, 17, 200),
    "strawberry_shortcake": (250, 3, 35, 11, 140),
    "sushi": (145, 5, 28, 1.5, 150),
    "tacos": (220, 10, 20, 11, 150),
    "takoyaki": (190, 7, 22, 8, 120),
    "tiramisu": (280, 5, 30, 16, 120),
    "tuna_tartare": (130, 22, 2, 4, 100),
    "waffles": (290, 7, 34, 14, 100),
}


def normalize_label(label):
    """'Apple Pie' or 'apple_pie' -> 'apple_pie'."""
    return str(label).strip().lower().replace(" ", "_").replace("-", "_")


def lookup(label):
    """Return the per-100g record for a label, or None if it is not in the table."""
    row = NUTRITION_PER_100G.get(normalize_label(label))
    if row is None:
        return None
    kcal, protein, carbs, fat, serving = row
    return {"kcal": kcal, "protein_g": protein, "carbs_g": carbs, "fat_g": fat, "serving_g": serving}


def estimate_for_portion(label, grams):
    """Scale the per-100g values to a portion in grams. Returns None for unknown labels."""
    record = lookup(label)
    if record is None or grams <= 0:
        return None
    factor = grams / 100.0
    return {
        "grams": grams,
        "calories": round(record["kcal"] * factor),
        "protein_g": round(record["protein_g"] * factor, 1),
        "carbs_g": round(record["carbs_g"] * factor, 1),
        "fat_g": round(record["fat_g"] * factor, 1),
    }
