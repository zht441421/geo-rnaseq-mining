#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(optparse)
  library(yaml)
  library(ggplot2)
  library(pheatmap)
})

option_list <- list(
  make_option("--counts", type = "character"),
  make_option("--metadata", type = "character"),
  make_option("--config", type = "character"),
  make_option("--dataset-id", type = "character"),
  make_option("--output-dir", type = "character")
)
opt <- parse_args(OptionParser(option_list = option_list))

read_tsv <- function(path) {
  read.delim(
    path,
    header = TRUE,
    sep = "\t",
    check.names = FALSE,
    stringsAsFactors = FALSE,
    na.strings = character()
  )
}

write_tsv <- function(value, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  write.table(
    value,
    file = path,
    sep = "\t",
    quote = FALSE,
    row.names = FALSE,
    col.names = TRUE
  )
}

robust_z <- function(values) {
  center <- median(values)
  spread <- median(abs(values - center))
  if (spread > 0) {
    return(0.6744897501960817 * (values - center) / spread)
  }
  if (sd(values) > 0) {
    return(as.numeric(scale(values)))
  }
  rep(0, length(values))
}

validate_raw_integer_counts <- function(frame) {
  if (ncol(frame) < 2) {
    stop("Bulk QC requires at least one sample count column")
  }
  if (anyDuplicated(frame[[1]])) {
    stop("Bulk QC input contains duplicate gene IDs")
  }
  values <- as.matrix(frame[, -1, drop = FALSE])
  numeric_values <- suppressWarnings(matrix(
    as.numeric(values),
    nrow = nrow(values),
    dimnames = dimnames(values)
  ))
  if (any(is.na(numeric_values)) || any(!is.finite(numeric_values))) {
    stop("Bulk QC requires finite non-negative integer raw counts")
  }
  if (any(numeric_values < 0)) {
    stop("Bulk QC requires finite non-negative integer raw counts")
  }
  if (any(abs(numeric_values - round(numeric_values)) > sqrt(.Machine$double.eps))) {
    stop("Bulk QC requires finite non-negative integer raw counts")
  }
  storage.mode(numeric_values) <- "integer"
  numeric_values
}

message_plot <- function(path, label) {
  png(path, width = 1200, height = 900, res = 140)
  plot.new()
  text(0.5, 0.5, label, cex = 1.4)
  dev.off()
}

output_dir <- opt$`output-dir`
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
config <- read_yaml(opt$config)
counts_frame <- read_tsv(opt$counts)
metadata <- read_tsv(opt$metadata)
if (!identical(colnames(counts_frame)[-1], metadata$sample_id)) {
  stop("QC input count columns are not in reviewed metadata order")
}
if (anyDuplicated(counts_frame[[1]])) {
  stop("QC input contains duplicate gene IDs")
}

counts <- validate_raw_integer_counts(counts_frame)
rownames(counts) <- counts_frame[[1]]
log_counts <- log2(counts + 1)
library_size <- colSums(counts)
detected_threshold <- config$bulk$detected_gene_min_count
detected_genes <- colSums(counts >= detected_threshold)

if (ncol(counts) >= 2 && nrow(counts) >= 2) {
  pca <- prcomp(t(log_counts), center = TRUE, scale. = FALSE)
  component_count <- min(5, ncol(pca$x))
  pca_distance <- sqrt(
    rowSums(
      sweep(
        pca$x[, seq_len(component_count), drop = FALSE],
        2,
        apply(pca$x[, seq_len(component_count), drop = FALSE], 2, median),
        "-"
      ) ^ 2
    )
  )
  variance <- 100 * pca$sdev ^ 2 / sum(pca$sdev ^ 2)
  pca_coordinates <- data.frame(
    sample_id = rownames(pca$x),
    PC1 = pca$x[, 1],
    PC2 = if (ncol(pca$x) >= 2) pca$x[, 2] else 0,
    stringsAsFactors = FALSE
  )
  pca_coordinates <- merge(
    pca_coordinates,
    metadata,
    by = "sample_id",
    sort = FALSE
  )
  pca_coordinates <- pca_coordinates[
    match(metadata$sample_id, pca_coordinates$sample_id),
    ,
    drop = FALSE
  ]
  pca_plot <- ggplot(
    pca_coordinates,
    aes(x = PC1, y = PC2, color = group, shape = batch, label = sample_id)
  ) +
    geom_point(size = 3) +
    geom_text(vjust = -0.8, check_overlap = TRUE) +
    labs(
      title = paste(opt$`dataset-id`, "bulk sample PCA"),
      x = sprintf("PC1 (%.1f%%)", variance[1]),
      y = sprintf("PC2 (%.1f%%)", ifelse(length(variance) >= 2, variance[2], 0))
    ) +
    theme_bw()
  ggsave(
    file.path(output_dir, "pca.png"),
    pca_plot,
    width = 8,
    height = 6,
    dpi = 160
  )
} else {
  pca_distance <- rep(0, ncol(counts))
  pca_coordinates <- data.frame(
    sample_id = colnames(counts),
    PC1 = 0,
    PC2 = 0,
    stringsAsFactors = FALSE
  )
  message_plot(file.path(output_dir, "pca.png"), "PCA requires at least two samples")
}
write_tsv(pca_coordinates, file.path(output_dir, "pca_coordinates.tsv"))

library_z <- robust_z(log10(library_size + 1))
detected_z <- robust_z(detected_genes)
pca_z <- robust_z(pca_distance)
threshold <- config$bulk$outlier_z_threshold
outlier_flag <- abs(library_z) >= threshold |
  abs(detected_z) >= threshold |
  abs(pca_z) >= threshold
flagged_metrics <- vapply(
  seq_along(outlier_flag),
  function(index) {
    labels <- c(
      if (abs(library_z[index]) >= threshold) "library_size" else NULL,
      if (abs(detected_z[index]) >= threshold) "detected_genes" else NULL,
      if (abs(pca_z[index]) >= threshold) "pca_distance" else NULL
    )
    if (length(labels) == 0) "none" else paste(labels, collapse = ";")
  },
  character(1)
)

metrics <- data.frame(
  sample_id = colnames(counts),
  dataset_id = metadata$dataset_id,
  group = metadata$group,
  batch = metadata$batch,
  subject_id = metadata$subject_id,
  library_size = library_size,
  detected_genes = detected_genes,
  library_size_robust_z = library_z,
  detected_genes_robust_z = detected_z,
  pca_distance_robust_z = pca_z,
  outlier_flag = tolower(as.character(outlier_flag)),
  stringsAsFactors = FALSE
)
write_tsv(metrics, file.path(output_dir, "sample_qc_metrics.tsv"))
outliers <- data.frame(
  sample_id = colnames(counts),
  dataset_id = metadata$dataset_id,
  outlier_flag = tolower(as.character(outlier_flag)),
  flagged_metrics = flagged_metrics,
  retained_for_analysis = "true",
  required_action = ifelse(outlier_flag, "user_review_manifest", "none"),
  stringsAsFactors = FALSE
)
write_tsv(outliers, file.path(output_dir, "outlier_report.tsv"))

annotation_columns <- intersect(
  c("dataset_id", "group", "batch", "sex", "age", "subject_id"),
  colnames(metadata)
)
annotations <- metadata[, c("sample_id", annotation_columns), drop = FALSE]
write_tsv(annotations, file.path(output_dir, "qc_annotations.tsv"))
heatmap_annotation <- annotations[, annotation_columns, drop = FALSE]
rownames(heatmap_annotation) <- annotations$sample_id
heatmap_annotation[] <- lapply(heatmap_annotation, as.factor)

if (ncol(counts) >= 2) {
  sample_distance <- as.matrix(dist(t(log_counts)))
  pheatmap(
    sample_distance,
    annotation_col = heatmap_annotation,
    annotation_row = heatmap_annotation,
    filename = file.path(output_dir, "sample_distance_heatmap.png"),
    width = 9,
    height = 8
  )
  correlation <- cor(log_counts, method = "pearson")
  correlation[!is.finite(correlation)] <- 0
  diag(correlation) <- 1
  pheatmap(
    correlation,
    annotation_col = heatmap_annotation,
    annotation_row = heatmap_annotation,
    filename = file.path(output_dir, "correlation_heatmap.png"),
    width = 9,
    height = 8
  )
  clustering <- hclust(dist(t(log_counts)))
  png(
    file.path(output_dir, "hierarchical_clustering.png"),
    width = 1400,
    height = 900,
    res = 140
  )
  plot(clustering, main = paste(opt$`dataset-id`, "hierarchical clustering"))
  dev.off()
} else {
  message_plot(
    file.path(output_dir, "sample_distance_heatmap.png"),
    "Sample distance requires at least two samples"
  )
  message_plot(
    file.path(output_dir, "correlation_heatmap.png"),
    "Correlation requires at least two samples"
  )
  message_plot(
    file.path(output_dir, "hierarchical_clustering.png"),
    "Clustering requires at least two samples"
  )
}

capture.output(sessionInfo(), file = file.path(output_dir, "qc_session_info.txt"))
writeLines(
  c(
    paste0("dataset_id=", opt$`dataset-id`),
    paste0("sample_count=", ncol(counts)),
    paste0("outlier_count=", sum(outlier_flag)),
    "samples_removed=0"
  ),
  con = file.path(output_dir, ".complete")
)
