# ==============================================================================
# src/geospatial_processing.py
# ==============================================================================
# This module contains functions for local geospatial data processing,
# specifically focused on raster operations like masking and statistics extraction.

import rasterio
import rasterio.mask
import numpy as np
import geopandas as gpd
from rasterio.features import geometry_mask
import os

def mask_raster_with_polygon(raster_path, polygon_gdf, output_path):
    """
    Masks a raster file using a GeoDataFrame of polygons.

    Args:
        raster_path (str): Path to the input raster file.
        polygon_gdf (geopandas.GeoDataFrame): GeoDataFrame containing the polygons.
        output_path (str): Path to save the masked raster.
    Returns:
        bool: True if masking was successful, False otherwise.
    """
    try:
        with rasterio.open(raster_path) as src:
            out_image, out_transform = rasterio.mask.mask(src, polygon_gdf.geometry, crop=True)
            out_meta = src.meta.copy()

            out_meta.update({"driver": "GTiff",
                             "height": out_image.shape[1],
                             "width": out_image.shape[2],
                             "transform": out_transform})

            with rasterio.open(output_path, "w", **out_meta) as dest:
                dest.write(out_image)
        return True
    except Exception as e:
        print(f"Error masking raster {raster_path} with polygons: {e}")
        return False

def calculate_masked_raster_stats(raster_path, mask_raster_path):
    """
    Calculates mean, min, max, std from a raster, considering a mask raster.
    Only pixels where the mask raster has a value > 0 are considered.

    Args:
        raster_path (str): Path to the input data raster file.
        mask_raster_path (str): Path to the mask raster file (e.g., coffee extent).
    Returns:
        dict: Dictionary of statistics (mean, min, max, std) or None if error.
    """
    try:
        with rasterio.open(raster_path) as src_data,\
             rasterio.open(mask_raster_path) as src_mask:

            # Ensure CRS and transform are compatible or handle reprojection if necessary
            # For simplicity, assuming they align in this function
            if src_data.crs != src_mask.crs or src_data.transform != src_mask.transform or src_data.shape != src_mask.shape:
                # This simple function assumes alignment. For real-world use,
                # you'd need to reproject/resample one to match the other.
                print(f"Warning: Raster CRS/transform/shape mismatch for {raster_path} and {mask_raster_path}.")
                print(f"Data CRS: {src_data.crs}, Mask CRS: {src_mask.crs}")
                print(f"Data Transform: {src_data.transform}, Mask Transform: {src_mask.transform}")
                print(f"Data Shape: {src_data.shape}, Mask Shape: {src_mask.shape}")
                return None # Or implement reprojection/resampling

            data_array = src_data.read(1, masked=True) # Read with masked=True to handle NoData
            mask_array = src_mask.read(1)

            # Apply the mask: only consider pixels where mask_array > 0
            # Ensure mask_array is boolean where True means valid data
            valid_pixels_mask = (mask_array > 0)

            # If the data array already has a mask (from NoData values), combine them
            if data_array.mask is not np.ma.nomask:
                combined_mask = data_array.mask | ~valid_pixels_mask
            else:
                combined_mask = ~valid_pixels_mask

            masked_data = np.ma.array(data_array, mask=combined_mask)

            if masked_data.count() == 0: # Check if there are any valid pixels after masking
                return {'mean': np.nan, 'min': np.nan, 'max': np.nan, 'std': np.nan, 'pixel_count': 0}

            return {
                'mean': masked_data.mean(),
                'min': masked_data.min(),
                'max': masked_data.max(),
                'std': masked_data.std(),
                'pixel_count': masked_data.count()
            }
    except Exception as e:
        print(f"Error calculating stats for {raster_path} with mask {mask_raster_path}: {e}")
        return None

def find_woreda_mask_file(woreda_id, mask_dir, suffix='_coffee_extent.tif'):
    """
    Finds the coffee extent mask file for a given woreda ID within a directory.
    """
    expected_file = os.path.join(mask_dir, f'{woreda_id}{suffix}')
    if os.path.exists(expected_file):
        return expected_file
    return None
