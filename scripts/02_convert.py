import pandas as pd
from pathlib import Path
import sys

def convert_mp3_to_wav() -> None:
    """
    Loads metadata, filters for successful downloads, and converts MP3s to WAV
    with BirdNET-compatible specifications (48kHz, 16-bit, mono).
    """
    # Define paths using pathlib
    base_dir = Path(__file__).parent.parent
    log_path = base_dir / "metadata" / "ingestion_log.csv"
    raw_dir = base_dir / "data" / "raw"
    wav_dir = base_dir / "data" / "wav"
    
    # Ensure wav directory exists
    wav_dir.mkdir(parents=True, exist_ok=True)
    
    # Load metadata
    if not log_path.exists():
        print(f"Error: {log_path} not found.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(log_path)
    except Exception as e:
        print(f"Error reading {log_path}: {e}")
        sys.exit(1)
    
    # Filter for rows where download_status is 'success'
    # We only want to convert files that were successfully downloaded
    mask = df["download_status"] == "success"
    indices_to_process = df[mask].index
    
    total = len(indices_to_process)
    if total == 0:
        print("No files found with download_status == 'success'.")
        return

    print(f"Starting conversion of {total} files...")
    
    for i, idx in enumerate(indices_to_process, 1):
        filename_raw = df.at[idx, "filename_raw"]
        mp3_path = raw_dir / filename_raw
        
        # Define output filename: same as raw but with .wav extension
        filename_wav = Path(filename_raw).with_suffix(".wav").name
        wav_path = wav_dir / filename_wav
        
        print(f"Converting {i}/{total}: {filename_raw}")
        
        if not mp3_path.exists():
            print(f"Warning: Raw file {mp3_path} does not exist. Skipping.")
            df.at[idx, "filename_wav"] = "FAILED"
            continue
            
        try:
            import subprocess
            result = subprocess.run(
                [
                    "ffmpeg", "-y",           # overwrite output without asking
                    "-i", str(mp3_path),      # input file
                    "-ar", "48000",           # sample rate: 48kHz
                    "-ac", "1",               # channels: mono
                    "-sample_fmt", "s16",     # 16-bit PCM (equivalent to sample_width=2)
                    str(wav_path)
                ],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"  ffmpeg error: {result.stderr[-200:]}")
                df.at[idx, "filename_wav"] = "FAILED"
            else:
                df.at[idx, "filename_wav"] = filename_wav

        except Exception as e:
            print(f"Error converting {filename_raw}: {e}")
            df.at[idx, "filename_wav"] = "FAILED"
            
    # Write the updated dataframe back to metadata/ingestion_log.csv
    try:
        df.to_csv(log_path, index=False)
        print(f"Finished. Updated log written to {log_path}")
    except Exception as e:
        print(f"Error saving updated log: {e}")
        sys.exit(1)

if __name__ == "__main__":
    convert_mp3_to_wav()
