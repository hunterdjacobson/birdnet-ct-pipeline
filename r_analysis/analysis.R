library(readr)
library(ggplot2)
library(dplyr)

# Load data
detections <- read_csv("outputs/detections_validated.csv")
threshold_metrics <- read_csv("outputs/threshold_metrics.csv")
species_summary <- read_csv("outputs/species_summary.csv")

# Plot 1: Confidence Distribution
# Faceted density plot of detection confidence scores, one facet per species, colored by whether the detection matched ground truth.
p1 <- ggplot(detections, aes(x = confidence, fill = qaqc_pass)) +
  geom_density(alpha = 0.5) +
  facet_wrap(~expected_common_name) +
  labs(title = "BirdNET Detection Confidence by Species and Accuracy",
       x = "Confidence Score",
       y = "Density",
       fill = "Correct Detection") +
  theme_minimal()

ggsave("outputs/confidence_distribution.png", plot = p1, width = 10, height = 6, dpi = 150)

# Plot 2: Threshold Tradeoff
# Line chart showing recall (left y-axis) and false positive rate (right y-axis) across the four confidence thresholds.
# We need to scale FPR to match the recall axis for the dual axis.
p2 <- ggplot(threshold_metrics, aes(x = threshold)) +
  geom_line(aes(y = species_recall, color = "Recall"), size = 1) +
  geom_point(aes(y = species_recall, color = "Recall"), size = 2) +
  geom_line(aes(y = false_positive_rate, color = "False Positive Rate"), size = 1) +
  geom_point(aes(y = false_positive_rate, color = "False Positive Rate"), size = 2) +
  scale_y_continuous(
    name = "Recall",
    limits = c(0, 1),
    sec.axis = sec_axis(~., name = "False Positive Rate")
  ) +
  labs(title = "Recall vs False Positive Rate by Confidence Threshold",
       x = "Confidence Threshold",
       color = "Metric") +
  theme_minimal()

ggsave("outputs/threshold_tradeoff.png", plot = p2, width = 10, height = 6, dpi = 150)

# Plot 3: Species-Level Recall at Confidence Threshold 0.50
# Horizontal bar chart of recall_at_50 per species, sorted descending.
species_summary <- species_summary %>%
  mutate(color_cat = case_when(
    recall_at_50 >= 0.80 ~ "High (>= 0.80)",
    recall_at_50 >= 0.60 ~ "Medium (0.60-0.79)",
    TRUE ~ "Low (< 0.60)"
  )) %>%
  mutate(common_name = reorder(common_name, recall_at_50))

p3 <- ggplot(species_summary, aes(x = common_name, y = recall_at_50, fill = color_cat)) +
  geom_bar(stat = "identity") +
  coord_flip() +
  scale_fill_manual(values = c("High (>= 0.80)" = "#2ecc71", "Medium (0.60-0.79)" = "#f1c40f", "Low (< 0.60)" = "#e74c3c")) +
  labs(title = "Species-Level Recall at Confidence Threshold 0.50",
       x = "Species",
       y = "Recall at 0.50",
       fill = "Performance") +
  theme_minimal()

ggsave("outputs/species_recall_bar.png", plot = p3, width = 10, height = 6, dpi = 150)

# Print text summary
metric_50 <- threshold_metrics %>% filter(threshold == 0.5)

cat("\n--- BirdNET Pipeline Analysis Summary ---\n")
cat(sprintf("Total recordings processed: %d\n", metric_50$total_files))
cat(sprintf("Total detections:          %d (at confidence >= 0.25)\n", max(threshold_metrics$total_detections_above_threshold)))
cat(sprintf("Overall recall at 0.50:    %.2f\n", metric_50$species_recall))
cat(sprintf("Overall FP rate at 0.50:   %.3f\n", metric_50$false_positive_rate))
cat("------------------------------------------\n")
