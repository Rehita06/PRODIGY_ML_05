
from PIL import Image
from transformers import pipeline

print("Loading pretrained food classifier...")

classifier = pipeline(
    "image-classification",
    model="yfh/food"
)

image = Image.open("test_food.jpg").convert("RGB")
predictions = classifier(image, top_k=3)

for prediction in predictions:
    print(
        prediction["label"],
        f'{prediction["score"]:.2%}'
    )
