# ==============================================================================
# src/gcs_io.py
# ==============================================================================
# This module provides utility functions for interacting with Google Cloud Storage (GCS).
# It handles downloading files from a GCS bucket to a local directory.

from google.cloud import storage
import os

def download_gcs_files(bucket_name, gcs_folder_prefix, local_dir):
    """
    Downloads all files from a specified GCS folder to a local directory.

    Args:
        bucket_name (str): Name of the GCS bucket.
        gcs_folder_prefix (str): Prefix of the folder in GCS (e.g., 'gee_exports/sentinel2_exports/').
        local_dir (str): Local directory path to save the files.
    """
    print(f"Attempting to download files from gs://{bucket_name}/{gcs_folder_prefix} to {local_dir}")
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    blobs = bucket.list_blobs(prefix=gcs_folder_prefix) # List blobs in the specified folder

    os.makedirs(local_dir, exist_ok=True) # Ensure local directory exists

    downloaded_count = 0
    for blob in blobs:
        # Construct the full local file path
        # Remove the folder prefix from the blob name to avoid creating nested folders locally
        local_file_path = os.path.join(local_dir, os.path.basename(blob.name))

        if blob.name.endswith('/'): # Skip directories
            continue

        if os.path.exists(local_file_path):
            # print(f"  Skipping existing file: {local_file_path}")
            continue

        try:
            blob.download_to_filename(local_file_path)
            print(f"  Downloaded {blob.name} to {local_file_path}")
            downloaded_count += 1
        except Exception as e:
            print(f"  Error downloading {blob.name}: {e}")

    print(f"Finished downloading. {downloaded_count} new files downloaded.")
