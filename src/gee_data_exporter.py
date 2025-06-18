# ==============================================================================
# src/gee_data_exporter.py
# ==============================================================================
# This module provides functions for exporting data from Google Earth Engine (GEE)
# to Google Cloud Storage (GCS). It includes functionalities for Sentinel-2, ERA5-Land,
# SRTM DEM, and SMAP data exports, handling image collection processing and
# aggregation over administrative boundaries.

import ee
from google.cloud import storage
import pandas as pd
import numpy as np
import os
import time

def cloud_mask_s2(image):
    """
    Masks clouds and shadows from Sentinel-2 imagery using the QA60 band.
    """
    qa = image.select('QA60')
    # Bits 10 and 11 are clouds and cirrus, respectively.
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11
    mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(
           qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    return image.updateMask(mask).divide(10000) # Scale to 0-1 range

def add_NDVI_SAVI(image):
    """
    Adds Normalized Difference Vegetation Index (NDVI) and Soil Adjusted Vegetation Index (SAVI)
    bands to a Sentinel-2 image.
    """
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    # SAVI: (NIR - RED) * (1 + L) / (NIR + RED + L), L=0.5 for intermediate vegetation density
    savi = image.expression(
        '(NIR - RED) * (1 + L) / (NIR + RED + L)', {
            'NIR': image.select('B8'),
            'RED': image.select('B4'),
            'L': 0.5
        }).rename('SAVI')
    return image.addBands(ndvi).addBands(savi)

def export_image_collection_by_feature(
    collection,
    feature_collection,
    reducer,
    scale,
    bucket_name,
    folder_name,
    prefix,
    start_date,
    end_date,
    band_names=None,
    tile_scale=4,
    max_pixels=1e13
):
    """
    Exports aggregated statistics from an Earth Engine ImageCollection for each feature
    in a FeatureCollection to Google Cloud Storage.

    Args:
        collection (ee.ImageCollection): The GEE ImageCollection to process.
        feature_collection (ee.FeatureCollection): The GEE FeatureCollection (e.g., woredas).
        reducer (ee.Reducer): The GEE reducer to apply (e.g., ee.Reducer.mean()).
        scale (int): The nominal scale in meters of the projection to work in.
        bucket_name (str): Name of the GCS bucket.
        folder_name (str): Folder within the GCS bucket to save outputs.
        prefix (str): Prefix for the exported file names (e.g., 'sentinel2_').
        start_date (str): Start date for the image collection (YYYY-MM-DD).
        end_date (str): End date for the image collection (YYYY-MM-DD).
        band_names (list, optional): List of band names to select before reducing.
        tile_scale (int): A scaling factor used to reduce aggregation contention.
        max_pixels (int): The maximum number of pixels to reduce.
    """
    def export_for_feature(feature):
        feature_id = feature.get('Woreda_ID').getInfo() # Assuming 'Woreda_ID' is consistent
        feature_name = feature.get('Woreda Name').getInfo() # Assuming 'Woreda Name' is consistent
        print(f"Processing Woreda: {feature_name} (ID: {feature_id})")

        # Filter the collection by date and geometry
        filtered_collection = collection.filterDate(start_date, end_date) \
                                        .filterBounds(feature.geometry())

        if band_names:
            filtered_collection = filtered_collection.select(band_names)

        # Map the reducer over the collection to get statistics per image
        def reduce_image(image):
            # Reduce the image over the feature's geometry
            stats = image.reduceRegion(
                reducer=reducer,
                geometry=feature.geometry(),
                scale=scale,
                tileScale=tile_scale,
                maxPixels=max_pixels
            )
            # Add properties to the dictionary including feature ID and date
            return ee.Feature(None, stats).set({
                'Woreda_ID': feature_id,
                'Woreda Name': feature_name,
                'year': image.date().get('year'),
                'month': image.date().get('month'),
                'day': image.date().get('day') # Not always available for monthly aggregates, check reducer
            })

        reduced_features = filtered_collection.map(reduce_image)

        # Export the FeatureCollection to GCS as a CSV
        task = ee.batch.Export.table.toCloudStorage(
            collection=reduced_features,
            description=f'{prefix}{feature_id}_export',
            bucket=bucket_name,
            fileNamePrefix=f'{folder_name}/{prefix}{feature_id}',
            fileFormat='CSV'
        )
        task.start()
        print(f"  Export task for {feature_name} ({feature_id}) started.")
        return task

    tasks = []
    # Convert ee.FeatureCollection to a list to iterate over
    feature_list = feature_collection.toList(feature_collection.size()).getInfo()
    for f_info in feature_list:
        f = ee.Feature(f_info)
        tasks.append(export_for_feature(f))

    print(f"Started {len(tasks)} export tasks.")
    return tasks

def monitor_tasks(tasks, polling_interval=30):
    """
    Monitors a list of Earth Engine tasks and prints their status.
    Returns True if all tasks succeeded, False otherwise.
    """
    print(f"\nMonitoring {len(tasks)} tasks...")
    active_tasks = list(tasks)
    while active_tasks:
        for task in list(active_tasks): # Iterate over a copy to allow modification
            status = task.status()
            task_id = task.id
            state = status['state']
            description = status['description']

            if state == 'COMPLETED':
                print(f"  Task {description} ({task_id}) - COMPLETED")
                active_tasks.remove(task)
            elif state == 'FAILED':
                print(f"  Task {description} ({task_id}) - FAILED. Error: {status.get('error_message', 'No error message.')}")
                active_tasks.remove(task)
            elif state in ['READY', 'RUNNING']:
                # print(f"  Task {description} ({task_id}) - {state}...")
                pass # Suppress constant output for active tasks
            else:
                print(f"  Task {description} ({task_id}) - Unknown state: {state}")
                active_tasks.remove(task) # Remove to avoid infinite loop on unknown state

        if active_tasks:
            print(f"  {len(active_tasks)} tasks still active. Waiting {polling_interval} seconds...")
            time.sleep(polling_interval)
    print("\nAll tasks monitored. Check individual task statuses above.")
    return all(task.status()['state'] == 'COMPLETED' for task in tasks)
