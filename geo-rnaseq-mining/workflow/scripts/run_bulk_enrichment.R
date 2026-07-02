#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(optparse)
  library(yaml)
})

option_list <- list(
  make_option("--config", type = "character"),
  make_option("--dataset-id", type = "character"),
  make_option("--deseq-dir", type = "character"),
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

read_gmt <- function(path) {
  lines <- readLines(path, warn = FALSE)
  pathways <- lapply(strsplit(lines, "\t", fixed = TRUE), function(parts) {
    unique(parts[-c(1, 2)])
  })
  names(pathways) <- vapply(
    strsplit(lines, "\t", fixed = TRUE),
    function(parts) parts[[1]],
    character(1)
  )
  pathways
}

empty_ora <- function() {
  data.frame(
    database = character(),
    direction = character(),
    pathway = character(),
    overlap = integer(),
    pathway_size = integer(),
    selected_size = integer(),
    universe_size = integer(),
    pvalue = numeric(),
    padj = numeric(),
    leading_genes = character(),
    stringsAsFactors = FALSE
  )
}

run_ora <- function(selected, universe, pathways, database, direction, min_size, max_size) {
  selected <- intersect(unique(selected), universe)
  rows <- lapply(names(pathways), function(pathway_name) {
    members <- intersect(unique(pathways[[pathway_name]]), universe)
    if (length(members) < min_size || length(members) > max_size) {
      return(NULL)
    }
    overlap <- intersect(selected, members)
    pvalue <- phyper(
      length(overlap) - 1,
      length(members),
      length(universe) - length(members),
      length(selected),
      lower.tail = FALSE
    )
    data.frame(
      database = database,
      direction = direction,
      pathway = pathway_name,
      overlap = length(overlap),
      pathway_size = length(members),
      selected_size = length(selected),
      universe_size = length(universe),
      pvalue = pvalue,
      padj = NA_real_,
      leading_genes = paste(overlap, collapse = ";"),
      stringsAsFactors = FALSE
    )
  })
  rows <- Filter(Negate(is.null), rows)
  if (length(rows) == 0) {
    return(empty_ora())
  }
  output <- do.call(rbind, rows)
  output$padj <- p.adjust(output$pvalue, method = "BH")
  output[order(output$padj, output$pvalue), , drop = FALSE]
}

safe_name <- function(value) {
  gsub("[^A-Za-z0-9_.-]", "_", value)
}

config <- read_yaml(opt$config)
enrichment_config <- config$bulk$enrichment
result_manifest <- read_tsv(
  file.path(opt$`deseq-dir`, "results_manifest.tsv")
)
dir.create(opt$`output-dir`, recursive = TRUE, showWarnings = FALSE)
status_rows <- list()

for (index in seq_len(nrow(result_manifest))) {
  result_row <- result_manifest[index, , drop = FALSE]
  contrast_id <- result_row$contrast_id[[1]]
  output_dir <- file.path(opt$`output-dir`, safe_name(contrast_id))
  dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)
  full_results <- read_tsv(result_row$full_results[[1]])
  significant <- read_tsv(result_row$significant_results[[1]])
  universe <- unique(full_results$gene_id)
  up <- significant$gene_id[significant$log2FoldChange > 0]
  down <- significant$gene_id[significant$log2FoldChange < 0]

  for (definition in list(
    list(name = "GO", path = enrichment_config$go_gmt, file = "go_enrichment.tsv"),
    list(
      name = "Reactome_or_KEGG",
      path = enrichment_config$pathway_gmt,
      file = "pathway_enrichment.tsv"
    )
  )) {
    destination <- file.path(output_dir, definition$file)
    if (is.null(definition$path) || !file.exists(definition$path)) {
      write_tsv(empty_ora(), destination)
      status_rows[[length(status_rows) + 1]] <- data.frame(
        dataset_id = opt$`dataset-id`,
        contrast_id = contrast_id,
        module = definition$name,
        status = "skipped_missing_gmt",
        message = "Configure an existing GMT file to run this enrichment module.",
        stringsAsFactors = FALSE
      )
    } else {
      pathways <- read_gmt(definition$path)
      ora <- rbind(
        run_ora(
          up,
          universe,
          pathways,
          definition$name,
          "up",
          enrichment_config$min_gene_set_size,
          enrichment_config$max_gene_set_size
        ),
        run_ora(
          down,
          universe,
          pathways,
          definition$name,
          "down",
          enrichment_config$min_gene_set_size,
          enrichment_config$max_gene_set_size
        )
      )
      write_tsv(ora, destination)
      status_rows[[length(status_rows) + 1]] <- data.frame(
        dataset_id = opt$`dataset-id`,
        contrast_id = contrast_id,
        module = definition$name,
        status = "completed",
        message = definition$path,
        stringsAsFactors = FALSE
      )
    }
  }

  gsea_path <- file.path(output_dir, "gsea.tsv")
  if (
    is.null(enrichment_config$gsea_gmt) ||
      !file.exists(enrichment_config$gsea_gmt)
  ) {
    write_tsv(
      data.frame(
        pathway = character(),
        pval = numeric(),
        padj = numeric(),
        ES = numeric(),
        NES = numeric(),
        size = integer(),
        leadingEdge = character(),
        stringsAsFactors = FALSE
      ),
      gsea_path
    )
    status_rows[[length(status_rows) + 1]] <- data.frame(
      dataset_id = opt$`dataset-id`,
      contrast_id = contrast_id,
      module = "GSEA",
      status = "skipped_missing_gmt",
      message = "Configure bulk.enrichment.gsea_gmt.",
      stringsAsFactors = FALSE
    )
  } else if (!requireNamespace("fgsea", quietly = TRUE)) {
    stop("fgsea is required when a GSEA GMT is configured")
  } else {
    rankings <- full_results$stat
    names(rankings) <- full_results$gene_id
    rankings <- sort(rankings[is.finite(rankings)], decreasing = TRUE)
    pathways <- read_gmt(enrichment_config$gsea_gmt)
    gsea <- fgsea::fgseaMultilevel(
      pathways = pathways,
      stats = rankings,
      minSize = enrichment_config$min_gene_set_size,
      maxSize = enrichment_config$max_gene_set_size
    )
    gsea <- as.data.frame(gsea)
    if ("leadingEdge" %in% colnames(gsea)) {
      gsea$leadingEdge <- vapply(
        gsea$leadingEdge,
        paste,
        collapse = ";",
        FUN.VALUE = character(1)
      )
    }
    write_tsv(gsea, gsea_path)
    status_rows[[length(status_rows) + 1]] <- data.frame(
      dataset_id = opt$`dataset-id`,
      contrast_id = contrast_id,
      module = "GSEA",
      status = "completed",
      message = enrichment_config$gsea_gmt,
      stringsAsFactors = FALSE
    )
  }
}

optional <- config$bulk$optional_modules
optional_names <- c("wgcna", "immune_infiltration", "gsva", "survival")
optional_enabled <- vapply(
  optional_names,
  function(name) isTRUE(optional[[name]]),
  logical(1)
)
optional_status <- data.frame(
  module = optional_names,
  enabled = tolower(as.character(optional_enabled)),
  status = ifelse(
    optional_enabled,
    "delegated_to_bulk_optional_modules",
    "disabled"
  ),
  stringsAsFactors = FALSE
)
write_tsv(optional_status, file.path(opt$`output-dir`, "optional_modules_status.tsv"))
write_tsv(
  do.call(rbind, status_rows),
  file.path(opt$`output-dir`, "enrichment_status.tsv")
)
capture.output(sessionInfo(), file = file.path(opt$`output-dir`, "session_info.txt"))
writeLines(
  c(
    paste0("dataset_id=", opt$`dataset-id`),
    paste0("contrast_count=", nrow(result_manifest))
  ),
  con = file.path(opt$`output-dir`, ".complete")
)
