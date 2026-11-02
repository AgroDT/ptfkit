# Independent references: original package functions, never converted artifacts.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 3L, !dir.exists(args[3]))
.libPaths(c(args[2], .libPaths()))
library(euptf2)
library(jsonlite)
stopifnot(as.character(packageVersion("euptf2")) == "1.0.0",
          as.character(packageVersion("ranger")) == "0.18.0")
dir.create(args[3], recursive = TRUE)
data(sample_data, package = "euptf2")
data(suggested_PTF, package = "euptf2")
write_json(suggested_PTF, file.path(args[3], "suggested.json"), pretty=TRUE, auto_unbox=TRUE)
files <- sort(list.files(file.path(args[1], "data"), pattern="_PTF[0-9]+[.]rdata$", full.names=TRUE))
inventory <- list()
for (path in files) {
    environment <- new.env()
    original <- load(path, envir=environment)
    stopifnot(length(original) == 1L)
    object <- environment[[original]]
    components <- if (inherits(object, "ranger")) list(object) else object
    name <- sub("^log10KS", "KS", original)
    family <- sub("_PTF[0-9]+$", "", name)
    ptf <- sub("^.*_(PTF[0-9]+)$", "\\1", name)
    features <- components[[1]]$forest$independent.variable.names
    stopifnot(all(vapply(components, function(m) identical(m$forest$independent.variable.names, features), logical(1))))
    audit <- lapply(components, function(m) {
        f <- m$forest
        leaves <- lapply(f$child.nodeIDs, function(x) which(x[[1]] == 0 & x[[2]] == 0))
        list(class=class(m), forest_class=class(f), treetype=f$treetype,
             features=f$independent.variable.names, ordered=f$is.ordered,
             dependent_var_id=f$dependent.varID, trees=m$num.trees,
             nodes=sum(lengths(f$split.values)), samples=m$num.samples,
             random_dim=dim(m$random.node.values),
             leaf_samples_present=!is.null(m$random.node.values) &&
                 all(vapply(seq_along(leaves), function(i) all(is.finite(m$random.node.values[leaves[[i]],i])), logical(1))))
    })
    inputs <- as.data.frame(sample_data)
    inputs <- inputs[complete.cases(inputs), ]
    stopifnot(nrow(inputs) == 10L)
    # Probe the first root of each independent parameter forest, inclusive
    # boundary and both sides. Other predictors stay at an original sample.
    for (component in components) {
        f <- component$forest
        variable <- f$split.varIDs[[1]][1]
        if (!is.null(f$dependent.varID)) variable <- variable - (variable > f$dependent.varID)
        feature <- f$independent.variable.names[variable+1L]
        threshold <- f$split.values[[1]][1]
        for (delta in c(-1e-10, 0, 1e-10)) {
            row <- inputs[1, ]
            row[[feature]] <- threshold + delta
            inputs <- rbind(inputs, row)
        }
    }
    for (texture in list(c(100,0,0), c(0,0,100), c(0,100,0))) {
        row <- inputs[1, ]
        row[, c("USSAND","USSILT","USCLAY")] <- texture
        inputs <- rbind(inputs, row)
    }
    mean <- suppressWarnings(euptfFun(ptf, inputs, target=family, query="predictions"))
    quantiles <- suppressWarnings(euptfFun(ptf, inputs, target=family, query="quantiles"))
    custom <- suppressWarnings(euptfFun(ptf, inputs[1:2, ], target=family, query="quantiles", quantiles=c(.1,.9)))
    count <- length(components)
    mean_count <- count + as.integer(family %in% c("VG","MVG"))
    cases <- lapply(seq_len(nrow(inputs)), function(i) {
        q <- if (count == 1L) as.numeric(quantiles[i,1:5]) else
            unlist(lapply(quantiles, function(q) as.numeric(q[i,-1])))
        list(inputs=sprintf("%.17g",as.numeric(inputs[i,features])), mean=as.numeric(mean[i,seq_len(mean_count)]),
             quantiles=q)
    })
    custom_cases <- lapply(1:2, function(i) {
        q <- if (count == 1L) as.numeric(custom[i,1:2]) else
            unlist(lapply(custom, function(q) as.numeric(q[i,-1])))
        list(inputs=sprintf("%.17g",as.numeric(inputs[i,features])), quantiles=q)
    })
    record <- list(name=name, original=original, file=basename(path), class=class(object),
                   family=family, features=features, component_names=names(components), components=audit)
    inventory[[length(inventory)+1L]] <- record
    reference <- list(name=name, oracle="euptf2::euptfFun", r_version=R.version.string,
        euptf2=as.character(packageVersion("euptf2")), ranger=as.character(packageVersion("ranger")),
        features=features, probabilities=c(.05,.25,.5,.75,.95), cases=cases,
        custom_probabilities=c(.1,.9), custom_cases=custom_cases)
    write_json(reference, file.path(args[3], paste0(name,".json")), auto_unbox=TRUE, pretty=TRUE, digits=NA)
    cat(name, length(cases), "cases\n")
    rm(environment, object, components)
    gc(FALSE)
}
write_json(inventory, file.path(args[3], "inventory.json"), auto_unbox=TRUE, pretty=TRUE, digits=NA)
