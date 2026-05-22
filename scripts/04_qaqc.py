import pandas as pd
from pathlib import Path
from typing import List, Optional

def run_qaqc() -> None:
    """
    Performs QA/QC on BirdNET detections against ground truth metadata.
    """
    # Setup paths using pathlib
    base_dir = Path(__file__).resolve().parent.parent
    metadata_path = base_dir / "metadata" / "ingestion_log.csv"
    processed_dir = base_dir / "data" / "processed"
    outputs_dir = base_dir / "outputs"
    
    # Ensure outputs directory exists
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load metadata (ground truth)
    if not metadata_path.exists():
        print(f"Error: Metadata file not found at {metadata_path}")
        return
    
    metadata_df = pd.read_csv(metadata_path)
    # Ensure xc_id is consistent type (int)
    metadata_df["xc_id"] = metadata_df["xc_id"].astype(int)
    
    # 2. Load all per-file detection CSVs from data/processed/ and concatenate
    print("Loading detection results...")
    detection_files = list(processed_dir.glob("*_detections.csv"))
    
    if not detection_files:
        print("No detection files found in data/processed/")
        return
    
    all_detections_list = []
    for f in detection_files:
        det_df = pd.read_csv(f)
        all_detections_list.append(det_df)
    
    detections_df = pd.concat(all_detections_list, ignore_index=True)
    detections_df["xc_id"] = detections_df["xc_id"].astype(int)
    
    # 3. Join detections to metadata on xc_id to add ground truth columns
    gt_cols = ["xc_id", "common_name", "scientific_name"]
    gt_df = metadata_df[gt_cols].rename(columns={
        "common_name": "expected_common_name",
        "scientific_name": "expected_scientific_name"
    })
    
    merged_df = pd.merge(detections_df, gt_df, on="xc_id", how="left")
    
    # 4. Define Thresholds
    CONFIDENCE_THRESHOLDS = [0.25, 0.50, 0.75, 0.90]
    
    # 5. Compute metrics for each threshold
    total_files = metadata_df["xc_id"].nunique()
    metrics_rows = []
    
    # Helper for name matching (case-insensitive)
    def is_match(row):
        return str(row["common_name"]).strip().lower() == str(row["expected_common_name"]).strip().lower()

    # Pre-calculate match status for efficiency
    merged_df["is_gt_match"] = merged_df.apply(is_match, axis=1)

    # Calculate threshold_passed_at (lowest threshold at which this detection passes)
    def get_lowest_threshold(row) -> Optional[float]:
        if not row["is_gt_match"]:
            return None
        # Thresholds are [0.25, 0.50, 0.75, 0.90]
        # If confidence is 0.8, it passes 0.25, 0.50, 0.75. Lowest is 0.25.
        for t in CONFIDENCE_THRESHOLDS:
            if row["confidence"] >= t:
                return t
        return None

    merged_df["threshold_passed_at"] = merged_df.apply(get_lowest_threshold, axis=1)
    
    # qaqc_pass (bool) - using threshold 0.50 as the standard for 'validated'
    merged_df["qaqc_pass"] = (merged_df["confidence"] >= 0.50) & (merged_df["is_gt_match"])

    print(f"Evaluating metrics for {total_files} files...")
    
    for threshold in CONFIDENCE_THRESHOLDS:
        # A detection PASSES if: confidence >= threshold AND name matches
        passed_mask = (merged_df["confidence"] >= threshold) & (merged_df["is_gt_match"])
        
        # A detection is a FALSE POSITIVE if: confidence >= threshold AND name does NOT match
        fp_mask = (merged_df["confidence"] >= threshold) & (~merged_df["is_gt_match"])
        
        # Total detections above threshold
        total_above = (merged_df["confidence"] >= threshold).sum()
        
        # False positive count
        fp_count = fp_mask.sum()
        
        # Files with at least one correct detection
        correct_files = merged_df[passed_mask]["xc_id"].nunique()
        
        # Metrics
        fpr = fp_count / total_above if total_above > 0 else 0.0
        recall = correct_files / total_files if total_files > 0 else 0.0
        
        metrics_rows.append({
            "threshold": threshold,
            "total_files": total_files,
            "files_with_correct_detection": correct_files,
            "total_detections_above_threshold": total_above,
            "false_positive_detections": fp_count,
            "false_positive_rate": fpr,
            "species_recall": recall
        })

    # 6. Save threshold_metrics.csv
    metrics_df = pd.DataFrame(metrics_rows)
    metrics_df.to_csv(outputs_dir / "threshold_metrics.csv", index=False)
    
    # 7. Save detections_validated.csv
    out_cols = [
        "xc_id", "filename_wav", "common_name", "scientific_name", 
        "expected_common_name", "expected_scientific_name",
        "start_time", "end_time", "confidence", "qaqc_pass", "threshold_passed_at"
    ]
    merged_df[out_cols].to_csv(outputs_dir / "detections_validated.csv", index=False)
    
    # 8. Update metadata/ingestion_log.csv
    # Set qaqc_passed="yes" for files where at least one detection passed at threshold=0.50
    passed_050_ids = merged_df[(merged_df["confidence"] >= 0.50) & (merged_df["is_gt_match"])]["xc_id"].unique()
    metadata_df["qaqc_passed"] = metadata_df["xc_id"].apply(lambda x: "yes" if x in passed_050_ids else "no")
    metadata_df.to_csv(metadata_path, index=False)
    
    # 9. Print formatted summary table
    print("\n" + "="*95)
    print(f"{'Threshold':<10} | {'Files Pass':<10} | {'Total Det':<10} | {'FP Det':<10} | {'FP Rate':<10} | {'Recall':<10}")
    print("-" * 95)
    for row in metrics_rows:
        print(f"{row['threshold']:<10.2f} | "
              f"{row['files_with_correct_detection']:<10} | "
              f"{row['total_detections_above_threshold']:<10} | "
              f"{row['false_positive_detections']:<10} | "
              f"{row['false_positive_rate']:<10.4f} | "
              f"{row['species_recall']:<10.4f}")
    print("="*95)
    print(f"Results saved to {outputs_dir}")
    print("Metadata log updated with QA/QC status (threshold=0.50).")

if __name__ == "__main__":
    run_qaqc()
