import firebase_admin
from firebase_admin import credentials, firestore
import requests
import os
from urllib.parse import urlparse

# Initialize Firebase Admin
cred = credentials.Certificate(r"service_key.json")
firebase_admin.initialize_app(cred)

# Get Firestore client
db = firestore.client()

# Folder to save images
save_folder = r"downloaded_images"


# Create folder if it doesn't exist
os.makedirs(save_folder, exist_ok=True)


# Get all issues
issues_ref = db.collection("issues")
docs = issues_ref.stream()


def handle_unresolved_issue(issue_id, data):
    # Your custom logic here
    print(f"Handling unresolved issue: {issue_id}")
    # For example, send a notification, log, etc.


print("\nDownloading issue images...")

for doc in docs:
    data = doc.to_dict()
    issue_id = doc.id
    image_url = data.get("imageUrl")
    status = data.get("status")  # Assuming 'status' is the field name

    if status == "Unresolved":
        handle_unresolved_issue(issue_id, data)

    print(image_url)

    if image_url:
        try:
            response = requests.get(image_url)
            response.raise_for_status()  # Check for errors

            # SAFELY extract clean extension WITHOUT query params
            parsed_url = urlparse(image_url)
            path = parsed_url.path  # path only, no query
            file_ext = os.path.splitext(path)[-1] or ".jpg"

            # If no extension found, default to .jpg
            if not file_ext.startswith("."):
                file_ext = ".jpg"

            filename = f"{issue_id}{file_ext}"
            filepath = os.path.join(save_folder, filename)

            # Write image to file
            with open(filepath, "wb") as f:
                f.write(response.content)

            print(f"Downloaded image for {issue_id} => {filepath}")

        except Exception as e:
            print(f"Failed to download image for {issue_id}: {e}")
    else:
        print(f"No imageUrl for {issue_id}")

print("\nDone.")
