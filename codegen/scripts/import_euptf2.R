# Offline conversion of the authenticated THS_PTF01 ranger object. No fitting.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 2L)
environment <- new.env(parent = emptyenv())
stopifnot(identical(load(args[1], envir = environment), "THS_PTF01"))
model <- environment$THS_PTF01
forest <- model$forest
stopifnot(inherits(model, "ranger"), inherits(forest, "ranger.forest"),
          identical(forest$treetype, "Regression"), model$num.trees == 200,
          identical(forest$independent.variable.names,
                    c("USSAND", "USSILT", "USCLAY", "DEPTH_M")),
          all(forest$is.ordered), is.matrix(model$random.node.values),
          ncol(model$random.node.values) == model$num.trees)
output <- file(args[2], open = "wb")
writeBin(charToRaw("PTFKQF01"), output)
write_u32 <- function(x) writeBin(as.integer(x), output, size = 4, endian = "little")
write_f64 <- function(x) writeBin(as.double(x), output, size = 8, endian = "little")
write_u32(c(1, model$num.trees))
for (tree in seq_len(model$num.trees)) {
    children <- forest$child.nodeIDs[[tree]]
    variables <- forest$split.varIDs[[tree]]
    values <- forest$split.values[[tree]]
    count <- length(values)
    stopifnot(length(children) == 2L, all(lengths(children) == count),
              length(variables) == count, count <= nrow(model$random.node.values),
              all(is.finite(values)))
    # Old ranger includes the response column in split variable IDs.
    if (!is.null(forest$dependent.varID)) {
        variables <- variables - (variables > forest$dependent.varID)
    }
    parents <- integer(count)
    write_u32(count)
    for (node in seq_len(count)) {
        left <- children[[1]][node]
        right <- children[[2]][node]
        leaf <- left == 0 && right == 0
        if (leaf) {
            sample <- model$random.node.values[node, tree]
            stopifnot(is.finite(sample))
            write_u32(c(0, 0, -1))
        } else {
            stopifnot(left >= node, right >= node, left < count, right < count,
                      left != right, variables[node] %in% 0:3)
            parents[c(left, right) + 1L] <- parents[c(left, right) + 1L] + 1L
            sample <- 0
            write_u32(c(left, right, variables[node]))
        }
        write_f64(c(values[node], sample))
    }
    stopifnot(parents[1] == 0L, all(parents[-1] == 1L))
}
close(output)
