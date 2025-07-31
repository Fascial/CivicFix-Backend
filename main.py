import os
import time
import requests
import firebase_admin
from modelsetup import Classifier
from firebase_admin import credentials, firestore


def process_unresolved_issue(doc, db, image_folder, classifier):
    data = doc.to_dict()
    issue_id = doc.id
    image_url = data.get("imageUrl")
    image_description = data.get("description", "")
    if not image_url:
        print(f"No image URL for issue {issue_id}")
        return

    try:
        response = requests.get(image_url)
        response.raise_for_status()
        ext = os.path.splitext(image_url.split("?")[0])[-1] or ".jpg"
        if not ext.startswith("."):
            ext = ".jpg"
        image_path = os.path.join(image_folder, f"{issue_id}{ext}")
        with open(image_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded image for {issue_id} to {image_path}")
    except Exception as e:
        print(f"Failed to download image for {issue_id}: {e}")
        return

    try:
        department = classifier.classify(image_path, image_description)
        print(f"Classifier output for {issue_id}: {department}")
    except Exception as e:
        print(f"Classifier failed for {issue_id}: {e}")
        if os.path.exists(image_path):
            os.remove(image_path)
        return

    data["department_assigned"] = department
    data["status"] = "In Progress"

    try:
        # Add to in_progress_issues collection
        db.collection("in_progress_issues").document(issue_id).set(data)
        print(f"Transferred {issue_id} to in_progress_issues.")

        # Delete from issues collection
        db.collection("issues").document(issue_id).delete()
        print(f"Deleted {issue_id} from issues collection.")
    except Exception as e:
        print(f"Failed to transfer or delete issue {issue_id}: {e}")
        import traceback

        traceback.print_exc()

    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"Deleted image file {image_path}")
    except Exception as e:
        print(f"Failed to delete image file {image_path}: {e}")


if __name__ == "__main__":
    cred = credentials.Certificate("service_key.json")
    firebase_admin.initialize_app(cred)

    db = firestore.client()
    image_folder = "downloaded_images"
    os.makedirs(image_folder, exist_ok=True)
    classifier = Classifier()

    processed_ids = set()

    print("Monitoring Firestore for unresolved issues...")
    while True:
        issues_ref = db.collection("issues")
        docs = issues_ref.where("status", "==", "Unresolved").stream()
        for doc in docs:
            if doc.id not in processed_ids:
                process_unresolved_issue(doc, db, image_folder, classifier)
                processed_ids.add(doc.id)
        time.sleep(2)
