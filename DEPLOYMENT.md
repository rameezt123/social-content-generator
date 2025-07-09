# Deployment Guide for Social Content Generator

## Deploying to Render

### Backend Deployment

1. **Create a new Web Service on Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Select the repository containing this project

2. **Configure Backend Service:**
   - **Name**: `social-content-generator-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Environment Variables:**
   - Add `OPENAI_API_KEY` with your OpenAI API key
   - Set `PYTHON_VERSION` to `3.11.0`

### Frontend Deployment

1. **Create a new Static Site on Render:**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New +" → "Static Site"
   - Connect your GitHub repository
   - Select the repository containing this project

2. **Configure Frontend Service:**
   - **Name**: `social-content-generator-frontend`
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

3. **Environment Variables:**
   - Add `VITE_API_URL` with your backend URL (e.g., `https://social-content-generator-backend.onrender.com`)

### Alternative: Using render.yaml

You can also deploy using the provided `render.yaml` files:

1. **Backend**: Use `backend/render.yaml`
2. **Frontend**: Use `frontend/render.yaml`

### Important Notes

- Make sure your backend service is deployed first
- Update the `VITE_API_URL` in the frontend to point to your deployed backend
- The backend will be available at: `https://your-backend-name.onrender.com`
- The frontend will be available at: `https://your-frontend-name.onrender.com`

### Local Development

For local development, the frontend will automatically use `http://localhost:8000` as the API URL.

### CORS Configuration

The backend is already configured to allow CORS from any origin for development. For production, you may want to restrict this to your frontend domain. 