# Deployment Guide for Wyzion Mem0 AI Demo

This guide covers multiple deployment options for the Wyzion Mem0 AI Demo application.

## Prerequisites

Before deploying, ensure you have:
- OpenAI API Key
- Mem0 API Key
- Python 3.11+
- Poetry (for local development)

## Table of Contents

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Railway Deployment](#railway-deployment)
4. [Render Deployment](#render-deployment)
5. [Heroku Deployment](#heroku-deployment)
6. [AWS EC2 Deployment](#aws-ec2-deployment)
7. [Environment Variables](#environment-variables)

---

## Local Development

### Setup

1. Install dependencies:
   ```bash
   poetry install
   ```

2. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. Run the application:
   ```bash
   poetry run python wyzion_mem0_ai_demo/app/main.py
   ```

The application will be available at `http://localhost:5000`

---

## Docker Deployment

### Using Docker Compose (Recommended for Local)

1. Ensure your `.env` file is configured with API keys

2. Build and run:
   ```bash
   docker-compose up --build
   ```

3. Access the app at `http://localhost:5000`

### Using Docker Directly

1. Build the image:
   ```bash
   docker build -t wyzion-mem0-ai-demo .
   ```

2. Run the container:
   ```bash
   docker run -p 5000:5000 \
     -e OPENAI_API_KEY=your_key \
     -e MEM0_API_KEY=your_key \
     -e FLASK_ENV=production \
     wyzion-mem0-ai-demo
   ```

---

## Railway Deployment

Railway is one of the easiest deployment platforms with excellent free tier.

### Steps:

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Initialize project:
   ```bash
   railway init
   ```

4. Add environment variables:
   ```bash
   railway variables set OPENAI_API_KEY=your_key
   railway variables set MEM0_API_KEY=your_key
   railway variables set FLASK_ENV=production
   ```

5. Deploy:
   ```bash
   railway up
   ```

### Alternative: Deploy via GitHub

1. Go to [Railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Add environment variables in the Railway dashboard
5. Railway will automatically detect the Dockerfile and deploy

---

## Render Deployment

Render offers free hosting with automatic HTTPS.

### Steps:

1. Go to [Render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: wyzion-mem0-ai-demo
   - **Environment**: Docker
   - **Instance Type**: Free
5. Add environment variables:
   - `OPENAI_API_KEY`
   - `MEM0_API_KEY`
   - `FLASK_ENV=production`
6. Click "Create Web Service"

Render will automatically build and deploy your Docker container.

---

## Heroku Deployment

### Prerequisites:
- [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

### Steps:

1. Login to Heroku:
   ```bash
   heroku login
   ```

2. Create a new Heroku app:
   ```bash
   heroku create wyzion-mem0-ai-demo
   ```

3. Add environment variables:
   ```bash
   heroku config:set OPENAI_API_KEY=your_key
   heroku config:set MEM0_API_KEY=your_key
   heroku config:set FLASK_ENV=production
   ```

4. Deploy:
   ```bash
   git push heroku main
   ```

5. Open your app:
   ```bash
   heroku open
   ```

---

## AWS EC2 Deployment

### Steps:

1. Launch an EC2 instance (Ubuntu 22.04 recommended)

2. SSH into your instance:
   ```bash
   ssh -i your-key.pem ubuntu@your-ec2-ip
   ```

3. Install dependencies:
   ```bash
   sudo apt update
   sudo apt install python3.11 python3-pip git -y
   pip install poetry
   ```

4. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/wyzion-mem0-ai-demo.git
   cd wyzion-mem0-ai-demo
   ```

5. Install Python dependencies:
   ```bash
   poetry install
   ```

6. Create and configure `.env` file:
   ```bash
   cp .env.example .env
   nano .env  # Add your API keys
   ```

7. Install and configure Nginx:
   ```bash
   sudo apt install nginx -y
   ```

8. Create systemd service `/etc/systemd/system/wyzion.service`:
   ```ini
   [Unit]
   Description=Wyzion Mem0 AI Demo
   After=network.target

   [Service]
   User=ubuntu
   WorkingDirectory=/home/ubuntu/wyzion-mem0-ai-demo
   Environment="PATH=/home/ubuntu/.local/bin"
   ExecStart=/home/ubuntu/.local/bin/poetry run gunicorn --bind 0.0.0.0:5000 --workers 2 wyzion_mem0_ai_demo.app.main:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

9. Start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start wyzion
   sudo systemctl enable wyzion
   ```

10. Configure Nginx as reverse proxy (create `/etc/nginx/sites-available/wyzion`):
    ```nginx
    server {
        listen 80;
        server_name your-domain.com;

        location / {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
    ```

11. Enable the site:
    ```bash
    sudo ln -s /etc/nginx/sites-available/wyzion /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    ```

---

## Environment Variables

Required environment variables for all deployments:

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |
| `MEM0_API_KEY` | Your Mem0 API key | `m0-...` |
| `FLASK_ENV` | Environment mode | `production` or `development` |
| `PORT` | Server port (optional) | `5000` |

### Setting Environment Variables

**Local (.env file)**:
```bash
OPENAI_API_KEY=sk-your-key
MEM0_API_KEY=m0-your-key
FLASK_ENV=development
```

**Railway**:
```bash
railway variables set KEY=value
```

**Render**:
Add in the dashboard under Environment Variables

**Heroku**:
```bash
heroku config:set KEY=value
```

---

## Health Checks

The application includes a basic health check endpoint at `/`. Most platforms will automatically detect this for monitoring.

For custom health checks, you can use:
```bash
curl http://your-app-url/
```

---

## Monitoring & Logs

### Railway
```bash
railway logs
```

### Render
View logs in the Render dashboard

### Heroku
```bash
heroku logs --tail
```

### Docker
```bash
docker logs -f container_name
```

---

## Security Considerations

1. Never commit `.env` file to version control
2. Use environment variables for all sensitive data
3. Enable HTTPS in production (most platforms do this automatically)
4. Rotate API keys regularly
5. Consider implementing rate limiting for production
6. Review Flask security best practices

---

## Troubleshooting

### Application won't start
- Check that all environment variables are set correctly
- Verify API keys are valid
- Check logs for specific error messages

### Port binding issues
- Ensure `PORT` environment variable is set correctly
- Check if another service is using the same port

### Memory issues
- Consider using more workers/threads in gunicorn
- Monitor memory usage and scale accordingly

---

## Recommended Platform Comparison

| Platform | Free Tier | Ease of Use | Auto-Deploy | Custom Domain |
|----------|-----------|-------------|-------------|---------------|
| Railway | ✅ ($5 credit) | ⭐⭐⭐⭐⭐ | ✅ | ✅ |
| Render | ✅ (Limited) | ⭐⭐⭐⭐⭐ | ✅ | ✅ |
| Heroku | ✅ (Sleep after inactivity) | ⭐⭐⭐⭐ | ✅ | ✅ |
| AWS EC2 | ❌ | ⭐⭐⭐ | ❌ | ✅ |

**Recommendation**: Start with Railway or Render for quick deployment with minimal configuration.

---

## Support

For issues or questions:
- Check application logs
- Review this deployment guide
- Check platform-specific documentation
