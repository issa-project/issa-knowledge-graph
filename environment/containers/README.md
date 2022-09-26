# Docker containers

Almost all of the tools used in the ISSA pipeline are executed within a Docker container context. That provides greater portability and maintainability of the execution environment.

### Configuration

Variable aspects of Docker containers such as directories, languages, etc. are configured in [env.sh](../../env.sh) file.

### Execution

Each container folder typically contains: 
- Docker image installation or build script `install-<contianer>.sh`
- Docker container run script `run-<contianer>.sh`

All of the containers, except for `virtuoso`, are started and stopped as they are needed. The `virtuoso` container should be constantly running to provide access to the generated Knowledge Graph. 

>:point_right:  The `dbpedia-spotlight.en` container requires a lot of memory and fails to execute on a 32Gb RAM machine if any other container besides `virtuoso` is running.

### Data persistence
Each Docker container is provided with a persistent storage directory on the host machine through the mapped volumes mechanism. These volumes can store models, configurations and database files. The volumes are created in the `/volumes` directory in the host FS.

If a Docker container has to access pipeline-generated files or pipeline scripts their locations are mapped to the `issa/data` and `issa/scripts` directories in the containers's FS.

## Containers

### annif
The `annif` container provides automated indexing of documents' text in the pipeline. For training the statistical models provided by Annif software we create a separate `annif-training` container (see [training](../../training) ) for more details. But both containers share the same project directory on the host FS.

We deploy [Annif Docker Image](https://github.com/NatLibFi/Annif/wiki/Usage-with-Docker) and configure the models that we would like to train and use on the document corpus. The [project config file](annif/projects.cfg) should be adapted for each use case.

- to install the image run [install-annif.sh](annif/install-annif.sh) script.

- to run the container invoke [run-annif.sh](annif/run-annif.sh) script. 

- to test the installation and configuration run 
  - ```docker exec annif annif list-projects```
 
 >:point_right: The [training](../../training) process has to be run at least once before the automated indexing is feasible. 

### agrovoc-pyclinrec
The `agrovoc-pyclinrec` container runs the text annotation service to annotate text in English or French with concepts from the [Agrovoc Multilingual Thesaurus](https://agrovoc.fao.org).

We build a Docker image to create the execution environment for the [Python Concept Recognition Library](https://github.com/twktheainur/pyclinrec) and to create a web application similar to other annotation Dockers, e.g. `dbpedia-spotlight` and `entity-fishing`. NOTE: we forked the library for consistensy reasons). 

By default this container is created specifically for Agrovoc vocabulary but it can be reconfigured for another SKOS thesaurus by providing its SPARQL endpoint in `DICT_ENDPOINT` environment variable. If graph name filtering is required than a graph name can be passed in 'DICT_GRAPH' variable of the `docker run` command.

>:point_right: Concept recognition is currently available only for English and French.

- to build the image and initialise pyclinrec container invoke [install-pyclinrec.sh](agrovoc-pyclinrec/install-pyclinrec.sh) script.

- to run the container invoke [run-pyclinrec.sh](agrovoc-pyclinrec/run-pyclinrec.sh) script. 

- to get help call ```http://localhost:5000/```

- to test annotation call 

  - ```curl -X POST http://localhost:5000/annotate --data-urlencode "text=Growing bananas in Ireland" --data-urlencode "lang=en" --data-urlencode "conf=0.15" -H "Accept: application/json"``` 
  - ```curl -X POST http://localhost:5000/annotate --data-urlencode "text=Cultiver des bananes en Irlande" --data-urlencode "lang=fr" --data-urlencode "conf=0.15" -H "Accept: application/json"```

>:point_right: The internal vocabulary and concept indexing is taking place during the installation and it may take a long time. On our machinne the initialization takes about 10 minutes. 

### dbpedia-spotlight
Two dbpeadia-spotlight containers are created from the [DBpedia Spotlight Docker image](https://hub.docker.com/r/dbpedia/dbpedia-spotlight) one per language `dbpedia-spotlight.en` and `dbpedia-spotlight.fr`. Each container relies on the downloaded language model. The model download is lengthy (on our machine 11 and 4 min for English and French) and is included in the installation script. The models are stored in the host FS.

- to install the image and download language models run [install-spotlight.sh](dbpedia-spotlight/install-spotlight.sh) script.

- to run the containers invoke [run-spotlight.sh](dbpedia-spotlight/run-spotlight.sh) script. 

- to test annotation call 

  - ```curl -X POST http://localhost:2222/rest/annotate --data-urlencode "text=Growing bananas in Ireland" --data-urlencode "lang=en" --data-urlencode "confidence=0.15" -H "Accept: application/json"``` 
  - ```curl -X POST http://localhost:2223/rest/annotate --data-urlencode "text=Cultiver des bananes en Irlande" --data-urlencode "lang=fr" --data-urlencode "confidence=0.15" -H "Accept: application/json"```

>:point_right:  The `dbpedia-spotlight.en` container requires a lot of memory and fails to execute on a 32Gb RAM machine if any other container besides `virtuoso` is running. It is also slow to launch and cannot be accessed immediately. We allocate a 2 min delay after the container start command.
 
>:point_right: To update the models it is sufficient to delete the model folder and re-run the container installation script.


### entity-fishing
We adapted Grobid's [Dockerfile](https://github.com/kermitt2/grobid/blob/master/Dockerfile.crf) to build a Docker image for [entity-fishing](https://nerd.readthedocs.io/en/latest/) entity recognition and disambiguation service.  Entity-fisihing also requires the models to be downloaded during the installation.

- to build the image and download language models run [install-entity-fishing.sh](entity-fishing/install-entity-fishing.sh) script.

- to run the containers invoke [run-entity-fishing.sh](entity-fishing/run-entity-fishing.sh) script. 

- to test annotation call 

  - ```curl -X POST http://localhost:8090/service/disambiguate -X POST -F "query={ 'text':'Growing bananas in Ireland', 'language': {'lang':'en'}}" -H "Accept: application/json"``` 
  - ```curl -X POST http://localhost:8090/service/disambiguate -X POST -F "query={ 'text':'Cultiver des bananes en Irlande', 'language': {'lang':'fr'}}" -H "Accept: application/json"``` 

>:point_right: To update the models run [install-models.sh](entity-fishing/install-models.sh) script. 

### grobid
The `grobid` container provides text extraction from the PDF documents of the corpus articles. 

We deploy the [CRF-only image](https://grobid.readthedocs.io/en/latest/Grobid-docker/) since our host machine does not have a GPU for CRF and Deep Learning image. No additional configuration is required.

- to install the image run [install-grobid.sh](grobid/install-grobid.sh) script.

- to run the containers invoke [run-grobid.sh](grobid/run-grobid.sh) script. 

- to test run command `curl http://localhost:8070/api/version`

### mongodb
The `mongodb` container provides intermediate storage for gathered data to enable easy use of [XR2RML tool](https://www.i3s.unice.fr/~fmichel/xr2rml_specification_v5.html) which is required an input database of JSON documents to create the customized mappings to the RDF dataset.

We deploy the official [MongoDb Docker Image](https://hub.docker.com/_/mongo) and configure the container to be integrated into the pipeline by mapping the volumes to the pipeline's scripts and data directories.

- to install the image run [install-mongodb.sh](mongodb/install-mongodb.sh) script.

- to run the container invoke [run-mongodb.sh](mongodb/install-mongodb.sh) script. 

- to run the interactive shell for MongoDB `docker exec -it  mongodb mongo`

### virtuoso
The `virtuoso` container provides storage for pipeline-generated Knowledge Graph and access to it via the SPARQL endpoint.

We deploy [OpenLink Virtuoso Enterprise Edition 7.2 Docker Image](https://hub.docker.com/r/openlink/virtuoso-closedsource-8) and configure it to be integrated into the pipeline. 

Before running the container for the first time it is necessary to create a dba password and store it in the $VIRTUOSO-PWD env variable. (We choose to set the variable in the user's `.bashrc` file. If you do the same remember to restart the user's session.)

- to install the image and configure Virtuoso run [install-virtuoso.sh](vistuoso/install-virtuoso.sh) script.

- to run the container invoke [run-virtuoso.sh](vistuoso/install-virtuoso.sh) script. 

- to access the SPARQL endpoint send HTTP request to `http://<host_name>:8890/sparql`.

>:point_right: This container should not be stopped except for maintenance reasons.




