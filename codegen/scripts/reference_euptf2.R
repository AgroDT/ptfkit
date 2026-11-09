# Run only against an installed, authenticated upstream euptf2 package.
# This script never reads the converted container or calls ptfkit inference.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L, !dir.exists(args[2]))
.libPaths(c(args[1], .libPaths()))
library(euptf2)
library(jsonlite)
stopifnot(as.character(packageVersion("euptf2")) == "1.0.0",
          as.character(packageVersion("ranger")) == "0.18.0")
dir.create(args[2], recursive = TRUE)
audit <- lapply(sprintf("THS_PTF%02d", 1:5), function(name) {
    e <- new.env()
    data(list = name, package = "euptf2", envir = e)
    model <- e[[name]]
    forest <- model$forest
    leaves <- lapply(forest$child.nodeIDs, function(x) which(x[[1]] == 0 & x[[2]] == 0))
    finite <- vapply(seq_along(leaves), function(i) {
        all(is.finite(model$random.node.values[leaves[[i]], i]))
    }, logical(1))
    list(name = name, class = class(model), forest_class = class(forest),
         members = names(model), forest_members = names(forest),
         predictors = forest$independent.variable.names, ordered = forest$is.ordered,
         dependent_var_id = forest$dependent.varID,
         trees = model$num.trees, samples = model$num.samples,
         nodes = sum(lengths(forest$split.values)), leaves = sum(lengths(leaves)),
         random_node_values_dim = dim(model$random.node.values),
         all_leaf_samples_finite = all(finite))
})
data(sample_data, package = "euptf2")
features <- c("USSAND", "USSILT", "USCLAY", "DEPTH_M")
inputs <- as.data.frame(sample_data)[, features]
textures <- rbind(c(100, 0, 0), c(0, 100, 0), c(0, 0, 100), c(40, 40, 20))
for (i in seq_len(nrow(textures))) {
    for (depth in c(0, 30, 200)) inputs[nrow(inputs)+1L, ] <- c(textures[i, ], depth)
}
# Exact root boundaries and small perturbations, using the original forest.
data(THS_PTF01, package = "euptf2")
for (tree in seq_len(12)) {
    feature <- THS_PTF01$forest$split.varIDs[[tree]][1]
    threshold <- THS_PTF01$forest$split.values[[tree]][1]
    for (delta in c(-1e-10, 0, 1e-10)) {
        row <- c(40, 40, 20, 30)
        row[feature] <- threshold + delta # old variable IDs are 1-based here
        inputs[nrow(inputs)+1L, ] <- row
    }
}
inputs[nrow(inputs)+1L, ] <- c(-1, 50, 51, -10)
inputs[nrow(inputs)+1L, ] <- c(120, 10, 0, 1000)
means <- suppressWarnings(euptfFun("PTF01", inputs, target = "THS", query = "predictions"))
quantiles <- suppressWarnings(euptfFun("PTF01", inputs, target = "THS", query = "quantiles",
                                     quantiles = c(0.05, 0.5, 0.95)))
cases <- lapply(seq_len(nrow(inputs)), function(i) {
    list(inputs = as.numeric(inputs[i, ]),
         expected = c(means[i, 1], as.numeric(quantiles[i, 1:3])))
})
missing <- inputs[1:3, ]
missing[2, "DEPTH_M"] <- NA_real_
missing_result <- suppressWarnings(euptfFun("PTF01", missing, target = "THS"))
stopifnot(identical(missing_result$OBS_ID, c(1L, 3L)))
metadata <- list(r_version = R.version.string,
                 versions = sapply(c("euptf2", "ranger", "jsonlite"), function(x) as.character(packageVersion(x))),
                 quantile_algorithm = "ranger stored random.node.values; stats::quantile type 7",
                 predict_ranger_sha256_source = "installed predict.ranger deparse recorded separately",
                 probabilities = c(0.05, 0.5, 0.95),
                 missing_retained_obs_id = missing_result$OBS_ID,
                 audit = audit, cases = cases)
write_json(metadata, file.path(args[2], "reference.json"), auto_unbox = TRUE,
           pretty = TRUE, digits = NA)
writeLines(deparse(getS3method("predict", "ranger")), file.path(args[2], "predict-ranger.txt"))
print(length(cases))
