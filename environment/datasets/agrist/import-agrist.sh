#!/bin/bash
# Author: Anna BOBASHEVA, University Cote d'Azur, Inria
#
# Licensed under the Apache License, Version 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
# Cretae the AgrIST thesaurus for describing the documents' domains. Done once unless something is updated.

# ISSA environment definitions
. ../../../env.sh

log_dir=$ISSA_ENV_LOG
mkdir -p $log_dir 
log=$log_dir/import_agrist_$(date "+%Y%m%d_%H%M%S").log

echo "Importing AgrIST thesaurus.."

CONTAINER_NAME=${VIRTUOSO_CONT_NAME:-virtuoso}
docker start $CONTAINER_NAME

echo "Loading AgrIST..."                                   >>$log

rm -v "$AGRIST_IMPORT_DIR"/*AgrIST*                         >>$log

cp -v AgrIST-Thema*.ttl "$AGRIST_IMPORT_DIR"
cp -v import-agrist.isql "$AGRIST_IMPORT_DIR"               >>$log

docker exec $CONTAINER_NAME \
            isql -H localhost -U dba -P $VIRTUOSO_PWD \
            exec="LOAD /database/import/import-agrist.isql"   &>>$log

echo "done."          




