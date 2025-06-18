# Coffee Yield Prediction using Remote Sensing and Machine Learning (Sidama, Ethiopia)

This project aims to predict coffee yields at the woreda (district) level in the Sidama region of Ethiopia, leveraging satellite imagery (Sentinel-2, SRTM, SMAP) and climate data (ERA5-Land) combined with machine learning techniques. It is a restructured and modularized version of a previous monolithic Jupyter Notebook.

## Project Overview

The core idea is to establish a data pipeline that:
1.  **Extracts** relevant geospatial and environmental data from Google Earth Engine (GEE).
2.  **Processes** this data, including masking by coffee-growing areas and aggregating features per administrative unit (woreda).
3.  **Integrates** with historical coffee yield data.
4.  **Engineers** time-series features (e.g., lagged vegetation indices, seasonal climatic averages).
5.  **Trains** a machine learning model to predict annual coffee yield.
6.  **Analyzes and Visualizes** the predictions and model insights.

## Setup and Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Zabrsh/coffee-yield-prediction-using-remote-sensing-data
cd coffee-yield-prediction-using-remote-sensing-data
```

### 2. Create a Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Google Earth Engine (GEE) Authentication
```bash
earthengine authenticate
```

### 5. Google Cloud Storage (GCS) Setup
- Create a Google Cloud Project with billing enabled
- Set up a GCS Bucket and update BUCKET_NAME in the notebooks
- Ensure proper permissions for GCS access
- For Jupyter/Colab authentication:
    ```python
    from google.colab import auth
    auth.authenticate_user()
    ```

### 6. Input Data
Place your data in the `data/input/` directory:
- MAPSPAM Coffee Extent Data (e.g., `spam2017V2r1_SSA_H_COFF_A.tif`)
- Raw Yield Data CSV with columns: `woreda_id`, `year`, and `yield_quintals_ha`

## Running the Project

Execute the notebooks sequentially:
1. `00_setup_and_common_data_loading.ipynb`: Initialize GEE and preprocess boundaries
2. `01_gee_sentinel2_export.ipynb`: Export Sentinel-2 composites
3. `02_gee_era5_export.ipynb`: Export ERA5-Land climate data
4. `03_gee_srtm_smap_export.ipynb`: Export elevation and soil moisture data
5. `04_mapspam_coffee_extent_processing.ipynb`: Process coffee area data
6. `05_vegetation_indices_calculation.ipynb`: Calculate vegetation indices
7. `06_environmental_data_integration.ipynb`: Aggregate environmental features
8. `07_yield_data_preparation.ipynb`: Clean yield data
9. `08_data_consolidation_and_feature_engineering.ipynb`: Merge features and engineer new ones
10. `09_yield_prediction_model.ipynb`: Train and evaluate models
11. `10_results_analysis_and_visualization.ipynb`: Visualize results

## Expected Outputs

- `data/processed/sidama_woredas.geojson`: Processed boundaries
- `data/processed/coffee_extents/*.tif`: Coffee extent rasters
- `data/processed/woreda_monthly_vegetation_indices.csv`: Aggregated vegetation indices
- `data/processed/woreda_monthly_environmental_data.csv`: Aggregated climate data
- `data/processed/woreda_annual_yield_data.csv`: Processed yield data
- `data/processed/master_woreda_data.csv`: Consolidated dataset
- `data/processed/sidama_coffee_yield_predictions_2025.csv`: Future yield predictions
- `models/best_yield_prediction_model.pkl`: Trained model
- `models/feature_scaler.pkl`: Feature scaler
- `models/feature_columns.pkl`: Feature column names

## Acknowledgments

This work was done as part of a Master's research thesis titled "Satellite driven coffee yield prediction in Sidama, Ethiopia", under the supervision of Professor Mikael Yu. Katev at the National University of Science and Technology MISIS.

Moscow, June 2025
