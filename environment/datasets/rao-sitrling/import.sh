#!/bin/bash
# Author: Anna BOBASHEVA, University Cote d'Azur, Inria
#
# Licensed under the Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
#
# Load OpenAlex topics labels and hierarchy into Virtuoso triplestore
#
# Parameters:
#   $1: file name of dump to import


# ISSA environment definitions
. ../../../env.sh

dump=$1


log_dir=${ISSA_ENV_LOG:-../../logs}
mkdir -p $log_dir 
log=$log_dir/import-rao-stirling-$(date "+%Y%m%d_%H%M%S").log

# Start container if needed
CONTAINER_NAME=${VIRTUOSO_CONT_NAME:-virtuoso}
docker start $CONTAINER_NAME

# Remove previously imported ttl files
rm -f -v $RAO_STIRLING_IMPORT_DIR/$dump        >>$log

cp -v $dump        $RAO_STIRLING_IMPORT_DIR    >>$log
cp -v import.isql  $RAO_STIRLING_IMPORT_DIR    >>$log

docker exec -w /database/import $CONTAINER_NAME \
            isql -H localhost -U dba -P $VIRTUOSO_PWD \
            exec="LOAD import.isql" -i $ISSA_NAMESPACE &>>$log
