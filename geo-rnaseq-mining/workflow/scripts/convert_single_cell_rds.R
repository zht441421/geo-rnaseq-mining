#!/usr/bin/env Rscript

suppressPackageStartupMessages(library(optparse))

options <- list(
  make_option("--input", type = "character"),
  make_option("--output", type = "character")
)
opt <- parse_args(OptionParser(option_list = options))
object <- readRDS(opt$input)

if (inherits(object, "Seurat")) {
  if (!requireNamespace("Seurat", quietly = TRUE)) {
    stop("Seurat is required to convert a Seurat RDS")
  }
  object <- Seurat::as.SingleCellExperiment(object)
}
if (!inherits(object, "SingleCellExperiment")) {
  stop("RDS must contain a Seurat or SingleCellExperiment object")
}
if (!requireNamespace("zellkonverter", quietly = TRUE)) {
  stop("zellkonverter is required to convert RDS to AnnData")
}
if (!("counts" %in% SummarizedExperiment::assayNames(object))) {
  stop("RDS object is missing the counts assay")
}
zellkonverter::writeH5AD(object, opt$output, X_name = "counts")
