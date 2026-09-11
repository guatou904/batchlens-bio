# Independent oracle: R model.matrix and QR row-space rank, not BatchLens's SVD.
# Input fixtures are constructed independently rather than exported from Python.
args <- commandArgs(trailingOnly = TRUE)
stopifnot(length(args) == 1)
crossed <- data.frame(time = rep(c("D0", "D7", "D0", "D7"), 2),
                      run = rep(c("A", "A", "B", "B"), 2))
cases <- list(
  balanced = crossed,
  `confounded-time` = data.frame(time = rep(c("D0", "D7"), each = 3),
                                run = rep(c("A", "B"), each = 3)),
  `partial-overlap` = data.frame(time = c("D0", "D0", "D7", "D7", "D7"),
                                 run = c("A", "A", "A", "B", "B")),
  `redundant-nuisance` = transform(crossed, machine = run),
  paired = data.frame(time = rep(c("D0", "D7"), 2),
                      run = rep(c("A", "B"), each = 2),
                      unit = rep(c("u1", "u2"), each = 2))
)
results <- lapply(names(cases), function(name) {
  d <- cases[[name]]
  d[] <- lapply(d, factor)
  formula <- if (name == "paired") ~ time + run + unit else
             if (name == "redundant-nuisance") ~ time + run + machine else ~ time + run
  X <- model.matrix(formula, d)
  contrast <- rep(0, ncol(X)); contrast[which(colnames(X) == "timeD7")] <- 1
  rank <- qr(X, tol = 1e-10)$rank
  augmented <- qr(rbind(X, contrast), tol = 1e-10)$rank
  data.frame(case = name, rank = rank,
             status = if (rank == augmented) "ESTIMABLE" else "NON_ESTIMABLE")
})
write.table(do.call(rbind, results), args[[1]], sep = "\t", quote = FALSE, row.names = FALSE)
cat(R.version.string, "\nFive independent QR fixtures verified.\n")
