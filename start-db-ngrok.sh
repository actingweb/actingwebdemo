#!/usr/bin/env bash
java -Djava.library.path=/Users/wedel/dynamodb/DynamoDBLocal_lib -jar /Users/wedel/dynamodb/DynamoDBLocal.jar -sharedDb  &
ngrok http -subdomain=greger 5000 > /dev/null 2>&1 &