#!/bin/bash

ACTION=$1

if [ "$ACTION" == "--on" ]; then
    echo "Starting the container using Docker Compose..."
    docker-compose up -d
elif [ "$ACTION" == "--off" ]; then
    echo "Stopping the container using Docker Compose..."
    docker-compose down
else
    echo "Invalid flag. Use --on to start or --off to stop."
fi
