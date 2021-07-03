# Overview

This repository exists to orchestrate and analyze results from the [BEAM model](https://github.com/LBNL-UCB-STI/beam) for the purposes of evaluating microtransit feasibility in Humboldt county.


## Quickstart

```
# Install deps
pdm install

# Register tasks: FIXME - configure or structure directory to look for new flows

# Register flows
pdm run python hcme/scripts/calculate_network_capacity.py

# Start a local prefect server
pdm run prefect server start

# Resolve port conflicts if needed, e.g. postgres:
# pdm run prefect server start --postgres-port 5433

# alternatively, run flows through the prefect cli
pdm run prefect run -p hcme/scripts/calculate_network_capacity.py \
    --param physsim_fp="/path/to/existing/physsim-network.xml" \
    --param osm_network_fp="/path/to/osm.pbf" \
    --param output_dir="./outputs"
```