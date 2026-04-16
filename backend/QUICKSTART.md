# 🚀 Quick Start Guide

Get the FindMyRepo backend running in 5 minutes!

## Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] MongoDB Atlas account created
- [ ] Google Gemini API key obtained (free at https://makersuite.google.com/app/apikey)
- [ ] Repository data ingested into MongoDB (using the ingestion script)

## Step-by-Step Setup

### 1. Install Dependencies (2 minutes)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment (1 minute)

Create `.env` file:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
MONGO_URI=mongodb+srv://your_username:your_password@cluster.mongodb.net/
GEMINI_API_KEY=your_gemini_api_key_here
PORT=8000
ALLOWED_ORIGINS=http://localhost:5173
```

**Where to get credentials:**
- **MONGO_URI**: MongoDB Atlas → Clusters → Connect → Connect your application
- **GEMINI_API_KEY**: https://makersuite.google.com/app/apikey

### 3. Setup MongoDB Indexes (2 minutes)

⚠️ **Important**: Without indexes, queries will be very slow!

**Option A: Automated Script** (Coming soon)

**Option B: Manual Setup**

Open MongoDB Atlas Shell or Compass and run:

```javascript
use findmyrepo

// Essential indexes
db.repos.createIndex({ "stars": -1, "pushed_at": -1 })
db.repos.createIndex({ "languages": 1 })
db.repos.createIndex({ "topics": 1 })
db.repos.createIndex({ "pushed_at": -1 })
db.repos.createIndex({ "github_id": 1 }, { unique: true })
```

**Vector Search Index** (for semantic search):
- Go to Atlas → Search → Create Search Index
- Name: `vector_index`
- Definition:
```json
{
  "fields": [{
    "type": "vector",
    "path": "embedding",
    "numDimensions": 384,
    "similarity": "cosine"
  }]
}
```

### 4. Start the Server (30 seconds)

```bash
python main.py
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Test the API (1 minute)

Open a new terminal and run:

```bash
python test_api.py
```

Or test manually:

```bash
# Health check
curl http://localhost:8000/health

# Search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "python web framework"}'
```

Visit the interactive docs: http://localhost:8000/docs

## ✅ Verification Checklist

- [ ] Server starts without errors
- [ ] Health check returns `"status": "healthy"`
- [ ] Search returns results
- [ ] Swagger UI loads at `/docs`

## 🐛 Troubleshooting

### Error: "MONGO_URI not found"
- **Solution**: Check that `.env` file exists and contains valid `MONGO_URI`

### Error: "Failed to connect to MongoDB"
- **Solution**: 
  1. Verify MONGO_URI format: `mongodb+srv://username:password@cluster.mongodb.net/`
  2. Check Network Access in MongoDB Atlas (whitelist your IP or use 0.0.0.0/0)
  3. Verify credentials are correct

### Error: "GEMINI_API_KEY not found"
- **Solution**: Get API key from https://makersuite.google.com/app/apikey and add to `.env`

### Search returns no results
- **Possible causes**:
  1. No repositories in database → Run ingestion script first
  2. Repositories don't have embeddings → Re-run ingestion with embedding generation
  3. Query doesn't match any repos → Try broader search terms

### Slow queries
- **Solution**: Create MongoDB indexes (see Step 3)

## 🎯 Next Steps

1. **Connect Frontend**: Update frontend `.env` with API URL
2. **Production Deployment**: Use gunicorn or similar WSGI server
3. **Monitoring**: Add logging and monitoring tools
4. **Scale**: Use MongoDB connection pooling and caching

## 📚 Additional Resources

- [Full README](README.md) - Complete documentation
- [API Documentation](http://localhost:8000/docs) - Interactive API explorer
- [MongoDB Indexes Guide](https://docs.mongodb.com/manual/indexes/) - Index optimization

## 🆘 Getting Help

If you encounter issues:
1. Check server logs for error messages
2. Verify all prerequisites are met
3. Review the full README.md
4. Check MongoDB Atlas logs

## 🎉 Success!

If all tests pass, your backend is ready! The API is now serving:
- ✅ Intelligent search with vector embeddings
- ✅ Personalized recommendations
- ✅ Advanced filtering and pagination
- ✅ Hidden gems discovery

Connect your frontend and start discovering repositories!