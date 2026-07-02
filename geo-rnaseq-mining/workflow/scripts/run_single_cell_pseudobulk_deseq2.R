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
  make_option("--dataset-id", type = "character", default = NA),
  make_option("--analysis-id", type = "character", default = NA),
  make_option("--output-dir", type = "character")
)
opt <- parse_args(OptionParser(option_list = option_list))

read_tsv <- function(path) {
  read.delim(path, header = TRUE, sep = "\t", check.names = FALSE,
             stringsAsFactors = FALSE, na.strings = character())
}

write_tsv <- function(value, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  write.table(value, file = path, sep = "\t", quote = FALSE,
              row.names = FALSE, col.names = TRUE)
}

safe_name <- function(value) {
  gsub("[^A-Za-z0-9_.-]", "_", value)
}

message_plot <- function(path, label) {
  png(path, width = 1200, height = 900, res = 140)
  plot.new()
  text(0.5, 0.5, label, cex = 1.2)
  dev.off()
}

coerce_metadata <- function(metadata) {
  factor_columns <- c(
    "pseudobulk_id", "dataset_id", "subject_id", "sample_id", "group",
    "cell_type", "author_label", "condition", "tissue", "batch", "sex",
    "timepoint", "treatment", "paired_group"
  )
  for (column in intersect(factor_columns, colnames(metadata))) {
    metadata[[column]] <- factor(metadata[[column]])
  }
  if ("age" %in% colnames(metadata)) {
    numeric_age <- suppressWarnings(as.numeric(metadata$age))
    if (all(is.na(metadata$age) | !is.na(numeric_age))) {
      metadata$age <- numeric_age
    }
  }
  metadata
}

config <- read_yaml(opt$config)
counts_frame <- read_tsv(opt$counts)
metadata_all <- read_tsv(opt$metadata)
contrasts_all <- read_tsv(opt$contrasts)
plan <- read_tsv(opt$`dataset-plan`)
dir.create(opt$`output-dir`, recursive = TRUE, showWarnings = FALSE)

if (!identical(colnames(counts_frame)[-1], metadata_all$pseudobulk_id)) {
  stop("Pseudobulk count columns differ from metadata order")
}
count_matrix <- as.matrix(counts_frame[, -1, drop = FALSE])
if (any(is.na(count_matrix)) || any(count_matrix < 0) || any(count_matrix %% 1 != 0)) {
  stop("Pseudobulk DESeq2 requires finite non-negative integer raw aggregated counts")
}
storage.mode(count_matrix) <- "integer"
rownames(count_matrix) <- counts_frame$gene_id

if (!is.na(opt$`analysis-id`) && opt$`analysis-id` != "NA") {
  analysis_ids <- opt$`analysis-id`
} else {
  analysis_ids <- unique(plan$analysis_id[
    plan$dataset_id == opt$`dataset-id` & plan$include == "true"
  ])
}
contrasts <- contrasts_all[
  contrasts_all$analysis_id %in% analysis_ids &
    contrasts_all$data_scope == "scrna_pseudobulk" &
    contrasts_all$enabled == "true",
  ,
  drop = FALSE
]
if (nrow(contrasts) == 0) {
  write_tsv(data.frame(status = "skipped_no_scrna_pseudobulk_contrasts"),
            file.path(opt$`output-dir`, "analysis_status.tsv"))
  writeLines("contrast_count=0", file.path(opt$`output-dir`, ".complete"))
  quit(save = "no", status = 0)
}

min_subjects <- config$single_cell$pseudobulk$min_subjects_per_group
manifest <- list()
status_rows <- list()

for (contrast_index in seq_len(nrow(contrasts))) {
  contrast <- contrasts[contrast_index, , drop = FALSE]
  contrast_id <- contrast$contrast_id[[1]]
  for (cell_type in sort(unique(metadata_all$cell_type))) {
    metadata <- metadata_all[
      metadata_all$cell_type == cell_type &
        metadata_all$eligibility == "eligible" &
        metadata_all$group %in% c(contrast$numerator[[1]], contrast$denominator[[1]]),
      ,
      drop = FALSE
    ]
    minimum <- max(as.integer(contrast$min_replicates_per_group[[1]]), as.integer(min_subjects))
    group_subjects <- tapply(metadata$subject_id, metadata$group, function(values) length(unique(values)))
    needed <- c(contrast$numerator[[1]], contrast$denominator[[1]])
    if (!all(needed %in% names(group_subjects)) || any(group_subjects[needed] < minimum)) {
      status_rows[[length(status_rows) + 1]] <- data.frame(
        contrast_id = contrast_id,
        cell_type = cell_type,
        status = "skipped_insufficient_subjects",
        minimum_subjects_per_group = minimum
      )
      next
    }
    metadata <- coerce_metadata(metadata)
    rownames(metadata) <- metadata$pseudobulk_id
    metadata$group <- relevel(factor(as.character(metadata$group)), ref = contrast$denominator[[1]])
    design_formula <- as.formula(contrast$design_formula[[1]])
    variables <- all.vars(design_formula)
    missing_variables <- setdiff(variables, colnames(metadata))
    if (length(missing_variables) > 0) {
      stop(paste("Pseudobulk design variables unavailable:", paste(missing_variables, collapse = ", ")))
    }
    if (any(!complete.cases(metadata[, variables, drop = FALSE]))) {
      stop("Pseudobulk design variables contain missing values")
    }
    design_matrix <- model.matrix(design_formula, metadata)
    if (qr(design_matrix)$rank != ncol(design_matrix)) {
      stop("Pseudobulk design matrix is not full rank")
    }
    selected_counts <- count_matrix[, metadata$pseudobulk_id, drop = FALSE]
    dds <- DESeqDataSetFromMatrix(
      countData = selected_counts,
      colData = metadata,
      design = design_formula
    )
    raw_gene_count <- nrow(dds)
    keep <- rowSums(counts(dds)) > 0
    dds <- dds[keep, ]
    if (nrow(dds) == 0) {
      stop(paste("No genes remain after filtering for", contrast_id, cell_type))
    }
    dds <- tryCatch(
      DESeq(dds),
      error = function(error) {
        if (!grepl("all gene-wise dispersion estimates", conditionMessage(error), fixed = TRUE)) {
          stop(error)
        }
        dds <- estimateSizeFactors(dds)
        dds <- estimateDispersionsGeneEst(dds)
        dispersions(dds) <- mcols(dds)$dispGeneEst
        nbinomWaldTest(dds)
      }
    )
    result <- results(dds, contrast = c("group", contrast$numerator[[1]], contrast$denominator[[1]]),
                      alpha = config$bulk$deseq2_alpha)
    result_frame <- data.frame(gene_id = rownames(result), as.data.frame(result), check.names = FALSE)
    result_frame <- result_frame[order(result_frame$padj, na.last = TRUE), , drop = FALSE]
    significant <- result_frame[
      !is.na(result_frame$padj) &
        result_frame$padj < config$bulk$deseq2_alpha &
        abs(result_frame$log2FoldChange) >= config$bulk$deseq2_abs_log2fc,
      ,
      drop = FALSE
    ]
    output_dir <- file.path(opt$`output-dir`, safe_name(contrast_id), safe_name(cell_type))
    full_path <- file.path(output_dir, "deseq2_full_results.tsv")
    significant_path <- file.path(output_dir, "deseq2_significant_results.tsv")
    write_tsv(result_frame, full_path)
    write_tsv(significant, significant_path)
    write_tsv(data.frame(pseudobulk_id = rownames(metadata), design_matrix, check.names = FALSE),
              file.path(output_dir, "design_matrix.tsv"))
    normalized <- counts(dds, normalized = TRUE)
    write_tsv(data.frame(gene_id = rownames(normalized), normalized, check.names = FALSE),
              file.path(output_dir, "normalized_counts.tsv"))
    transformed_matrix <- tryCatch(
      {
        transformed <- if (nrow(dds) < 1000) {
          varianceStabilizingTransformation(dds, blind = FALSE)
        } else {
          vst(dds, blind = FALSE)
        }
        assay(transformed)
      },
      error = function(error) {
        log2(normalized + 1)
      }
    )

    png(file.path(output_dir, "ma_plot.png"), width = 1200, height = 900, res = 140)
    plotMA(result, alpha = config$bulk$deseq2_alpha, main = paste(contrast_id, cell_type))
    dev.off()
    volcano <- result_frame
    volcano$significant <- !is.na(volcano$padj) &
      volcano$padj < config$bulk$deseq2_alpha &
      abs(volcano$log2FoldChange) >= config$bulk$deseq2_abs_log2fc
    volcano$minus_log10_padj <- -log10(pmax(volcano$padj, .Machine$double.xmin))
    volcano_plot <- ggplot(volcano, aes(x = log2FoldChange, y = minus_log10_padj, color = significant)) +
      geom_point(alpha = 0.6, size = 1.2, na.rm = TRUE) +
      scale_color_manual(values = c("FALSE" = "grey65", "TRUE" = "firebrick")) +
      theme_bw() +
      labs(title = paste(contrast_id, cell_type), x = "log2 fold change", y = "-log10 adjusted p-value")
    ggsave(file.path(output_dir, "volcano_plot.png"), volcano_plot, width = 8, height = 6, dpi = 160)

    if (ncol(transformed_matrix) >= 2 && nrow(transformed_matrix) >= 2) {
      pca <- prcomp(t(transformed_matrix), center = TRUE, scale. = FALSE)
      variance <- 100 * pca$sdev ^ 2 / sum(pca$sdev ^ 2)
      pca_frame <- data.frame(
        pseudobulk_id = rownames(pca$x),
        PC1 = pca$x[, 1],
        PC2 = if (ncol(pca$x) >= 2) pca$x[, 2] else 0,
        group = as.character(metadata[rownames(pca$x), "group"]),
        subject_id = as.character(metadata[rownames(pca$x), "subject_id"])
      )
      write_tsv(pca_frame, file.path(output_dir, "pca.tsv"))
      pca_plot <- ggplot(pca_frame, aes(x = PC1, y = PC2, color = group, label = subject_id)) +
        geom_point(size = 3) +
        geom_text(vjust = -0.8, check_overlap = TRUE) +
        theme_bw() +
        labs(title = paste(contrast_id, cell_type, "PCA"),
             x = sprintf("PC1 (%.1f%%)", variance[1]),
             y = sprintf("PC2 (%.1f%%)", ifelse(length(variance) >= 2, variance[2], 0)))
      ggsave(file.path(output_dir, "pca.png"), pca_plot, width = 8, height = 6, dpi = 160)
      correlation <- cor(transformed_matrix, method = "pearson")
      write_tsv(data.frame(pseudobulk_id = rownames(correlation), correlation, check.names = FALSE),
                file.path(output_dir, "sample_correlation.tsv"))
      pheatmap(correlation, filename = file.path(output_dir, "sample_correlation.png"), width = 8, height = 7)
    } else {
      message_plot(file.path(output_dir, "pca.png"), "Insufficient samples or genes for PCA")
      message_plot(file.path(output_dir, "sample_correlation.png"), "Insufficient samples for correlation")
      write_tsv(data.frame(), file.path(output_dir, "pca.tsv"))
      write_tsv(data.frame(), file.path(output_dir, "sample_correlation.tsv"))
    }

    subject_stats <- aggregate(
      cbind(cell_count = as.numeric(as.character(metadata$cell_count)),
            total_UMI = as.numeric(as.character(metadata$total_UMI))) ~ group,
      data = metadata,
      FUN = sum
    )
    subject_counts <- aggregate(subject_id ~ group, data = metadata, FUN = function(values) length(unique(values)))
    colnames(subject_counts)[2] <- "subject_count"
    stats <- merge(subject_counts, subject_stats, by = "group", all = TRUE)
    stats$contrast_id <- contrast_id
    stats$cell_type <- cell_type
    stats$genes_in_raw_matrix <- raw_gene_count
    stats$genes_analyzed <- nrow(dds)
    stats$significant_genes <- nrow(significant)
    write_tsv(stats, file.path(output_dir, "subject_cell_stats.tsv"))
    write_tsv(metadata, file.path(output_dir, "pseudobulk_samples.tsv"))
    capture.output(sessionInfo(), file = file.path(output_dir, "session_info.txt"))
    manifest[[length(manifest) + 1]] <- data.frame(
      dataset_id = ifelse(is.na(opt$`dataset-id`), paste(unique(metadata$dataset_id), collapse = ";"), opt$`dataset-id`),
      analysis_id = contrast$analysis_id[[1]],
      contrast_id = contrast_id,
      cell_type = cell_type,
      full_results = full_path,
      significant_results = significant_path,
      pca = file.path(output_dir, "pca.png"),
      ma_plot = file.path(output_dir, "ma_plot.png"),
      volcano_plot = file.path(output_dir, "volcano_plot.png"),
      sample_correlation = file.path(output_dir, "sample_correlation.tsv"),
      subject_count = length(unique(metadata$subject_id)),
      cell_count = sum(as.numeric(as.character(metadata$cell_count))),
      cell_replication_used = "false"
    )
  }
}

if (length(manifest) > 0) {
  write_tsv(do.call(rbind, manifest), file.path(opt$`output-dir`, "results_manifest.tsv"))
} else {
  write_tsv(data.frame(status = "no_estimable_celltype_contrasts"),
            file.path(opt$`output-dir`, "analysis_status.tsv"))
}
if (length(status_rows) > 0) {
  write_tsv(do.call(rbind, status_rows), file.path(opt$`output-dir`, "skipped_celltypes.tsv"))
}
capture.output(sessionInfo(), file = file.path(opt$`output-dir`, "session_info.txt"))
writeLines(
  c(
    paste0("result_count=", length(manifest)),
    "replicate_unit=subject_id",
    "cell_replication_used=false"
  ),
  file.path(opt$`output-dir`, ".complete")
)
