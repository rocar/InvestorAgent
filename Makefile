# Makefile for InvestorAgent Docker Build
# Variables can be adjusted to suit your project or local registry settings.
IMAGE_NAME = investoragent
TAG        = latest
REGISTRY   = 192.168.1.223:5000

# Default target
all: build

# Build the Docker image
build:
	docker buildx build --platform linux/amd64,linux/arm64 -t ${REGISTRY}/$(IMAGE_NAME):$(TAG) --push . --output=type=registry,registry.insecure=true

# Tag the image for your local registry
tag:
	docker tag $(IMAGE_NAME):$(TAG) $(REGISTRY)/$(IMAGE_NAME):$(TAG)

# Push the tagged image to your registry
push: tag
	docker push $(REGISTRY)/$(IMAGE_NAME):$(TAG)

# Pull the image from your registry
pull:
	docker pull $(REGISTRY)/$(IMAGE_NAME):$(TAG)

# Run the container mapping port 8000 to host port 8000
run:
	docker run -d -p 8000:8000 ${REGISTRY}/$(IMAGE_NAME):$(TAG)

# Run python locally
local:
	uvicorn investor_agent.api:app --host 0.0.0.0 --port 8000 --reload

# Follow logs of the most recent container
logs:
	docker logs -f $$(docker ps -lq)

# Clean up all stopped containers (use with caution)
clean:
	docker rm $$(docker ps -a -q)