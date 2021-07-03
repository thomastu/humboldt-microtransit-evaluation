import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from lxml import etree
from pyrosm import OSM

from prefect import task, Flow, Parameter
from typing import Tuple


mph_to_mps = 0.44704


@task
def parse_physsim_network(physsim_fp):
    """Parse a MATSIM network file to a pandas dataframe with model params.

    Args:
        physsim_fp (str): Path to a reference physsim_network.xml file
    """
    with open(physsim_fp, "rb") as fh:
        network = etree.fromstring(fh.read())
    attributes = ["id", "capacity", "freespeed", "permlanes", "length"]

    # Only inspect links which have valid attributes!
    basePath = "//links/link[boolean(attributes/attribute[@name='type'])]"
    attributes_data = zip(
        *(network.xpath(f"{basePath}/@{attr}") for attr in attributes)
    )
    link_types = network.xpath(f"{basePath}/attributes/attribute[@name='type']/text()")

    # Poll for available mode choices (should be something like car,bike,walk)
    # And then create a dummy variable for each unique mode choice
    modes = set()
    mode_choices = pd.Series(network.xpath(f"{basePath}/@modes"))
    for choice_set in mode_choices.unique():
        for mode in choice_set.split(","):
            modes.add(mode)

    # Build a dataframe from the physsim xml file
    network = pd.DataFrame(attributes_data, columns=attributes)
    network = network.astype(float)
    network["modes"] = mode_choices
    for mode in modes:
        network[mode] = mode_choices.str.contains(mode)

    # Map link types to the OSM column name
    network["highway"] = link_types
    return network


@task(nout=2)
def parse_osm_network(osm_network_fp: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Parse an OSM network file and return nodes and links.

    Args:
        osm_network_fp (str): Path to an OSM pbf file.
    """
    osm = OSM(osm_network_fp)
    nodes, links = osm.get_network(nodes=True, network_type="all")
    links["maxspeed"] = links["maxspeed"] * mph_to_mps
    return nodes, links


@task
def calculate_network_capacity(links, reference_network):
    """Calculates network capacity for the given OSM based on 

    Args:
        osm_network_fp (str): Filepath to the network with a OSM pbf file
        reference_network (pd.DataFrame): The reference network from which to calculate network flow.
    """

    # Enforce immutability for input data
    # Need to reconstruct the dataframe due to GeoDataFrame wonkiness
    links = links[["id", "lanes", "highway", "u", "v"]].copy()
    reference_network = reference_network.copy()

    model_params = ["highway", "permlanes"]
    for param in model_params:
        assert param in reference_network.columns, f"Missing '{param}' column"

    model = smf.ols(f"capacity ~ highway", data=reference_network).fit()

    # Trim down on variables by removing non-significant variables and assigning a dummy value
    critical_params = model.pvalues[model.pvalues < 0.05].index
    critical_params = (
        critical_params[critical_params.str.startswith("highway")]
        .str.split(".")
        .str.get(-1)
        .str.rstrip("]")
        .tolist()
    )

    # Filter for params that are not significant significant categories and assign those to "MISC"
    train_highway_encoder = {
        k: "MISC"
        for k in reference_network["highway"][
            ~reference_network["highway"].isin(critical_params)
        ].unique()
    }

    highway_encoder = {
        k: "MISC"
        for k in links["highway"][~links["highway"].isin(critical_params)].unique()
    }
    reference_network["highway"] = reference_network["highway"].replace(
        train_highway_encoder
    )

    # Rerun the model
    model = smf.ols(
        f"capacity ~ highway + permlanes",
        data=reference_network[["capacity", "highway", "permlanes"]],
    ).fit()

    # Now hot-encode the OSM link data
    links["highway"] = links["highway"].replace(highway_encoder)
    links["permlanes"] = links["lanes"].fillna(1).astype(float)

    links["capacity"] = model.predict(sm.add_constant(links))
    return links


@task
def save_link_data(links, output_dir):
    links.to_csv(f"{output_dir}/links.csv", index=False)


with Flow("create_network_data") as flow:
    osm_network_fp = Parameter("osm_network_fp")
    physsim_fp = Parameter("physsim_fp")
    output_dir = Parameter("output_dir")

    reference_network = parse_physsim_network(physsim_fp)
    nodes, edges = parse_osm_network(osm_network_fp)
    links = calculate_network_capacity(edges, reference_network)
    save_link_data(links, output_dir)


if __name__ == "__main__":
    flow.register("hcme")

