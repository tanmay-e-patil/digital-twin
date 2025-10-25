# Mise Deployment Tasks

This document explains how to use the `mise.toml` configuration to run deployment tasks individually or as a complete workflow.

## Prerequisites

- [Install mise](https://mise.jdx.dev/getting-started.html)
- AWS credentials configured
- Terraform installed

## Environment Variables

You can override the default environment variables:

```bash
export ENVIRONMENT=prod  # dev, test, or prod (default: dev)
export PROJECT_NAME=my-project  # default: twin
```

## Available Tasks

### Individual Tasks

1. **Build Lambda package**
   ```bash
   mise run build-lambda
   ```

2. **Initialize Terraform**
   ```bash
   mise run terraform-init
   ```

3. **Create or select Terraform workspace**
   ```bash
   mise run terraform-workspace
   ```

4. **Apply Terraform configuration**
   ```bash
   mise run terraform-apply
   ```

5. **Get Terraform outputs**
   ```bash
   mise run get-terraform-outputs
   ```

6. **Build frontend**
   ```bash
   mise run build-frontend
   ```

7. **Deploy frontend to S3**
   ```bash
   mise run deploy-frontend
   ```

8. **Show deployment information**
   ```bash
   mise run deploy-info
   ```

### Combined Tasks

1. **Full deployment** (equivalent to the original script)
   ```bash
   mise run deploy
   ```

2. **Deploy backend only**
   ```bash
   mise run deploy-backend
   ```

3. **Deploy frontend only**
   ```bash
   mise run deploy-frontend-only
   ```

## Usage Examples

### Deploy to development environment (default)
```bash
mise run deploy
```

### Deploy to production environment
```bash
ENVIRONMENT=prod mise run deploy
```

### Deploy with custom project name
```bash
PROJECT_NAME=my-digital-twin mise run deploy
```

### Step-by-step deployment
If you want to run the deployment step by step and verify each stage:

```bash
# 1. Build the Lambda package
mise run build-lambda

# 2. Initialize and apply Terraform
mise run terraform-init
mise run terraform-workspace
mise run terraform-apply

# 3. Build and deploy frontend
mise run build-frontend
mise run deploy-frontend

# 4. Show deployment information
mise run deploy-info
```

### Deploy only the backend
```bash
mise run deploy-backend
```

### Deploy only the frontend (after backend is already deployed)
```bash
mise run deploy-frontend-only
```

## Benefits

1. **Granular control**: Run only the parts you need
2. **Error recovery**: If one step fails, you can fix it and continue from that point
3. **Parallel development**: Frontend and backend teams can work independently
4. **Faster iteration**: No need to redeploy everything when only one part changes

## Migration from scripts/deploy.sh

The original `scripts/deploy.sh` script is still available for backward compatibility. The mise tasks provide the same functionality but with more flexibility:

```bash
# Old way
./scripts/deploy.sh prod my-project

# New way
ENVIRONMENT=prod PROJECT_NAME=my-project mise run deploy