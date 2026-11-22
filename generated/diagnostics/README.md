# Superseded atomic-quadrature diagnostic

The initial deferral solver treated conditional quantile nodes as probability
atoms. Its middle GDP grid cycled, and a smaller update weight did not resolve
the residual. These failed attempts are archived for transparency and are not
used in the paper. `replication/deferrals.py` now integrates cumulative weights
linearly across continuous probability cells. All nine final refinements
converge; the successful run is `generated/replication_continuous.log`, and the
final results and residuals are in `generated/results.json`.
