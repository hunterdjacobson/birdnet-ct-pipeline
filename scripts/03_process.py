import pandas as pd
from pathlib import Path
import datetime
from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

def process_audio():
    """
    Processes WAV files using BirdNET-Analyzer and saves detections.
    """
    # Setup paths using pathlib
    base_dir = Path(__file__).resolve().parent.parent
    metadata_path = base_dir / "metadata" / "ingestion_log.csv"
    wav_dir = base_dir / "data" / "wav"
    processed_dir = base_dir / "data" / "processed"
    
    # Ensure processed directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Load metadata
    if not metadata_path.exists():
        print(f"Error: Metadata file not found at {metadata_path}")
        return
    
    df = pd.read_csv(metadata_path)
    
    # Filter rows where filename_wav is not empty and not "FAILED"
    # We also check if birdnet_processed is not already 'yes' to allow resumption
    mask = (df["filename_wav"].notna()) & (df["filename_wav"] != "FAILED") & (df["birdnet_processed"] != "yes")
    rows_to_process = df[mask].copy()
    
    if rows_to_process.empty:
        print("No new WAV files to process.")
        return

    # Instantiate Analyzer ONCE (loads model into memory)
    print("Initializing BirdNET Analyzer...")
    analyzer = Analyzer()

    total = len(rows_to_process)
    
    for i, (idx, row) in enumerate(rows_to_process.iterrows(), 1):
        filename_wav = row["filename_wav"]
        wav_path = wav_dir / filename_wav
        xc_id = row["xc_id"]
        
        if not wav_path.exists():
            print(f"Processing {i}/{total}: {filename_wav} -> FAILED (File not found)")
            continue
            
        print(f"Processing {i}/{total}: {filename_wav}", end=" ", flush=True)
        
        try:
            # Create Recording object
            recording = Recording(
                analyzer=analyzer,
                path=str(wav_path),
                lat=41.6032,      # Connecticut latitude
                lon=-73.0877,     # Connecticut longitude
                date=datetime.datetime(2024, 6, 15),  # Representative summer date
                min_conf=0.1      # Low threshold for later filtering
            )
            
            # Run analysis
            recording.analyze()
            detections = recording.detections
            
            # Prepare detection data
            det_rows = []
            for det in detections:
                # recording.detections returns a list of dicts with:
                # common_name, scientific_name, start_time, end_time, confidence, label
                det_rows.append({
                    "xc_id": xc_id,
                    "filename_wav": filename_wav,
                    "common_name": det["common_name"],
                    "scientific_name": det["scientific_name"],
                    "start_time": det["start_time"],
                    "end_time": det["end_time"],
                    "confidence": det["confidence"]
                })
            
            # Save detections to per-file CSV
            stem = wav_path.stem
            out_csv = processed_dir / f"{stem}_detections.csv"
            
            det_df = pd.DataFrame(det_rows, columns=[
                "xc_id", "filename_wav", "common_name", "scientific_name", 
                "start_time", "end_time", "confidence"
            ])
            det_df.to_csv(out_csv, index=False)
            
            # Update main dataframe
            df.at[idx, "birdnet_processed"] = "yes"
            
            print(f"-> {len(det_rows)} detections")
            
        except Exception as e:
            print(f"-> FAILED ({e})")
            
    # Save updated metadata log
    df.to_csv(metadata_path, index=False)
    print("\nProcessing complete. Metadata log updated.")

if __name__ == "__main__":
    process_audio()
