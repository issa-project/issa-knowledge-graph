#!/bin/bash
# Authors: Anna BOBASHEVA, University Cote d'Azur, Inria
#
# Licensed under the Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
# Query all unique URIs from the annotations generated by entity-fishing

# Environment definitions
. ../../../env.sh

VIRTUOSO_PORT=${VIRTUOSO_HOST_HTTP_PORT:-8890}
ISSA_NS=${ISSA_NAMESPACE:-http://data-issa.cirad.fr/}

NES_GRAPH=${ISSA_NS}graph/entity-fishing-nes
WD_GRAPH=${ISSA_NS}graph/wikidata-named-entities

# Set the number of URIs to retrieve
query=$(cat << EOF
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT (count(distinct ?uri) as ?cnt)
FROM <${NES_GRAPH}>
FROM <${WD_GRAPH}>
WHERE { ?annot oa:hasBody ?uri. 
        FILTER NOT EXISTS {GRAPH <${WD_GRAPH}> {?uri rdfs:label ?wdLabel .}}}
EOF
)


size=$(curl -H "accept: text/csv" \
            --data-urlencode "query=${query}" \
     	    http://localhost:$VIRTUOSO_PORT/sparql \
			| grep -o -E '[0-9]+' )



# Max number of URIs to retrieve at once (limit of the SPARQL endpoint)
limit=10000

query=$(cat << EOF
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX oa: <http://www.w3.org/ns/oa#>
SELECT DISTINCT ?uri
FROM <${NES_GRAPH}>
FROM <${WD_GRAPH}>
WHERE { ?annot oa:hasBody ?uri. 
        FILTER NOT EXISTS {GRAPH <${WD_GRAPH}> {?uri rdfs:label ?wdLabel .}}}
LIMIT ${limit}
OFFSET 

EOF
)
 
result=wikidata-ne-uris.txt

resulttmp=/tmp/sparql-response-$$.ttl
echo -n "" > $resulttmp

offset=0

while [ "$offset" -lt "$size" ]
do
    echo "Retrieving URIs starting at $offset..."

    echo "${query}${offset}"

    curl -H "accept: text/csv" \
		--data-urlencode "query=${query}${offset}" \
     	http://localhost:$VIRTUOSO_PORT/sparql \
        | grep -v '"uri"' | sed 's|"||g' >> $resulttmp
     offset=$(($offset + $limit))
     
done

cat $resulttmp | sort | uniq > $result
rm $resulttmp

