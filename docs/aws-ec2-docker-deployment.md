# AWS EC2 Docker Deployment – AI Document Assistant

**Project:** AI Document Assistant  
**Cloud Provider:** Amazon Web Services (AWS)  
**Region:** Asia Pacific (Sydney) – `ap-southeast-2`  
**Container Platform:** Docker  
**Application Framework:** FastAPI  
**Operating System:** Ubuntu (EC2)

## 1. Overview

This document describes the deployment of the AI Document Assistant application on an AWS EC2 Ubuntu server using Docker.

The objective was to install Docker, clone the GitHub repository, configure environment variables, build a Docker image, create persistent storage, and run the FastAPI application inside a Docker container.

## 2. Connect to EC2 Using SSH

Connected to the EC2 instance from a local Linux laptop using SSH key-based authentication.

Command:

```bash
ssh -i /path/to/private-key.pem ubuntu@EC2_PUBLIC_IP
```

Private key permissions:

```bash
chmod 400 /path/to/private-key.pem
```

**Learning:** SSH provides secure remote access to the Ubuntu EC2 server using public-key authentication.

## 3. Docker Installation and Verification

Installed Docker Engine on the Ubuntu EC2 instance.

Verified the installation:

```bash
docker --version
docker compose version
```

Tested Docker:

```bash
sudo docker run hello-world
```

Configured Docker access for the Ubuntu user:

```bash
sudo usermod -aG docker $USER
newgrp docker
```

Verified Docker without sudo:

```bash
docker run hello-world
```

## 4. Clone the GitHub Repository

Cloned the existing AI Document Assistant project from GitHub.

```bash
git clone https://github.com/Athiranidev/ai-document-assistant.git
```

Entered the project directory:

```bash
cd ai-document-assistant
```

Verified the project files:

```bash
ls -la
```

The repository contained the application source code and Docker configuration files.

## 5. Docker Configuration

Used the existing Dockerfile to define the application image.

Important Docker configuration files:

| File | Purpose |
|---|---|
| Dockerfile | Defines the application image |
| .dockerignore | Excludes unnecessary files from the build context |
| .gitignore | Prevents sensitive and unnecessary files from being committed |
| requirements-docker.txt | Contains Docker application dependencies |
| constraints-docker.txt | Defines dependency constraints |

The Dockerfile configures the application to run using Uvicorn.

Application startup command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The container listens on port 8000.

## 6. Environment Variables and API Configuration

Created an environment configuration file on EC2.

The configuration included:

```env
GEMINI_API_KEY=<YOUR_GEMINI_API_KEY>
GEMINI_MODEL=gemini-3.5-flash-lite
```

Secured the environment file:

```bash
chmod 600 .env
```

**Security practices:**

- Keep API keys inside environment variables.
- Never commit `.env` to GitHub.
- Never expose private SSH keys.
- Ensure `.env` is included in `.gitignore` and `.dockerignore`.

## 7. Build the Docker Image

Built the Docker image from the project directory.

```bash
docker build -t ai-document-assistant:latest .
```

Verified the image:

```bash
docker images
```

Image name:

`ai-document-assistant:latest`

**Learning:** A Docker image is a packaged application template used to create Docker containers.

Building the image locally or on EC2 does not automatically upload it to GitHub. Container images can be published separately to Docker Hub or Amazon ECR.

## 8. Docker Persistent Storage

Created a named Docker volume to preserve application data.

```bash
docker volume create ai-document-assistant-data
```

Verified:

```bash
docker volume ls
```

The volume was mounted at:

```text
/app/storage
```

**Learning:** Docker named volumes provide persistent storage outside the container's writable layer.

The application uses ChromaDB for persistent vector storage.

## 9. Run the Docker Container

Started the application container in detached mode.

```bash
docker run -d \
  --name ai-document-assistant \
  -p 127.0.0.1:8000:8000 \
  --env-file .env \
  -v ai-document-assistant-data:/app/storage \
  ai-document-assistant:latest
```

Verified the running container:

```bash
docker ps
```

Observed port mapping:

```text
127.0.0.1:8000 -> 8000/tcp
```

Container name:

`ai-document-assistant`

**Learning:** Detached mode (`-d`) allows the container to run in the background.

Port mapping connects the EC2 host's localhost port 8000 to the container's port 8000.

## 10. Application Startup Verification

Checked application logs:

```bash
docker logs --tail 40 ai-document-assistant
```

Successful startup messages included:

```text
Gemini client initialized.
ChromaDB persistent client initialized.
Embedding model loaded successfully.
Application startup complete.
Uvicorn running on http://0.0.0.0:8000
```

This confirmed successful initialization of the main application components.

A Hugging Face unauthenticated-request warning appeared during model loading but did not prevent startup.

## 11. Application Testing

The application exposed the following FastAPI endpoints:

| Endpoint | Purpose |
|---|---|
| `/` | Application welcome endpoint |
| `/health` | Application health check |
| `/docs` | Swagger API documentation |
| `/documents/upload` | Document upload |
| `/documents/search` | Document search |
| `/documents/ask` | AI-powered document question answering |

Verified the health endpoint:

```bash
curl http://localhost:8000/health
```

Response:

```json
{"status":"healthy"}
```

The root endpoint returned:

```json
{"message":"Welcome to AI Document Assistant","status":"running"}
```

Swagger UI was accessible through:

```text
http://localhost:8000/docs
```

## 12. SSH Port Forwarding

The application was bound to EC2 localhost rather than being directly exposed to the public internet.

Used SSH local port forwarding to access the application from the laptop.

Command:

```bash
ssh -i /path/to/private-key.pem \
  -L 8000:127.0.0.1:8000 \
  ubuntu@EC2_PUBLIC_IP
```

Accessed Swagger UI from the local browser:

```text
http://localhost:8000/docs
```

**Learning:** SSH tunnelling securely forwards traffic from a local port to a remote service.

## 13. Gemini API Troubleshooting

During testing of the `/documents/ask` endpoint, the request returned an HTTP 502 error associated with a Gemini API 503 response.

Error:

```text
503 UNAVAILABLE
This model is currently experiencing high demand.
```

Updated the Gemini model configuration in `.env`:

```env
GEMINI_MODEL=gemini-3.5-flash-lite
```

The Docker container was recreated to load the updated environment configuration.

However, the subsequent question-answering test remained loading and was not confirmed successful.

**Status:** Further investigation of Gemini API availability and request handling is required.

## 14. SSH Connectivity Troubleshooting

Later, SSH connectivity became unavailable.

Checked EC2 status checks in AWS Console:

- System status: Passed
- Instance status: Passed
- EBS status: Passed

Checked the laptop's public IPv4 address:

```bash
curl -4 https://api.ipify.org
```

Reviewed the EC2 security group's SSH inbound rule.

The SSH connection continued returning:

```text
ssh: connect to host EC2_PUBLIC_IP port 22:
Connection timed out
```

The problem was not confirmed to be caused by SSH authentication.

Further network and instance troubleshooting is required before reconnecting.

## 15. AWS Cost Management

Service cost breakdown:

| Service | Cost |
|---|---:|
| EC2-Other | $0.02 |
| EC2-Instances | $0.01 |
| VPC | $0.00 |
| S3 | $0.00 |
| Other listed services | $0.00 |

The account showed that current usage was covered by AWS Free Plan credits.

Stopped the EC2 instance from the AWS Management Console to avoid further compute charges.

**Important:** Stopping an EC2 instance does not stop EBS storage charges or charges from other billable resources.

## 16. Current Deployment Status

| Component | Status |
|---|---|
| EC2 infrastructure | Created |
| Ubuntu environment | Prepared |
| Docker installation | Completed |
| GitHub repository clone | Completed |
| Docker image build | Completed |
| Docker named volume | Created |
| Environment configuration | Completed |
| Container startup | Successful |
| Gemini initialization | Successful |
| ChromaDB initialization | Successful |
| Embedding model loading | Successful |
| Health endpoint | Verified |
| Root endpoint | Verified |
| Swagger UI | Accessible during initial deployment |
| Gemini question answering | Pending further testing |
| SSH connectivity | Currently unavailable |
| EC2 instance | Stopped |

## 17. Future Improvements

Planned improvements:

1. Restore SSH connectivity.
2. Verify the Gemini question-answering endpoint.
3. Configure Nginx as a reverse proxy.
4. Configure HTTPS using an SSL certificate.
5. Consider Amazon ECR for Docker image storage.
6. Configure GitHub Actions for CI/CD.
7. Configure application monitoring and logging.
8. Configure AWS billing and usage alerts.
9. Review EBS storage and other AWS resources to manage costs.
10. Complete application deployment and end-to-end testing.

## 18. Key DevOps Concepts Practiced

- AWS EC2 provisioning and administration
- Linux server management
- SSH key-based authentication
- Security groups and port management
- Docker Engine installation
- Docker image building
- Docker container lifecycle
- Docker port mapping
- Docker named volumes
- Environment variable management
- FastAPI deployment
- Application logging and troubleshooting
- SSH local port forwarding
- AWS billing and cost monitoring

---

**Project Milestone:**

Successfully built and started the AI Document Assistant Docker container on an AWS EC2 Ubuntu server. Verified application startup, health endpoint, and root endpoint. The instance was subsequently stopped to control AWS costs. Gemini question answering and final remote connectivity remain pending.
