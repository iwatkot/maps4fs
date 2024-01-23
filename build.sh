#!/bin/bash

echo "Starting building Docker image..."
docker build --platform linux/amd64 -t iwatkot/maps4fs .
echo "Docker image has been successfully built, exiting..."