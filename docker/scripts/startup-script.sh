#!/usr/bin/env bash

while true; do sleep 1; done

# IMAGE_PATH="${GCP_DOCKER_IMAGE_NAME}:${GCP_DOCKER_IMAGE_TAG}"

# echo "Waiting for the Docker image to be available in GCP Artifact Registry: $GCP_DOCKER_IMAGE_NAME"
# while ! gcloud artifacts docker images list "asia-northeast3-docker.pkg.dev/${GCP_PROJECT_ID}/${GCP_REPO_NAME}" \
#     --filter="IMAGE='$ONLY_DOCKER_IMAGE_NAME' AND TAGS='$GCP_DOCKER_IMAGE_TAG'" --format="get(IMAGE)" | grep -q "$GCP_DOCKER_IMAGE_NAME"; do
#     echo "Image not found, checking again in 10 seconds..."
#     sleep 10
# done

# echo "Docker image found in Artifact Registry: $IMAGE_PATH"

# echo "Pulling Docker image: $IMAGE_PATH"
# docker pull $IMAGE_PATH


# if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
#     echo "Container $CONTAINER_NAME is already running. No new container will be started."
# else
#     echo "Running new container: $CONTAINER_NAME"
#     docker run -d --name $CONTAINER_NAME $IMAGE_PATH
#     echo "Container $CONTAINER_NAME is up and running."
# fi

# Run extra commands
exec "$@"