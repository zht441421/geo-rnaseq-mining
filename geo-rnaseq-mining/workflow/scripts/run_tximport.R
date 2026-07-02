#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(optparse)
  library(tximport)
})

option_list <- list(
  make_option("--manifest", type = "character"),
  make_option("--dataset-id", type = "character"),
  make_option("--quant-root", type = "character"),
  make_option("--tx2gene", type = "character"),
  make_option("--counts", type = "character"),
  make_option("--unrounded-counts", type = "character"),
  make_option("--abundance", type = "character"),
  make_option("--length", type = "character"),
  make_option("--summary", type = "character"),
  make_option("--session-info", type = "character")
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

write_matrix <- function(matrix_value, path, round_values = FALSE) {
  output <- data.frame(
    gene_id = rownames(matrix_value),
    matrix_value,
    check.names = FALSE
  )
  if (round_values) {
    output[, -1] <- lapply(
      output[, -1, drop = FALSE],
      function(values) as.integer(round(values))
    )
  }
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  write.table(
    output,
    file = path,
    sep = "\t",
    quote = FALSE,
    row.names = FALSE,
    col.names = TRUE
  )
}

manifest <- read_tsv(opt$manifest)
active <- manifest[
  manifest$dataset_id == opt$`dataset-id` &
    manifest$include == "true" &
    manifest$review_status == "confirmed" &
    grepl("bulk", manifest$data_type, ignore.case = TRUE) &
    !grepl("pseudobulk", manifest$data_type, ignore.case = TRUE),
  ,
  drop = FALSE
]
if (nrow(active) == 0) {
  stop("No active reviewed bulk samples were found for tximport")
}
sample_ids <- active$sample_id
quant_files <- file.path(opt$`quant-root`, sample_ids, "quant.sf")
names(quant_files) <- sample_ids
missing_files <- quant_files[!file.exists(quant_files)]
if (length(missing_files) > 0) {
  stop(paste("Missing Salmon quant files:", paste(missing_files, collapse = ", ")))
}

tx2gene <- read_tsv(opt$tx2gene)
if (ncol(tx2gene) < 2) {
  stop("tx2gene must contain at least transcript and gene columns")
}
tx2gene <- tx2gene[, 1:2, drop = FALSE]
colnames(tx2gene) <- c("TXNAME", "GENEID")
if (anyDuplicated(tx2gene$TXNAME)) {
  stop("tx2gene transcript identifiers must be unique")
}

txi <- tximport(
  quant_files,
  type = "salmon",
  tx2gene = tx2gene,
  txOut = FALSE,
  countsFromAbundance = "no",
  ignoreTxVersion = FALSE
)
if (!identical(colnames(txi$counts), sample_ids)) {
  stop("tximport output order differs from reviewed manifest order")
}

write_matrix(txi$counts, opt$`unrounded-counts`)
write_matrix(txi$counts, opt$counts, round_values = TRUE)
write_matrix(txi$abundance, opt$abundance)
write_matrix(txi$length, opt$length)

summary <- data.frame(
  dataset_id = opt$`dataset-id`,
  sample_id = sample_ids,
  transcript_quantifier = "Salmon",
  aggregation = "tximport",
  counts_from_abundance = "no",
  rounded_for_count_matrix = "true",
  unrounded_counts_retained = opt$`unrounded-counts`,
  stringsAsFactors = FALSE
)
dir.create(dirname(opt$summary), recursive = TRUE, showWarnings = FALSE)
write.table(
  summary,
  file = opt$summary,
  sep = "\t",
  quote = FALSE,
  row.names = FALSE
)
capture.output(sessionInfo(), file = opt$`session-info`)
