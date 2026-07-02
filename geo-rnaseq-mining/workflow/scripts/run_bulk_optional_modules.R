#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(optparse)
  library(yaml)
})

option_list <- list(
  make_option("--config", type = "character"),
  make_option("--dataset-id", type = "character"),
  make_option("--deseq-dir", type = "character"),
  make_option("--metadata", type = "character"),
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

read_expression <- function(path) {
  frame <- read_tsv(path)
  matrix <- as.matrix(frame[, -1, drop = FALSE])
  storage.mode(matrix) <- "numeric"
  rownames(matrix) <- frame[[1]]
  matrix
}

read_gmt <- function(path) {
  definitions <- strsplit(readLines(path, warn = FALSE), "\t", fixed = TRUE)
  sets <- lapply(definitions, function(parts) unique(parts[-c(1, 2)]))
  names(sets) <- vapply(definitions, `[[`, character(1), 1)
  sets
}

run_wgcna <- function(expression, settings, output_dir) {
  if (ncol(expression) < 4 || nrow(expression) < 10) {
    return("not_estimable_insufficient_samples_or_genes")
  }
  data_expression <- t(expression)
  finite_genes <- apply(data_expression, 2, function(values) {
    all(is.finite(values)) && stats::sd(values) > 0
  })
  data_expression <- data_expression[, finite_genes, drop = FALSE]
  if (ncol(data_expression) < 10) {
    return("not_estimable_after_quality_filter")
  }
  correlations <- stats::cor(data_expression, use = "pairwise.complete.obs")
  adjacency <- ((1 + correlations) / 2) ^ as.numeric(settings$soft_power)
  diag(adjacency) <- 0
  connectivity <- rowSums(adjacency)
  shared_neighbors <- adjacency %*% adjacency
  denominator <- outer(connectivity, connectivity, pmin) + 1 - adjacency
  tom <- (shared_neighbors + adjacency) / pmax(denominator, .Machine$double.eps)
  diag(tom) <- 1
  dissimilarity <- 1 - tom
  tree <- hclust(as.dist(dissimilarity), method = "average")
  minimum_size <- as.integer(settings$min_module_size)
  requested_modules <- max(
    2,
    min(
      floor(ncol(data_expression) / minimum_size),
      ncol(data_expression)
    )
  )
  modules <- stats::cutree(tree, k = requested_modules)
  module_sizes <- table(modules)
  modules[module_sizes[as.character(modules)] < minimum_size] <- 0
  colors <- ifelse(modules == 0, "grey", paste0("module_", modules))
  eigengene_list <- lapply(
    setdiff(unique(colors), "grey"),
    function(module) {
      values <- data_expression[, colors == module, drop = FALSE]
      component <- stats::prcomp(values, center = TRUE, scale. = TRUE)$x[, 1]
      component
    }
  )
  if (length(eigengene_list) > 0) {
    eigengenes <- do.call(cbind, eigengene_list)
    colnames(eigengenes) <- setdiff(unique(colors), "grey")
  } else {
    eigengenes <- matrix(
      numeric(),
      nrow = nrow(data_expression),
      ncol = 0,
      dimnames = list(rownames(data_expression), character())
    )
  }
  write_tsv(
    data.frame(
      gene_id = colnames(data_expression),
      module = colors,
      stringsAsFactors = FALSE
    ),
    file.path(output_dir, "gene_modules.tsv")
  )
  write_tsv(
    data.frame(
      sample_id = rownames(eigengenes),
      eigengenes,
      check.names = FALSE
    ),
    file.path(output_dir, "module_eigengenes.tsv")
  )
  write_tsv(
    data.frame(
      gene_id = rownames(adjacency),
      connectivity = connectivity,
      stringsAsFactors = FALSE
    ),
    file.path(output_dir, "network_connectivity.tsv")
  )
  "completed"
}

run_immune <- function(expression, settings, output_dir) {
  path <- settings$signature_matrix
  if (is.null(path) || !file.exists(path)) {
    stop("An existing immune signature_matrix is required when enabled")
  }
  if (!requireNamespace("nnls", quietly = TRUE)) {
    stop("nnls package is required for immune infiltration")
  }
  signature_frame <- read_tsv(path)
  signature <- as.matrix(signature_frame[, -1, drop = FALSE])
  storage.mode(signature) <- "numeric"
  rownames(signature) <- signature_frame[[1]]
  genes <- intersect(rownames(expression), rownames(signature))
  if (length(genes) < 10) {
    stop("Fewer than 10 genes overlap the immune signature matrix")
  }
  estimates <- vapply(
    colnames(expression),
    function(sample_id) {
      fit <- nnls::nnls(signature[genes, , drop = FALSE], expression[genes, sample_id])
      values <- pmax(fit$x, 0)
      if (sum(values) > 0) values / sum(values) else values
    },
    numeric(ncol(signature))
  )
  rownames(estimates) <- colnames(signature)
  write_tsv(
    data.frame(
      cell_type = rownames(estimates),
      estimates,
      check.names = FALSE
    ),
    file.path(output_dir, "immune_proportions.tsv")
  )
  "completed"
}

run_gsva <- function(expression, settings, output_dir) {
  path <- settings$gene_sets_gmt
  if (is.null(path) || !file.exists(path)) {
    stop("An existing GSVA gene_sets_gmt is required when enabled")
  }
  if (!identical(settings$method, "zscore")) {
    stop("Supported dependency-free GSVA method is zscore")
  }
  gene_sets <- read_gmt(path)
  standardized <- t(scale(t(expression)))
  standardized[!is.finite(standardized)] <- 0
  score_rows <- lapply(names(gene_sets), function(pathway) {
    genes <- intersect(gene_sets[[pathway]], rownames(standardized))
    if (length(genes) == 0) {
      return(NULL)
    }
    score <- colSums(standardized[genes, , drop = FALSE]) /
      sqrt(length(genes))
    data.frame(
      pathway = pathway,
      method = "zscore",
      t(score),
      check.names = FALSE
    )
  })
  score_rows <- Filter(Negate(is.null), score_rows)
  if (length(score_rows) == 0) {
    stop("No GSVA gene sets overlap the expression matrix")
  }
  scores <- do.call(rbind, score_rows)
  write_tsv(
    scores,
    file.path(output_dir, "gsva_scores.tsv")
  )
  "completed"
}

run_survival <- function(expression, settings, output_dir) {
  path <- settings$metadata_file
  if (is.null(path) || !file.exists(path)) {
    stop("An existing survival metadata_file is required when enabled")
  }
  if (!requireNamespace("survival", quietly = TRUE)) {
    stop("survival package is required when bulk.optional_modules.survival=true")
  }
  metadata <- read_tsv(path)
  required <- c(
    settings$sample_id_column,
    settings$time_column,
    settings$event_column
  )
  if (!all(required %in% colnames(metadata))) {
    stop("Survival metadata lacks configured sample/time/event columns")
  }
  sample_ids <- intersect(
    colnames(expression),
    metadata[[settings$sample_id_column]]
  )
  if (length(sample_ids) < 5) {
    return("not_estimable_fewer_than_five_samples")
  }
  metadata <- metadata[
    match(sample_ids, metadata[[settings$sample_id_column]]),
    ,
    drop = FALSE
  ]
  variances <- apply(expression[, sample_ids, drop = FALSE], 1, var)
  genes <- names(
    head(sort(variances, decreasing = TRUE), as.integer(settings$max_genes))
  )
  rows <- lapply(genes, function(gene_id) {
    frame <- data.frame(
      time = as.numeric(metadata[[settings$time_column]]),
      event = as.numeric(metadata[[settings$event_column]]),
      expression = as.numeric(expression[gene_id, sample_ids])
    )
    fit <- tryCatch(
      survival::coxph(
        survival::Surv(time, event) ~ expression,
        data = frame
      ),
      error = function(error) NULL
    )
    if (is.null(fit)) {
      return(NULL)
    }
    summary <- summary(fit)
    data.frame(
      gene_id = gene_id,
      hazard_ratio = summary$coefficients[1, "exp(coef)"],
      coefficient = summary$coefficients[1, "coef"],
      standard_error = summary$coefficients[1, "se(coef)"],
      pvalue = summary$coefficients[1, "Pr(>|z|)"],
      stringsAsFactors = FALSE
    )
  })
  rows <- Filter(Negate(is.null), rows)
  if (length(rows) == 0) {
    return("not_estimable_no_converged_models")
  }
  results <- do.call(rbind, rows)
  results$padj <- p.adjust(results$pvalue, method = "BH")
  write_tsv(
    results[order(results$padj, results$pvalue), , drop = FALSE],
    file.path(output_dir, "univariate_cox.tsv")
  )
  "completed"
}

config <- read_yaml(opt$config)
optional <- config$bulk$optional_modules
manifest <- read_tsv(file.path(opt$`deseq-dir`, "results_manifest.tsv"))
metadata <- read_tsv(opt$metadata)
dir.create(opt$`output-dir`, recursive = TRUE, showWarnings = FALSE)
status <- list()

definitions <- list(
  wgcna = list(
    enabled = isTRUE(optional$wgcna),
    settings = optional$wgcna_settings,
    runner = run_wgcna
  ),
  immune_infiltration = list(
    enabled = isTRUE(optional$immune_infiltration),
    settings = optional$immune_infiltration_settings,
    runner = run_immune
  ),
  gsva = list(
    enabled = isTRUE(optional$gsva),
    settings = optional$gsva_settings,
    runner = run_gsva
  ),
  survival = list(
    enabled = isTRUE(optional$survival),
    settings = optional$survival_settings,
    runner = run_survival
  )
)

for (module in names(definitions)) {
  definition <- definitions[[module]]
  if (!definition$enabled) {
    status[[length(status) + 1]] <- data.frame(
      dataset_id = opt$`dataset-id`,
      contrast_id = "NA",
      module = module,
      enabled = "false",
      status = "disabled",
      message = "Disabled by config.",
      stringsAsFactors = FALSE
    )
    next
  }
  for (index in seq_len(nrow(manifest))) {
    contrast_id <- manifest$contrast_id[[index]]
    expression <- read_expression(manifest$transformed_matrix[[index]])
    output_dir <- file.path(
      opt$`output-dir`,
      safe_name(contrast_id),
      module
    )
    module_status <- definition$runner(
      expression,
      definition$settings,
      output_dir
    )
    status[[length(status) + 1]] <- data.frame(
      dataset_id = opt$`dataset-id`,
      contrast_id = contrast_id,
      module = module,
      enabled = "true",
      status = module_status,
      message = output_dir,
      stringsAsFactors = FALSE
    )
  }
}

write_tsv(
  do.call(rbind, status),
  file.path(opt$`output-dir`, "optional_modules_status.tsv")
)
capture.output(sessionInfo(), file = file.path(opt$`output-dir`, "session_info.txt"))
writeLines(
  c(
    paste0("dataset_id=", opt$`dataset-id`),
    paste0("enabled_module_count=", sum(vapply(
      definitions,
      function(value) value$enabled,
      logical(1)
    )))
  ),
  file.path(opt$`output-dir`, ".complete")
)
