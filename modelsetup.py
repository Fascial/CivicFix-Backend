import base64
import requests


class Classifier:
    def __init__(
        self, model_url="http://localhost:11434/api/generate", model_name="gemma3"
    ):
        self.model_url = model_url
        self.model_name = model_name

        with open("information.txt", "r") as file:
            self.information = file.read()

    def encode_image(self, image_path):
        with open(image_path, "rb") as img:
            return base64.b64encode(img.read()).decode("utf-8")

    def classify(self, image_path, image_description=None):
        image_data = self.encode_image(image_path)

        prompt = f"""
            {self.information}
            Image Captions according to user: {image_description}
            The user description might sometimes be incomplete or faulty
        """

        response = requests.post(
            self.model_url,
            json={
                "model": self.model_name,
                "prompt": prompt,
                "images": [image_data],
                "stream": False,
            },
        )

        return response.json()["response"].strip()
