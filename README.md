# Avian Acoustic Detection Pipeline — Connecticut Species

This project implements an automated, end-to-end avian acoustic detection pipeline designed to process and validate wildlife audio recordings. By accurately identifying bird vocalizations from raw acoustic data, this tool supports long-term conservation monitoring and biodiversity assessments. The framework mirrors standard National Park Service (NPS) Autonomous Recording Unit (ARU) data workflows, providing a robust methodology for ingesting field recordings, running machine learning models, and conducting rigorous quality assurance.

## Pipeline Overview

| Script | Input | Output | Purpose |
| :--- | :--- | :--- | :--- |
| `01_acquire.py` | xeno-canto API | `data/raw/*.mp3`, `ingestion_log.csv` | Downloads species recordings and initializes ground-truth metadata. |
| `02_convert.py` | `data/raw/*.mp3` | `data/wav/*.wav` | Converts audio to meet strict BirdNET requirements (48kHz, mono, 16-bit). |
| `03_process.py` | `data/wav/*.wav` | `data/processed/*_detections.csv` | Analyzes audio segments using the BirdNET-Analyzer machine learning model. |
| `04_qaqc.py` | `*_detections.csv`, `ingestion_log.csv` | `threshold_metrics.csv`, `detections_validated.csv` | Validates blind detections against ground truth and calculates confidence thresholds. |
| `05_combine.py` | `detections_validated.csv` | `species_summary.csv` | Aggregates species-level performance metrics for downstream ecological reporting. |

## Relevance to ARU Workflows

This pipeline is heavily modeled after National Park Service (NPS) Autonomous Recording Unit (ARU) data management protocols to demonstrate production-ready bioacoustics engineering. It employs the structured directory architecture and strict file naming conventions necessary for handling large-scale acoustic datasets efficiently and preventing data loss. Furthermore, the inclusion of automated batch processing, a quantitative QA/QC validation framework, and a reproducible Standard Operating Procedure (SOP) ensures that derived ecological datasets are scientifically defensible and ready for occupancy modeling.

## QA/QC Results

| Threshold | Files w/ Correct Detection | Total Detections | False Positive Rate | Species Recall |
| :--- | :--- | :--- | :--- | :--- |
| 0.25 | 73 | 1324 | 0.1715 | 0.9125 |
| 0.50 | 70 | 1006 | 0.1203 | 0.8750 |
| 0.75 | 68 | 708 | 0.0876 | 0.8500 |
| 0.90 | 55 | 424 | 0.0755 | 0.6875 |

## Species Coverage

The pipeline is currently configured to monitor 10 common avian species found in Connecticut and the northeastern United States:

- American Robin (*Turdus migratorius*)
- Black-capped Chickadee (*Poecile atricapillus*)
- Song Sparrow (*Melospiza melodia*)
- American Crow (*Corvus brachyrhynchos*)
- Blue Jay (*Cyanocitta cristata*)
- White-throated Sparrow (*Zonotrichia albicollis*)
- Wood Thrush (*Hylocichla mustelina*)
- Ovenbird (*Seiurus aurocapilla*)
- Hermit Thrush (*Catharus guttatus*)
- American Redstart (*Setophaga ruticilla*)

## Tech Stack

- **Python 3.11**
- **birdnetlib** (Wrapping BirdNET-Analyzer v2.4)
- **ffmpeg** (Audio conversion via subprocess)
- **xeno-canto API v3**
- **R 4.6.0** (Statistical analysis)
- **ggplot2** (Data visualization)
- **librosa** / **TensorFlow** (birdnetlib audio processing dependencies)

## Local Setup

Run the following exact PowerShell commands to clone the repository, install dependencies, and execute the full pipeline sequentially:

```powershell
# 1. Clone the repository and navigate into it
git clone https://github.com/hunterdjacobson/birdnet-ct-pipeline.git
cd birdnet-ct-pipeline

# 2. Create and activate a Python virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Install required Python dependencies
pip install -r requirements.txt

# 4. Configure your xeno-canto API key
echo "XC_API_KEY=your_api_key_here" > .env

# 5. Run the pipeline sequence
python scripts/01_acquire.py
python scripts/02_convert.py
python scripts/03_process.py
python scripts/04_qaqc.py
python scripts/05_combine.py
```

## Data Source

Acoustic data is sourced from [xeno-canto](https://xeno-canto.org/), a global database of recorded wildlife sounds. 

Machine learning detections are powered by **BirdNET-Analyzer** (Kahl et al. 2021), a collaborative project by the Cornell Lab of Ornithology and the Chemnitz University of Technology.
