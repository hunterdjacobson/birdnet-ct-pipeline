# BirdNET Acoustic Detection Pipeline — Project Context

## What this project is
An end-to-end pipeline that acquires real bird audio recordings for
Connecticut species from the xeno-canto API, converts them to WAV,
runs BirdNET-Analyzer for automated species detection, performs QA/QC
against known ground-truth labels, and outputs validated detection
results with a full metadata log and SOP documentation.

## Target species (Connecticut / northeastern US)
- American Robin (Turdus migratorius)
- Black-capped Chickadee (Poecile atricapillus)
- Song Sparrow (Melospiza melodia)
- American Crow (Corvus brachyrhynchos)
- Blue Jay (Cyanocitta cristata)
- White-throated Sparrow (Zonotrichia albicollis)
- Wood Thrush (Hylocichla mustelina)
- Ovenbird (Seiurus aurocapilla)
- Hermit Thrush (Catharus guttatus)
- American Redstart (Setophaga ruticilla)

## Tech stack
- Python 3.11
- birdnetlib (BirdNET-Analyzer wrapper)
- ffmpeg
- requests (xeno-canto API calls — OK to use here, not async)
- pandas (data management and CSV I/O)
- R 4.x with ggplot2, dplyr, readr, rmarkdown

## Project structure
```birdnet-ct-pipeline/
├── data/
│   ├── raw/              # original .mp3 from xeno-canto (never modified)
│   ├── wav/              # converted .wav files ready for BirdNET
│   ├── processed/        # per-file BirdNET detection CSVs
│   └── validated/        # post-QA/QC cleaned results
├── metadata/
│   └── ingestion_log.csv # master record of every file processed
├── outputs/
│   └── detections_validated.csv
├── r_analysis/
│   ├── analysis.R
│   └── report.Rmd
├── docs/
│   └── SOP.md
├── scripts/
│   ├── 01_acquire.py
│   ├── 02_convert.py
│   ├── 03_process.py
│   ├── 04_qaqc.py
│   └── 05_combine.py
├── requirements.txt
├── GEMINI.md
└── README.md
```

## Coding rules
- Use type hints on all functions
- All file paths use pathlib.Path, never raw strings
- File naming convention: {SPECIES_CODE}_{XCID}_{QUALITY}.mp3 / .wav
  where SPECIES_CODE is the first 4 letters of genus + first 4 of species
  (e.g. TURDMIGR for Turdus migratorius)
- Every file processed must get a row written to metadata/ingestion_log.csv
- Never overwrite raw/ files — raw data is sacred
- All scripts must be runnable independently (not depend on prior script
  having been run in the same process)
- Print progress to stdout as processing happens
- Connecticut lat/lon: 41.6032, -73.0877

## Data source
xeno-canto API v3 (https://xeno-canto.org/api/3/recordings)
Requires API key loaded from .env as XC_API_KEY.
Query params: query (search string, use structured tags e.g. "gen:Turdus sp:migratorius"), 
key (API key), page (pagination).
Response JSON: recordings[] array with id, en, file, q, lat, lon, loc, date, length fields.
The "file" field may start with "//" — prepend "https:" if so.
Never hardcode the API key — load from os.environ only.

## What to never do
- Never modify files in data/raw/
- Never hardcode paths — always use pathlib.Path(__file__).parent
- Never silently swallow exceptions — log them to the metadata
- Never use os.path — use pathlib only