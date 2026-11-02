# Compare original R states directly, without conversion or native inference.
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args)==4L, !file.exists(args[4]))
.libPaths(c(args[2],.libPaths()))
library(euptf2)
library(jsonlite)
collection <- read_json(file.path(args[3],"collection.json"))
archive <- read_json(file.path(args[3],"scientific-archive.json"))
lookup <- list()
for (model in collection$models) {
    if (identical(model$source_kind,"scientific-archive")) next
    for (i in seq_along(model$components)) lookup[[model$components[[i]]$original]] <- list(model=model,index=i)
}
normalize <- function(name) sub("^KS_","log10KS_",sub("^FC2_","FC_2_",sub("^AWC2_","AWC_2_",name)))
report <- lapply(archive$files,function(source) {
    e<-new.env(); loaded<-load(file.path(args[1],source$path),envir=e)
    stopifnot(length(loaded)==1L)
    original <- e[[loaded]]
    stopifnot(inherits(original,"ranger"),inherits(original$forest,"ranger.forest"))
    key<-normalize(sub("[.]rdata$","",basename(source$path)))
    package<-lookup[[key]]
    fields<-c("child.nodeIDs","split.varIDs","split.values","is.ordered","independent.variable.names","dependent.varID","num.trees","treetype")
    if (!is.null(package)) {
        data(list=package$model$original,package="euptf2",envir=e)
        counterpart<-e[[package$model$original]]
        if (!inherits(counterpart,"ranger")) counterpart<-counterpart[[package$index]]
        equal<-vapply(fields,function(field)identical(original$forest[[field]],counterpart$forest[[field]]),logical(1))
        samples_equal<-identical(original$random.node.values,counterpart$random.node.values)
        stopifnot(all(equal),samples_equal)
        list(path=source$path,original=loaded,package_model=package$model$name,
             component=package$index,forest_fields_identical=as.list(equal),terminal_response_matrix_identical=samples_equal)
    } else {
        stopifnot(grepl("VG_EUHYDI/VG_.*_PTF26[.]rdata$",source$path))
        list(path=source$path,original=loaded,package_model=NULL,archive_only_model="VG_PTF26")
    }
})
write_json(list(revision=archive$revision,archived_forests=length(report),
               packaged_forests=sum(vapply(report,function(x)!is.null(x$package_model),logical(1))),
               archive_only_forests=sum(vapply(report,function(x)is.null(x$package_model),logical(1))),
               comparisons=report),args[4],auto_unbox=TRUE,pretty=TRUE,digits=NA)
