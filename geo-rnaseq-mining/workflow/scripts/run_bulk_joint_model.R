#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(optparse)
  library(yaml)
  library(DESeq2)
  library(ggplot2)
  library(pheatmap)
})

option_list <- list(
  make_option("--counts", type = "character"),
  make_option("--metadata", type = "character"),
  make_option("--contrasts", type = "character"),
  make_option("--dataset-plan", type = "character"),
  make_option("--config", type = "character"),
  make_option("--analysis-id", type = "character"),
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

safe_name <- function(value) {
  gsub("[^A-Za-z0-9_.-]", "_", value)
}

message_plot <- function(path, label) {
  png(path, width = 1200, height = 900, res = 140)
  plot.new()
  text(0.5, 0.5, label, cex = 1.3)
  dev.off()
}

coerce_metadata <- function(metadata) {
  factor_columns <- c(
    "sample_id", "subject_id", "paired_group", "dataset_id", "dataset",
    "group", "batch", "sex", "condition", "tissue", "timepoint", "treatment"
  )
  for (column in colnames(metadata)) {
    values <- metadata[[column]]
    values[values %in% c("", "NA", "N/A", "null", "None")] <- NA
    numeric_values <- suppressWarnings(as.numeric(values))
    if (column == "age" && all(is.na(values) | !is.na(numeric_values))) {
      metadata[[column]] <- numeric_values
    } else if (column %in% factor_columns) {
      metadata[[column]] <- factor(values)
    } else {
      metadata[[column]] <- values
    }
  }
  metadata
}

config <- read_yaml(opt$config)
counts_frame <- read_tsv(opt$counts)
metadata_all <- read_tsv(opt$metadata)
contrasts_all <- read_tsv(opt$contrasts)
plan <- read_tsv(opt$`dataset-plan`)
selected_plan <- plan[
  plan$analysis_id == opt$`analysis-id` & plan$include == "true",
  ,
  drop = FALSE
]
if (
  nrow(selected_plan) < 2 ||
    !all(selected_plan$analysis_strategy == "joint_model") ||
    any(selected_plan$role == "validation")
) {
  stop("dataset_plan.tsv does not authorize this joint model")
}
if (!identical(colnames(counts_frame)[-1], metadata_all$sample_id)) {
  stop("Joint count columns differ from reviewed metadata order")
}
if (any(counts_frame[, -1, drop = FALSE] < 0)) {
  stop("Joint model received negative counts")
}
if (any(counts_frame[, -1, drop = FALSE] %% 1 != 0)) {
  stop("Joint model received non-integer counts")
}
counts_all <- as.matrix(counts_frame[, -1, drop = FALSE])
storage.mode(counts_all) <- "integer"
rownames(counts_all) <- counts_frame[[1]]
contrasts <- contrasts_all[
  contrasts_all$analysis_id == opt$`analysis-id` &
    contrasts_all$enabled == "true" &
    contrasts_all$data_scope == "bulk",
  ,
  drop = FALSE
]
if (nrow(contrasts) == 0) {
  stop("No enabled bulk contrast exists for the joint analysis")
}

dir.create(opt$`output-dir`, recursive = TRUE, showWarnings = FALSE)
result_manifest <- list()
effect_summary <- list()
combat_enabled <- isTRUE(
  config$multi_dataset$joint_model$combat_seq$enabled
)

for (contrast_index in seq_len(nrow(contrasts))) {
  contrast <- contrasts[contrast_index, , drop = FALSE]
  contrast_id <- contrast$contrast_id[[1]]
  contrast_dir <- file.path(opt$`output-dir`, safe_name(contrast_id))
  dir.create(contrast_dir, recursive = TRUE, showWarnings = FALSE)
  selected <- metadata_all
  subset_column <- contrast$subset_column[[1]]
  subset_value <- contrast$subset_value[[1]]
  if (!is.na(subset_column) && !(subset_column %in% c("", "NA", "N/A", "null", "None"))) {
    if (!(subset_column %in% colnames(selected))) {
      stop(paste("Unknown subset column for", contrast_id, subset_column))
    }
    selected <- selected[selected[[subset_column]] == subset_value, , drop = FALSE]
  }
  numerator <- contrast$numerator[[1]]
  denominator <- contrast$denominator[[1]]
  selected <- selected[
    selected$group %in% c(numerator, denominator),
    ,
    drop = FALSE
  ]
  count_subset <- counts_all[, selected$sample_id, drop = FALSE]
  metadata <- coerce_metadata(selected)
  rownames(metadata) <- selected$sample_id
  metadata$group <- relevel(factor(as.character(metadata$group)), ref = denominator)
  metadata$dataset_id <- factor(as.character(metadata$dataset_id))
  metadata$dataset <- metadata$dataset_id
  design_formula <- as.formula(contrast$design_formula[[1]])
  design_variables <- all.vars(design_formula)
  missing_variables <- setdiff(design_variables, colnames(metadata))
  if (length(missing_variables) > 0) {
    stop(paste("Unavailable design variables:", paste(missing_variables, collapse = ", ")))
  }
  if (any(!complete.cases(metadata[, design_variables, drop = FALSE]))) {
    stop(paste("Design variables contain missing values for", contrast_id))
  }
  design_matrix <- model.matrix(design_formula, data = metadata)
  design_rank <- qr(design_matrix)$rank
  if (design_rank != ncol(design_matrix)) {
    stop(
      sprintf(
        "Design matrix for %s is not full rank: rank=%d columns=%d",
        contrast_id,
        design_rank,
        ncol(design_matrix)
      )
    )
  }
  write_tsv(
    data.frame(sample_id = rownames(design_matrix), design_matrix, check.names = FALSE),
    file.path(contrast_dir, "design_matrix.tsv")
  )

  analysis_counts <- count_subset
  if (combat_enabled) {
    if (!requireNamespace("sva", quietly = TRUE)) {
      stop("ComBat-seq was enabled but the sva package is unavailable")
    }
    analysis_counts <- sva::ComBat_seq(
      counts = count_subset,
      batch = metadata$dataset_id,
      group = metadata$group
    )
    storage.mode(analysis_counts) <- "integer"
    write_tsv(
      data.frame(gene_id = rownames(analysis_counts), analysis_counts, check.names = FALSE),
      file.path(contrast_dir, "combat_seq_adjusted_counts.tsv")
    )
  }

  dds <- DESeqDataSetFromMatrix(
    countData = analysis_counts,
    colData = metadata,
    design = design_formula
  )
  raw_gene_count <- nrow(dds)
  keep <- rowSums(counts(dds)) >= config$bulk$detected_gene_min_count &
    rowSums(counts(dds)) > 0
  dds <- dds[keep, ]
  if (nrow(dds) == 0) {
    stop(paste("No genes remain after count filtering for", contrast_id))
  }
  dds <- DESeq(dds)
  result <- results(
    dds,
    contrast = c("group", numerator, denominator),
    alpha = config$bulk$deseq2_alpha
  )
  result_frame <- data.frame(
    gene_id = rownames(result),
    as.data.frame(result),
    check.names = FALSE
  )
  result_frame <- result_frame[order(result_frame$padj, na.last = TRUE), , drop = FALSE]
  significant <- result_frame[
    !is.na(result_frame$padj) &
      result_frame$padj < config$bulk$deseq2_alpha &
      abs(result_frame$log2FoldChange) >= config$bulk$deseq2_abs_log2fc,
    ,
    drop = FALSE
  ]
  full_path <- file.path(contrast_dir, "deseq2_full_results.tsv")
  significant_path <- file.path(contrast_dir, "deseq2_significant_results.tsv")
  write_tsv(result_frame, full_path)
  write_tsv(significant, significant_path)

  normalized <- counts(dds, normalized = TRUE)
  write_tsv(
    data.frame(gene_id = rownames(normalized), normalized, check.names = FALSE),
    file.path(contrast_dir, "normalized_counts.tsv")
  )
  transformation <- config$bulk$transformation
  transformed <- if (transformation == "rlog") {
    rlog(dds, blind = FALSE)
  } else if (nrow(dds) < 1000) {
    varianceStabilizingTransformation(dds, blind = FALSE)
  } else {
    vst(dds, blind = FALSE)
  }
  transformed_matrix <- assay(transformed)
  transformed_path <- file.path(contrast_dir, paste0(transformation, "_matrix.tsv"))
  write_tsv(
    data.frame(gene_id = rownames(transformed_matrix), transformed_matrix, check.names = FALSE),
    transformed_path
  )

  png(file.path(contrast_dir, "ma_plot.png"), width = 1200, height = 900, res = 140)
  plotMA(result, alpha = config$bulk$deseq2_alpha, main = contrast_id)
  dev.off()
  volcano <- result_frame
  volcano$significant <- !is.na(volcano$padj) &
    volcano$padj < config$bulk$deseq2_alpha &
    abs(volcano$log2FoldChange) >= config$bulk$deseq2_abs_log2fc
  volcano$minus_log10_padj <- -log10(pmax(volcano$padj, .Machine$double.xmin))
  volcano_plot <- ggplot(
    volcano,
    aes(x = log2FoldChange, y = minus_log10_padj, color = significant)
  ) +
    geom_point(alpha = 0.6, size = 1.2, na.rm = TRUE) +
    scale_color_manual(values = c("FALSE" = "grey65", "TRUE" = "firebrick")) +
    labs(title = contrast_id, x = "log2 fold change", y = "-log10 adjusted p-value") +
    theme_bw()
  ggsave(
    file.path(contrast_dir, "volcano_plot.png"),
    volcano_plot,
    width = 8,
    height = 6,
    dpi = 160
  )
  if (nrow(significant) >= 2) {
    heatmap_genes <- head(significant$gene_id, 50)
    heatmap_annotation <- as.data.frame(
      colData(transformed)[, intersect(
        c("dataset_id", "group", "batch", "sex", "subject_id"),
        colnames(colData(transformed))
      ), drop = FALSE]
    )
    heatmap_annotation[] <- lapply(heatmap_annotation, function(values) {
      droplevels(factor(as.character(values)))
    })
    usable_annotations <- vapply(
      heatmap_annotation,
      function(values) !anyNA(values) && nlevels(values) >= 2,
      logical(1)
    )
    heatmap_annotation <- heatmap_annotation[, usable_annotations, drop = FALSE]
    pheatmap(
      transformed_matrix[heatmap_genes, , drop = FALSE],
      scale = "row",
      annotation_col = if (ncol(heatmap_annotation) > 0) heatmap_annotation else NULL,
      filename = file.path(contrast_dir, "deg_heatmap.png"),
      width = 9,
      height = 9
    )
  } else {
    message_plot(
      file.path(contrast_dir, "deg_heatmap.png"),
      "Fewer than two genes pass configured thresholds"
    )
  }

  pca <- prcomp(t(transformed_matrix), center = TRUE, scale. = FALSE)
  variance <- 100 * pca$sdev ^ 2 / sum(pca$sdev ^ 2)
  pca_frame <- data.frame(
    sample_id = rownames(pca$x),
    PC1 = pca$x[, 1],
    PC2 = if (ncol(pca$x) >= 2) pca$x[, 2] else 0,
    group = as.character(metadata[rownames(pca$x), "group"]),
    dataset_id = as.character(metadata[rownames(pca$x), "dataset_id"])
  )
  pca_plot <- ggplot(
    pca_frame,
    aes(x = PC1, y = PC2, color = group, shape = dataset_id, label = sample_id)
  ) +
    geom_point(size = 3) +
    geom_text(vjust = -0.8, check_overlap = TRUE) +
    labs(
      title = paste(contrast_id, "joint-model PCA"),
      x = sprintf("PC1 (%.1f%%)", variance[1]),
      y = sprintf("PC2 (%.1f%%)", ifelse(length(variance) >= 2, variance[2], 0))
    ) +
    theme_bw()
  ggsave(file.path(contrast_dir, "pca.png"), pca_plot, width = 8, height = 6, dpi = 160)

  cooks <- assays(dds)[["cooks"]]
  write_tsv(
    data.frame(
      sample_id = colnames(dds),
      max_cooks_distance = apply(cooks, 2, max, na.rm = TRUE),
      retained_for_analysis = "true"
    ),
    file.path(contrast_dir, "sample_cooks_distance.tsv")
  )
  write_tsv(
    data.frame(
      contrast_id = contrast_id,
      analysis_id = opt$`analysis-id`,
      numerator = numerator,
      denominator = denominator,
      design_formula = contrast$design_formula[[1]],
      design_rank = design_rank,
      design_columns = ncol(design_matrix),
      design_full_rank = "true",
      sample_count = ncol(dds),
      dataset_count = length(unique(metadata$dataset_id)),
      genes_in_raw_matrix = raw_gene_count,
      genes_analyzed = nrow(dds),
      significant_genes = nrow(significant),
      samples_removed = 0,
      combat_seq_used = tolower(as.character(combat_enabled)),
      ordinary_combat_used = "false"
    ),
    file.path(contrast_dir, "contrast_qc.tsv")
  )
  capture.output(sessionInfo(), file = file.path(contrast_dir, "session_info.txt"))
  writeLines(resultsNames(dds), con = file.path(contrast_dir, "results_names.txt"))

  result_manifest[[length(result_manifest) + 1]] <- data.frame(
    analysis_id = opt$`analysis-id`,
    contrast_id = contrast_id,
    full_results = full_path,
    significant_results = significant_path,
    normalized_counts = file.path(contrast_dir, "normalized_counts.tsv"),
    transformed_matrix = transformed_path,
    session_info = file.path(contrast_dir, "session_info.txt")
  )
  effect_summary[[length(effect_summary) + 1]] <- data.frame(
    analysis_id = opt$`analysis-id`,
    contrast_id = contrast_id,
    tested_genes = nrow(result_frame),
    significant_genes = nrow(significant),
    up_genes = sum(significant$log2FoldChange > 0, na.rm = TRUE),
    down_genes = sum(significant$log2FoldChange < 0, na.rm = TRUE)
  )
}

write_tsv(do.call(rbind, result_manifest), file.path(opt$`output-dir`, "results_manifest.tsv"))
write_tsv(
  do.call(rbind, effect_summary),
  file.path(opt$`output-dir`, "effect_direction_summary.tsv")
)
capture.output(sessionInfo(), file = file.path(opt$`output-dir`, "session_info.txt"))
writeLines(
  c(
    paste0("analysis_id=", opt$`analysis-id`),
    paste0("contrast_count=", nrow(contrasts)),
    paste0("combat_seq_used=", tolower(as.character(combat_enabled))),
    "ordinary_combat_used=false"
  ),
  con = file.path(opt$`output-dir`, ".complete")
)
