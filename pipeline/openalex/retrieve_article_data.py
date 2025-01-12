# -*- coding: utf-8 -*-
""" 
Retrieve from OpenAlex 3 types of metadata about the documents with a DOI: authorships, SDGs and topics.
from dedicated SPARQL micro-services.

This script is invoked with the following command line arguments:
    - the path to the configuration file containing the class cfg_openalex_data
    - `--datatype`: the type of data to fetch from OpenAlex, one of 'authorships', 'sdgs', 'topics'

@author: Quentin Scordo, Franck Michel
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import requests
import time
from tqdm import tqdm
from traceback import format_exc
from urllib.parse import quote, urlencode
import sys

sys.path.append("..")
from util import add_path_to_config
from util import open_timestamp_logger, close_timestamp_logger
from util import INFO, DEBUG
from openalex.common import fetch_document_list

add_path_to_config()
from config import cfg_openalex_data as cfg

# %% Set up logging
logger = open_timestamp_logger(
    log_prefix=os.path.splitext(os.path.basename(__file__))[0],
    log_dir=cfg.LOG_PATH,
    file_level=DEBUG if cfg.DEBUG else INFO,
)


def fetch_data(data_type, document_uri, doi) -> str:
    """
    Fetch data from one of the SPARQL microservices,
    for a given DOI and document URI

    Args:
        data_type (str): one of 'authorship', 'sdg', 'topics'
        document_uri (str): document URI (in ISSA, not in OpenAlex)
        doi (str): document DOI

    Returns:
       str: RDF data in Turtle format
    """
    try:
        encoded_document_uri = quote(document_uri, safe="")
        encoded_doi = quote(doi, safe="")
        sparql_query = cfg.SPARQL_PREFIXES + " CONSTRUCT WHERE { ?s ?p ?o. }"
        encoded_sparql_query = urlencode({"query": sparql_query})
        url = f"{cfg.SERVICES[data_type]}?documentUri={encoded_document_uri}&documentDoi={encoded_doi}&{encoded_sparql_query}"

        logger.debug(f"Fetching {data_type} data for {document_uri}, DOI {doi}")
        response = requests.get(url, headers={"Accept": "text/turtle"})
        response.raise_for_status()
        return response.text

    except requests.exceptions.HTTPError as e:
        logger.error(
            f"Could not retrieve {data_type} for document {document_uri}, DOI {doi}: {e.response.text}"
        )
        return None
    except requests.exceptions.RequestException as e:
        logger.error(
            f"Could not retrieve {data_type} for document {document_uri}, DOI {doi}: {e}"
        )
        return None


# %% Main processing loop
if __name__ == "__main__":

    # Parse the inline parameters
    parser = argparse.ArgumentParser(
        description="Retrieve from OpenAlex 3 types of metadata about the documents: authorships, SDGs and topics"
    )
    parser.add_argument(
        "config_file",
        help="path to the configuration file contaning class cfg_openalex_data",
    )
    parser.add_argument(
        "--datatype",
        dest="data_type",
        help="type of data to fetch from OpenAlex, one of 'authorships', 'sdgs', 'topics'",
        choices=["authorships", "sdgs", "topics"],
    )
    args = parser.parse_args()

    # Initialize lists and counters
    rdf_results = []
    error_count = 0

    # Fetch list of document URIs and DOIs
    document_list = fetch_document_list()
    logger.info(f"No. documents with a DOI: {len(document_list)}")

    if cfg.OPENALEX_API["use_mailto"]:
        # Parallel execution with ThreadPoolExecutor
        logger.info(f"Running with {cfg.OPENALEX_API['max_workers']} workers")
        with ThreadPoolExecutor(
            max_workers=cfg.OPENALEX_API["max_workers"]
        ) as executor:
            future_to_doi = {
                executor.submit(
                    fetch_data,
                    args.data_type,
                    cfg.DOCUMENT_URI_TEMPLATE % item["paper_id"],
                    item["doi"],
                ): (cfg.DOCUMENT_URI_TEMPLATE % item["paper_id"], item["doi"])
                for item in document_list
            }
            for future in tqdm(as_completed(future_to_doi), total=len(document_list)):
                document_uri, doi = future_to_doi[future]
                try:
                    rdf_data = future.result()
                    if rdf_data:
                        rdf_results.append(rdf_data)
                        logger.debug(
                            f"Recorded {args.data_type} data for {document_uri}, DOI {doi}"
                        )
                    else:
                        error_count += 1
                        time.sleep(cfg.OPENALEX_API["pause_error"])
                except Exception as exc:
                    logger.error(
                        f"Exception while processing document {document_uri}, DOI {doi}: {exc}"
                    )
                    error_count += 1
                    time.sleep(cfg.OPENALEX_API["pause_error"])
    else:
        # Sequential execution
        logger.info("Running in sequential execution mode")
        for item in tqdm(document_list):
            doi, paper_id = item["doi"], item["paper_id"]
            document_uri = cfg.DOCUMENT_URI_TEMPLATE % paper_id
            try:
                rdf_data = fetch_data(args.data_type, document_uri, doi)
                if rdf_data:
                    rdf_results.append(rdf_data)
                    logger.debug(
                        f"Recorded {args.data_type} data for {document_uri}, DOI {doi}"
                    )
                    time.sleep(cfg.OPENALEX_API["pause_sequential"])
                else:
                    error_count += 1
                    time.sleep(cfg.OPENALEX_API["pause_error"])
            except Exception as exc:
                logger.error(f"Exception while processing DOI {doi} : {exc}")
                logger.error(format_exc())
                error_count += 1
                time.sleep(cfg.OPENALEX_API["pause_error"])

    # Save RDF results to a Turtle file
    output = cfg.OUTPUT_FILES[args.data_type]
    with open(output, "w", encoding="utf-8") as rdf_file:
        rdf_file.write(cfg.SPARQL_PREFIXES)
        for rdf_data in rdf_results:
            for line in rdf_data.splitlines():
                if not line.startswith("@prefix"):
                    rdf_file.write(line + "\n")

    # Summary logging
    logger.info(f"{args.data_type} data saved in {output}")
    logger.info(f"Number of successful records: {len(rdf_results)}")
    logger.info(f"Number of errors: {error_count}")

close_timestamp_logger(logger)
