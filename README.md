# A Graph-Based Approach to IoT Service Detection in Middleware (Capstone Code) #

## Getting Started ##
Run docker compose command to setup networks and build/run all docker images. 
```bash
docker build -t base_node -f Dockerfiles/client.Dockerfile .
docker-compose -f docker-compose.yaml up --build
```