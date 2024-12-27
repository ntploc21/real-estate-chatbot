import base64

DATA_FULL_DIR = "/app/data-full"


def image_to_base64(image_path):
    parts = image_path.split("/")
    image_path = f"{DATA_FULL_DIR}/images/{parts[-2]}/{parts[-1]}"
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string
