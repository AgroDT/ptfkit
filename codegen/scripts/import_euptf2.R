# Offline export of authenticated ranger state. No fitting or random sampling.
args <- commandArgs(trailingOnly = TRUE)
write_u32 <- function(x, output) writeBin(as.integer(x), output, size=4, endian="little")
write_forest <- function(model, features, output) {
    forest <- model$forest
    stopifnot(inherits(model,"ranger"), inherits(forest,"ranger.forest"),
              identical(forest$treetype,"Regression"), model$num.trees == 200,
              identical(forest$independent.variable.names,features), all(forest$is.ordered),
              is.matrix(model$random.node.values), ncol(model$random.node.values) == model$num.trees)
    write_u32(model$num.trees, output)
    for (tree in seq_len(model$num.trees)) {
        children <- forest$child.nodeIDs[[tree]]
        variables <- forest$split.varIDs[[tree]]
        values <- forest$split.values[[tree]]
        count <- length(values)
        stopifnot(length(children)==2L, all(lengths(children)==count),
                  length(variables)==count, count<=nrow(model$random.node.values), all(is.finite(values)))
        if (!is.null(forest$dependent.varID)) variables <- variables - (variables > forest$dependent.varID)
        left <- children[[1]]
        right <- children[[2]]
        leaf <- left==0 & right==0
        internal <- !leaf
        stopifnot(all(left[internal] > (seq_len(count)-1L)[internal]),
                  all(right[internal] > (seq_len(count)-1L)[internal]),
                  all(left[internal]<count), all(right[internal]<count),
                  all(left[internal]!=right[internal]), all(variables[internal] %in% seq.int(0,length(features)-1L)))
        parents <- tabulate(c(left[internal],right[internal])+1L, nbins=count)
        stopifnot(parents[1]==0L, all(parents[-1]==1L))
        sample <- numeric(count)
        sample[leaf] <- model$random.node.values[which(leaf),tree]
        stopifnot(all(is.finite(sample)))
        variables[leaf] <- -1L
        integers <- writeBin(as.integer(rbind(left,right,variables)), raw(), size=4, endian="little")
        numbers <- writeBin(as.double(rbind(values,sample)), raw(), size=8, endian="little")
        write_u32(count, output)
        writeBin(as.vector(rbind(matrix(integers,nrow=12),matrix(numbers,nrow=16))),output)
    }
}
if (length(args)==2L) {
    environment <- new.env(parent=emptyenv())
    stopifnot(identical(load(args[1],envir=environment),"THS_PTF01"))
    output <- file(args[2],open="wb")
    writeBin(charToRaw("PTFKQF01"),output)
    write_u32(1,output)
    write_forest(environment$THS_PTF01,c("USSAND","USSILT","USCLAY","DEPTH_M"),output)
    close(output)
} else {
    stopifnot(length(args)==4L, args[1]=="collection", dir.exists(args[4]))
    plan <- read.csv(args[3],stringsAsFactors=FALSE)
    for (row in seq_len(nrow(plan))) {
        entry <- plan[row,]
        environment <- new.env(parent=emptyenv())
        stopifnot(identical(load(file.path(args[2],"data",entry$file),envir=environment),entry$original))
        object <- environment[[entry$original]]
        components <- if (inherits(object,"ranger")) list(object) else object
        features <- strsplit(entry$features,";",fixed=TRUE)[[1]]
        transforms <- as.integer(strsplit(entry$transforms,";",fixed=TRUE)[[1]])
        stopifnot(length(components)==length(transforms))
        output <- file(file.path(args[4],paste0(entry$name,".ptfq")),open="wb")
        writeBin(charToRaw("PTFKQF02"),output)
        write_u32(c(entry$id,length(features),length(components)),output)
        for (component in seq_along(components)) {
            write_u32(transforms[component],output)
            write_forest(components[[component]],features,output)
        }
        close(output)
        cat(entry$name,"converted\n")
    }
}
