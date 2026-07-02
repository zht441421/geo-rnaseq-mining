#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(GEOquery)
  library(jsonlite)
  library(optparse)
})

option_list <- list(
  make_option("--accessions", type = "character", default = ""),
  make_option("--series-output", type = "character", dest = "series_output"),
  make_option("--samples-output", type = "character", dest = "samples_output"),
  make_option(
    "--platforms-output",
    type = "character",
    dest = "platforms_output"
  ),
  make_option("--event-log", type = "character", dest = "event_log"),
  make_option("--cache-dir", type = "character", dest = "cache_dir"),
  make_option("--retries", type = "integer", default = 3),
  make_option(
    "--retry-delay",
    type = "double",
    default = 5,
    dest = "retry_delay"
  )
)
opt <- parse_args(OptionParser(option_list = option_list))

na_value <- "NA"
now_utc <- function() {
  format(Sys.time(), tz = "UTC", usetz = TRUE)
}

clean_scalar <- function(value) {
  flattened <- as.character(unlist(value, recursive = TRUE, use.names = FALSE))
  flattened <- flattened[!is.na(flattened) & nzchar(flattened)]
  if (length(flattened) == 0) na_value else flattened[[1]]
}

clean_vector <- function(value) {
  flattened <- as.character(unlist(value, recursive = TRUE, use.names = FALSE))
  flattened <- flattened[!is.na(flattened) & nzchar(flattened)]
  if (length(flattened) == 0) character(0) else flattened
}

metadata_entries_json <- function(metadata, indices = seq_along(metadata)) {
  entries <- lapply(indices, function(index) {
    list(
      field_name = names(metadata)[[index]],
      values = as.character(
        unlist(metadata[[index]], recursive = TRUE, use.names = TRUE)
      )
    )
  })
  toJSON(entries, auto_unbox = FALSE, null = "null", na = "string")
}

meta_json <- function(metadata) {
  metadata_entries_json(metadata)
}

meta_value <- function(metadata, candidates) {
  for (candidate in candidates) {
    if (!is.null(metadata[[candidate]])) {
      return(clean_scalar(metadata[[candidate]]))
    }
  }
  na_value
}

characteristics_json <- function(metadata) {
  indices <- grep("^characteristics_ch1", names(metadata))
  if (length(indices) == 0) return(na_value)
  metadata_entries_json(metadata, indices)
}

extract_srx <- function(metadata) {
  relation_keys <- grep("^relation", names(metadata), value = TRUE)
  relation_values <- unlist(metadata[relation_keys], use.names = FALSE)
  hits <- regmatches(
    relation_values,
    gregexpr("SRX[0-9]+", relation_values, perl = TRUE)
  )
  accessions <- unique(unlist(hits, use.names = FALSE))
  accessions <- accessions[nzchar(accessions)]
  if (length(accessions) == 0) na_value else paste(accessions, collapse = ";")
}

append_event <- function(events, rule, accession, severity, event_type, message,
                         suggested_action, attempt = na_value,
                         cache_hit = FALSE) {
  events[[length(events) + 1]] <- data.frame(
    timestamp_utc = now_utc(),
    rule = rule,
    accession = accession,
    severity = severity,
    event_type = event_type,
    message = gsub("[\t\r\n]+", " ", as.character(message)),
    suggested_action = suggested_action,
    attempt = as.character(attempt),
    cache_hit = tolower(as.character(cache_hit)),
    stringsAsFactors = FALSE
  )
  events
}

write_rows <- function(rows, columns, path) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  if (length(rows) == 0) {
    result <- as.data.frame(
      setNames(replicate(length(columns), character(0), simplify = FALSE), columns),
      stringsAsFactors = FALSE
    )
  } else {
    result <- do.call(rbind, rows)
    result <- result[, columns, drop = FALSE]
    result[is.na(result) | result == ""] <- na_value
  }
  write.table(
    result,
    file = path,
    sep = "\t",
    row.names = FALSE,
    col.names = TRUE,
    quote = TRUE,
    na = na_value,
    fileEncoding = "UTF-8"
  )
}

fetch_geo <- function(accession, cache_file, retries, retry_delay) {
  if (file.exists(cache_file)) {
    return(list(object = readRDS(cache_file), cache_hit = TRUE, attempt = 0))
  }
  last_error <- NULL
  for (attempt in seq_len(retries)) {
    result <- tryCatch(
      getGEO(
        accession,
        GSEMatrix = FALSE,
        getGPL = TRUE,
        AnnotGPL = FALSE,
        destdir = dirname(cache_file)
      ),
      error = function(error) {
        last_error <<- error
        NULL
      }
    )
    if (!is.null(result)) {
      if (is.list(result) && !inherits(result, "GSE")) result <- result[[1]]
      saveRDS(result, cache_file)
      return(list(object = result, cache_hit = FALSE, attempt = attempt))
    }
    if (attempt < retries) Sys.sleep(retry_delay)
  }
  stop(sprintf(
    "GEOquery failed after %d attempts for %s: %s",
    retries, accession, conditionMessage(last_error)
  ))
}

series_columns <- c(
  "gse_accession", "title", "summary", "overall_design", "submission_date",
  "last_update_date", "pubmed_id", "organism", "raw_metadata_json",
  "fetched_at_utc", "cache_hit"
)
sample_columns <- c(
  "gse_accession", "gsm_accession", "title", "source_name", "organism",
  "platform", "characteristics_ch1_raw", "relation_raw", "srx_accessions",
  "raw_metadata_json", "fetched_at_utc", "cache_hit"
)
platform_columns <- c(
  "gse_accession", "gpl_accession", "title", "technology", "organism",
  "manufacturer", "raw_metadata_json", "fetched_at_utc", "cache_hit"
)

series_rows <- list()
sample_rows <- list()
platform_rows <- list()
events <- list()
accessions <- unique(trimws(strsplit(opt$accessions, ",", fixed = TRUE)[[1]]))
accessions <- accessions[nzchar(accessions)]
dir.create(opt$cache_dir, recursive = TRUE, showWarnings = FALSE)

if (length(accessions) == 0) {
  events <- append_event(
    events, "fetch_geo_metadata", na_value, "WARNING", "NO_ACCESSIONS",
    "No GSE accessions were configured; header-only raw metadata files were created.",
    "Add one or more GSE accessions under geo.accessions in config/config.yaml."
  )
}

for (accession in accessions) {
  cache_file <- file.path(opt$cache_dir, paste0(accession, ".rds"))
  fetched <- tryCatch(
    fetch_geo(accession, cache_file, opt$retries, opt$retry_delay),
    error = function(error) {
      events <<- append_event(
        events, "fetch_geo_metadata", accession, "ERROR", "GEO_FETCH_FAILED",
        conditionMessage(error),
        "Check the accession, network access, NCBI/GEO availability, and retry."
      )
      NULL
    }
  )
  if (is.null(fetched)) next

  tryCatch({
    gse <- fetched$object
    fetched_at <- now_utc()
    gse_meta <- Meta(gse)
    gsm_list <- GSMList(gse)
    gpl_list <- GPLList(gse)
    sample_organisms <- unique(vapply(
      gsm_list,
      function(gsm) meta_value(Meta(gsm), c("organism_ch1", "organism")),
      character(1)
    ))
    sample_organisms <- sample_organisms[sample_organisms != na_value]

    series_rows[[length(series_rows) + 1]] <- data.frame(
      gse_accession = accession,
      title = meta_value(gse_meta, c("title")),
      summary = meta_value(gse_meta, c("summary")),
      overall_design = meta_value(gse_meta, c("overall_design")),
      submission_date = meta_value(gse_meta, c("submission_date")),
      last_update_date = meta_value(gse_meta, c("last_update_date")),
      pubmed_id = meta_value(gse_meta, c("pubmed_id")),
      organism = if (length(sample_organisms) == 0) na_value else
        paste(sample_organisms, collapse = ";"),
      raw_metadata_json = meta_json(gse_meta),
      fetched_at_utc = fetched_at,
      cache_hit = tolower(as.character(fetched$cache_hit)),
      stringsAsFactors = FALSE
    )

    for (gsm_accession in names(gsm_list)) {
      gsm_meta <- Meta(gsm_list[[gsm_accession]])
      relation_indices <- grep("^relation", names(gsm_meta))
      relation_values <- if (length(relation_indices) == 0) na_value else
        metadata_entries_json(gsm_meta, relation_indices)
      sample_rows[[length(sample_rows) + 1]] <- data.frame(
        gse_accession = accession,
        gsm_accession = gsm_accession,
        title = meta_value(gsm_meta, c("title")),
        source_name = meta_value(gsm_meta, c("source_name_ch1", "source_name")),
        organism = meta_value(gsm_meta, c("organism_ch1", "organism")),
        platform = meta_value(gsm_meta, c("platform_id")),
        characteristics_ch1_raw = characteristics_json(gsm_meta),
        relation_raw = relation_values,
        srx_accessions = extract_srx(gsm_meta),
        raw_metadata_json = meta_json(gsm_meta),
        fetched_at_utc = fetched_at,
        cache_hit = tolower(as.character(fetched$cache_hit)),
        stringsAsFactors = FALSE
      )
    }

    for (gpl_accession in names(gpl_list)) {
      gpl_meta <- Meta(gpl_list[[gpl_accession]])
      platform_rows[[length(platform_rows) + 1]] <- data.frame(
        gse_accession = accession,
        gpl_accession = gpl_accession,
        title = meta_value(gpl_meta, c("title")),
        technology = meta_value(gpl_meta, c("technology")),
        organism = meta_value(gpl_meta, c("organism")),
        manufacturer = meta_value(gpl_meta, c("manufacturer")),
        raw_metadata_json = meta_json(gpl_meta),
        fetched_at_utc = fetched_at,
        cache_hit = tolower(as.character(fetched$cache_hit)),
        stringsAsFactors = FALSE
      )
    }

    events <- append_event(
      events, "fetch_geo_metadata", accession, "INFO", "GEO_FETCH_COMPLETE",
      sprintf(
        "Fetched %d GSM and %d GPL records.",
        length(gsm_list), length(gpl_list)
      ),
      "No action required.",
      fetched$attempt,
      fetched$cache_hit
    )
  }, error = function(error) {
    events <<- append_event(
      events, "fetch_geo_metadata", accession, "ERROR", "GEO_PARSE_FAILED",
      conditionMessage(error),
      "Inspect the cached GEO object and raw GEO record, then rerun."
    )
  }
  )
}

write_rows(series_rows, series_columns, opt$series_output)
write_rows(sample_rows, sample_columns, opt$samples_output)
write_rows(platform_rows, platform_columns, opt$platforms_output)
event_columns <- c(
  "timestamp_utc", "rule", "accession", "severity", "event_type", "message",
  "suggested_action", "attempt", "cache_hit"
)
write_rows(events, event_columns, opt$event_log)
