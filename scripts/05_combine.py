import pandas as pd
from pathlib import Path
from typing import List

def create_summary() -> None:
    """
    Combines ingestion log and validated detections to produce a per-species summary.
    Calculates acquisition counts, BirdNET processing status, recall, and confidence metrics.
    """
    # Setup paths using pathlib as per GEMINI.md rules
    base_dir = Path(__file__).resolve().parent.parent
    metadata_path = base_dir / "metadata" / "ingestion_log.csv"
    detections_path = base_dir / "outputs" / "detections_validated.csv"
    output_path = base_dir / "outputs" / "species_summary.csv"

    # 1. Load data
    if not metadata_path.exists():
        print(f"Error: Metadata file not found at {metadata_path}")
        return
    if not detections_path.exists():
        print(f"Error: Validated detections file not found at {detections_path}")
        return

    print(f"Loading data from {metadata_path.name} and {detections_path.name}...")
    log_df = pd.read_csv(metadata_path)
    det_df = pd.read_csv(detections_path)

    # 2. Group by species from ingestion_log.csv
    # We use species_code, common_name, and scientific_name as they define our target species
    species_groups = log_df.groupby(["species_code", "common_name", "scientific_name"])
    
    summary_rows = []
    
    print("Calculating species-level metrics...")
    for (code, common, scientific), group in species_groups:
        # Acquisition metrics
        n_acquired = len(group)
        n_processed = (group["birdnet_processed"] == "yes").sum()
        n_passed_qaqc = (group["qaqc_passed"] == "yes").sum()
        
        # Recall is based on total files acquired for this species
        recall = n_passed_qaqc / n_acquired if n_acquired > 0 else 0.0
        
        # Filter detections associated with these specific recordings (expected_common_name)
        # We use the common name to filter detections_validated.csv
        species_det = det_df[det_df["expected_common_name"] == common]
        
        # Correct detections at reference threshold 0.50 (qaqc_pass is True)
        correct_det = species_det[species_det["qaqc_pass"] == True]
        mean_conf_correct = correct_det["confidence"].mean() if not correct_det.empty else 0.0
        
        # False Positive (FP) detections at reference threshold 0.50 
        # (confidence >= 0.50 AND common_name != expected_common_name)
        fp_det = species_det[
            (species_det["confidence"] >= 0.50) & 
            (species_det["common_name"].str.strip().str.lower() != species_det["expected_common_name"].str.strip().str.lower())
        ]
        mean_conf_fp = fp_det["confidence"].mean() if not fp_det.empty else 0.0
        
        summary_rows.append({
            "species_code": code,
            "common_name": common,
            "scientific_name": scientific,
            "n_files_acquired": n_acquired,
            "n_files_birdnet_processed": n_processed,
            "n_files_passed_qaqc_50": n_passed_qaqc,
            "recall_at_50": recall,
            "mean_confidence_correct_detections": mean_conf_correct,
            "mean_confidence_fp_detections": mean_conf_fp
        })
        
    summary_df = pd.DataFrame(summary_rows)
    
    # Sort by species_code for consistent output
    summary_df = summary_df.sort_values("species_code")
    
    # 3. Save to outputs/species_summary.csv
    summary_df.to_csv(output_path, index=False)
    
    # 4. Print formatted summary table
    print("\n" + "="*135)
    print(f"{'Code':<10} | {'Common Name':<25} | {'Acq':<5} | {'Proc':<5} | {'QAQC':<5} | {'Recall':<8} | {'Avg Conf(C)':<12} | {'Avg Conf(FP)':<12}")
    print("-" * 135)
    for _, row in summary_df.iterrows():
        print(f"{row['species_code']:<10} | "
              f"{row['common_name']:<25} | "
              f"{row['n_files_acquired']:<5} | "
              f"{row['n_files_birdnet_processed']:<5} | "
              f"{row['n_files_passed_qaqc_50']:<5} | "
              f"{row['recall_at_50']:<8.4f} | "
              f"{row['mean_confidence_correct_detections']:<12.4f} | "
              f"{row['mean_confidence_fp_detections']:<12.4f}")
    print("="*135)
    print(f"Summary results written to: {output_path}")

if __name__ == "__main__":
    create_summary()
