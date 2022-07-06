#!/bin/bash

for i in `cat /environment`; do
    export $i
    done

    neo4j console
