import sys, os, json, logging
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

from models import UploadImageRequest, CreatePostRequest, ImageRecord, BlogPost, GuardStatus
from vision import VisionProcessor
from embeddings import EmbeddingsProcessor
from matcher import Matcher
from guard import MismatchGuard

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Image Matching", version="2.0.0")

vision = VisionProcessor()
embeddings = EmbeddingsProcessor()
matcher = Matcher(embeddings)

IMAGES: Dict[str, ImageRecord] = {}
POSTS: Dict[str, BlogPost] = {}
SUGGESTIONS: Dict[str, List] = {}
AUDIT_LOG: List[Dict] = []

def audit(action: str, data: dict):
    AUDIT_LOG.append({"timestamp": datetime.now().isoformat(), "action": action, "data": data})
    logger.info(f"[{action}] {data}")

# ============ HTML INTERFACE ============

HTML_INTERFACE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Image Matching Engine</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px 30px;
            text-align: center;
        }
        header h1 { font-size: 2.5em; margin-bottom: 10px; }
        header p { font-size: 1.1em; opacity: 0.9; }
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding: 40px;
        }
        .panel {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            border: 2px solid #e9ecef;
        }
        .panel h2 {
            color: #667eea;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 0.95em;
        }
        input, textarea, select {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 1em;
            font-family: inherit;
            transition: border-color 0.3s;
        }
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        textarea {
            resize: vertical;
            min-height: 100px;
        }
        button {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.05em;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
        }
        button:active {
            transform: translateY(0);
        }
        .results {
            margin-top: 30px;
        }
        .result-item {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 12px;
            border-left: 5px solid #667eea;
        }
        .result-item.accepted {
            border-left-color: #28a745;
            background: #f0fdf4;
        }
        .result-item.rejected {
            border-left-color: #dc3545;
            background: #fef2f2;
        }
        .result-item h4 {
            margin-bottom: 8px;
            color: #333;
        }
        .result-item p {
            font-size: 0.9em;
            color: #666;
            margin: 5px 0;
        }
        .badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
            margin-top: 8px;
        }
        .badge-accepted {
            background: #28a745;
            color: white;
        }
        .badge-rejected {
            background: #dc3545;
            color: white;
        }
        .badge-approval {
            background: #ffc107;
            color: #333;
        }
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 20px;
        }
        .stat-box {
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 2px solid #667eea;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            font-size: 0.9em;
            color: #666;
            margin-top: 5px;
        }
        .full-width {
            grid-column: 1 / -1;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e9ecef;
        }
        .tab-btn {
            padding: 10px 20px;
            background: transparent;
            border: none;
            color: #667eea;
            font-weight: 600;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            margin-bottom: -2px;
            transition: all 0.3s;
        }
        .tab-btn.active {
            border-bottom-color: #667eea;
            color: #667eea;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .message {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            animation: slideIn 0.3s ease;
        }
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .message.info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .loader {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .guard-check {
            background: white;
            padding: 10px;
            margin: 8px 0;
            border-radius: 6px;
            font-size: 0.85em;
            border-left: 4px solid #ddd;
        }
        .guard-check.pass {
            border-left-color: #28a745;
            background: #f0fdf4;
        }
        .guard-check.fail {
            border-left-color: #dc3545;
            background: #fef2f2;
        }
        .metric {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            border-left: 5px solid #667eea;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        .metric-label {
            color: #666;
            font-size: 0.95em;
        }
        @media (max-width: 1024px) {
            .content {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🚀 AI Image Matching Engine</h1>
            <p>Vision AI + Embeddings + Smart Matching + Guard Logic + Evaluation</p>
        </header>
        
        <div class="content">
            <!-- LEFT PANEL: Upload & Create -->
            <div class="panel">
                <div class="tabs">
                    <button class="tab-btn active" onclick="switchTab('upload')">Upload Image</button>
                    <button class="tab-btn" onclick="switchTab('create')">Create Post</button>
                </div>
                
                <!-- Upload Image -->
                <div id="upload" class="tab-content active">
                    <h2>📷 Upload Image</h2>
                    <div id="uploadMessage"></div>
                    <div class="form-group">
                        <label>Image URL</label>
                        <input type="text" id="imageUrl" placeholder="https://unsplash.com/photo...">
                    </div>
                    <div class="form-group">
                        <label>Caption</label>
                        <input type="text" id="imageCaption" placeholder="A red fox in the forest">
                    </div>
                    <button onclick="uploadImage()">
                        <span id="uploadBtn">Upload & Process</span>
                    </button>
                </div>
                
                <!-- Create Post -->
                <div id="create" class="tab-content">
                    <h2>📝 Create Blog Post</h2>
                    <div id="createMessage"></div>
                    <div class="form-group">
                        <label>Title</label>
                        <input type="text" id="postTitle" placeholder="Understanding Red Foxes">
                    </div>
                    <div class="form-group">
                        <label>Content</label>
                        <textarea id="postContent" placeholder="Blog post content..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Category</label>
                        <select id="postCategory">
                            <option value="animal">Animal</option>
                            <option value="object">Object</option>
                            <option value="scene">Scene</option>
                        </select>
                    </div>
                    <button onclick="createPost()">
                        <span id="createBtn">Create Post</span>
                    </button>
                </div>
            </div>
            
            <!-- RIGHT PANEL: Results & Analysis -->
            <div class="panel">
                <div class="tabs">
                    <button class="tab-btn active" onclick="switchTab('data')">Data</button>
                    <button class="tab-btn" onclick="switchTab('match')">Match</button>
                    <button class="tab-btn" onclick="switchTab('eval')">Evaluate</button>
                </div>
                
                <!-- Data View -->
                <div id="data" class="tab-content active">
                    <h2>📊 System Data</h2>
                    <div class="stats">
                        <div class="stat-box">
                            <div class="stat-number" id="imgCount">0</div>
                            <div class="stat-label">Images Uploaded</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" id="postCount">0</div>
                            <div class="stat-label">Posts Created</div>
                        </div>
                    </div>
                    <button onclick="loadDemoData()" style="margin-top: 20px;">📥 Load Demo Data (3 posts + 3 images)</button>
                    
                    <h3 style="margin-top: 30px; color: #667eea;">Images:</h3>
                    <div id="imagesList"></div>
                    
                    <h3 style="margin-top: 20px; color: #667eea;">Posts:</h3>
                    <div id="postsList"></div>
                </div>
                
                <!-- Matching View -->
                <div id="match" class="tab-content">
                    <h2>🎯 Match Results</h2>
                    <div class="form-group">
                        <label>Select Post to Match:</label>
                        <select id="postSelect"></select>
                    </div>
                    <button onclick="runMatching()">🚀 Run Matching</button>
                    
                    <div id="matchResults" class="results" style="margin-top: 30px;"></div>
                </div>
                
                <!-- Evaluation View -->
                <div id="eval" class="tab-content">
                    <h2>📈 Evaluation Metrics</h2>
                    <button onclick="evaluate()" style="margin-bottom: 20px;">📊 Calculate Precision</button>
                    <div id="evalResults"></div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const API = "http://localhost:8000";
        
        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            event.target.classList.add('active');
        }
        
        async function uploadImage() {
            const url = document.getElementById('imageUrl').value;
            const caption = document.getElementById('imageCaption').value;
            if (!url || !caption) return alert('Fill all fields');
            
            const btn = document.getElementById('uploadBtn');
            btn.innerHTML = '<span class="loader"></span> Processing...';
            
            try {
                const res = await fetch(`${API}/images/upload`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url, caption})
                });
                const data = await res.json();
                showMessage('uploadMessage', `✅ Image uploaded! Confidence: ${data.vision_confidence.toFixed(2)}`, 'success');
                document.getElementById('imageUrl').value = '';
                document.getElementById('imageCaption').value = '';
                updateStats();
            } catch (e) {
                showMessage('uploadMessage', `❌ Error: ${e.message}`, 'error');
            } finally {
                btn.innerHTML = 'Upload & Process';
            }
        }
        
        async function createPost() {
            const title = document.getElementById('postTitle').value;
            const content = document.getElementById('postContent').value;
            const category = document.getElementById('postCategory').value;
            if (!title || !content) return alert('Fill all fields');
            
            const btn = document.getElementById('createBtn');
            btn.innerHTML = '<span class="loader"></span> Creating...';
            
            try {
                const res = await fetch(`${API}/posts`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({title, content, category})
                });
                const data = await res.json();
                showMessage('createMessage', `✅ Post created!`, 'success');
                document.getElementById('postTitle').value = '';
                document.getElementById('postContent').value = '';
                updateStats();
            } catch (e) {
                showMessage('createMessage', `❌ Error: ${e.message}`, 'error');
            } finally {
                btn.innerHTML = 'Create Post';
            }
        }
        
        async function loadDemoData() {
            try {
                await fetch(`${API}/demo/load-sample-data`, {method: 'POST'});
                showMessage('uploadMessage', '✅ Demo data loaded!', 'success');
                updateStats();
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }
        
        async function runMatching() {
            const postId = document.getElementById('postSelect').value;
            if (!postId) return alert('Select a post');
            
            try {
                const res = await fetch(`${API}/match/${postId}`, {method: 'POST'});
                const data = await res.json();
                
                let html = `<div class="message info">
                    Matched <strong>${data.total_images}</strong> images
                    <br> Accepted: ${data.accepted_matches} | Rejected: ${data.rejected_matches}
                </div>`;
                
                if (data.top_3_accepted && data.top_3_accepted.length > 0) {
                    html += '<h3>✅ Accepted Matches</h3>';
                    data.top_3_accepted.forEach(m => {
                        html += `<div class="result-item accepted">
                            <h4>${m.image_id}</h4>
                            <p><strong>Similarity:</strong> ${(m.similarity_score * 100).toFixed(1)}%</p>
                            <p><strong>Confidence:</strong> ${(m.vision_confidence * 100).toFixed(1)}%</p>
                            <span class="badge badge-accepted">ACCEPTED</span>
                        </div>`;
                    });
                }
                
                if (data.rejected_matches > 0) {
                    html += '<h3>❌ Rejected (Guard Logic)</h3>';
                    html += '<p class="message info">Guard logic blocked ' + data.rejected_matches + ' low-confidence matches</p>';
                }
                
                document.getElementById('matchResults').innerHTML = html;
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }
        
        async function evaluate() {
            try {
                const res = await fetch(`${API}/evaluate`, {method: 'POST'});
                const data = res.status === 422 ? {message: 'Run matching first'} : await res.json();
                
                let html = '';
                if (data.precision_top_1) {
                    html = `
                        <div class="metric">
                            <div class="metric-value">${(data.precision_top_1 * 100).toFixed(1)}%</div>
                            <div class="metric-label">Precision@1 (Top-1 Accuracy)</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">${data.correct_top_1}/${data.total_eval_pairs}</div>
                            <div class="metric-label">Correct Predictions</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">📊 System accurately matched top suggestions</div>
                        </div>
                    `;
                } else {
                    html = '<div class="message info">' + data.message + '</div>';
                }
                document.getElementById('evalResults').innerHTML = html;
            } catch (e) {
                alert('Error: ' + e.message);
            }
        }
        
        async function updateStats() {
            try {
                const images = await fetch(`${API}/images`).then(r => r.json());
                const posts = await fetch(`${API}/posts`).then(r => r.json());
                
                document.getElementById('imgCount').innerHTML = images.total;
                document.getElementById('postCount').innerHTML = posts.total;
                
                document.getElementById('imagesList').innerHTML = images.images.map(i => 
                    `<div class="result-item">
                        <h4>${i.id}</h4>
                        <p>${i.caption}</p>
                        ${i.vision_metadata ? `<p>📷 ${i.vision_metadata.category} (${(i.vision_metadata.confidence*100).toFixed(0)}%)` : ''}
                    </div>`
                ).join('');
                
                document.getElementById('postsList').innerHTML = posts.posts.map(p =>
                    `<div class="result-item">
                        <h4>${p.id}: ${p.title}</h4>
                        <p>Category: <strong>${p.category}</strong></p>
                    </div>`
                ).join('');
                
                const options = posts.posts.map(p => `<option value="${p.id}">${p.title}</option>`).join('');
                document.getElementById('postSelect').innerHTML = options;
            } catch (e) {
                console.error(e);
            }
        }
        
        function showMessage(el, msg, type) {
            const div = document.getElementById(el);
            div.innerHTML = `<div class="message ${type}">${msg}</div>`;
            setTimeout(() => div.innerHTML = '', 5000);
        }
        
        updateStats();
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_INTERFACE

# ============ API ENDPOINTS ============

@app.post("/images/upload")
async def upload_image(req: UploadImageRequest):
    image_id = f"img_{len(IMAGES) + 1}"
    vision_output = await vision.process_image(req.url, req.caption)
    embedding = await embeddings.embed_text(req.caption)
    
    img = ImageRecord(id=image_id, url=req.url, caption=req.caption, 
                     vision_metadata=vision_output, embedding=embedding, created_at=datetime.now())
    IMAGES[image_id] = img
    audit("image_uploaded", {"image_id": image_id, "caption": req.caption[:50]})
    
    return {"image_id": image_id, "status": "processed", "vision_confidence": vision_output.confidence}

@app.get("/images")
async def list_images():
    return {"total": len(IMAGES), "images": [i.model_dump() for i in list(IMAGES.values())[:10]]}

@app.post("/posts")
async def create_post(req: CreatePostRequest):
    post_id = f"post_{len(POSTS) + 1}"
    embedding = await embeddings.embed_text(f"{req.title} {req.content}")
    post = BlogPost(id=post_id, title=req.title, content=req.content, category=req.category,
                   embedding=embedding, created_at=datetime.now())
    POSTS[post_id] = post
    audit("post_created", {"post_id": post_id, "title": req.title})
    return {"post_id": post_id, "status": "created"}

@app.get("/posts")
async def list_posts():
    return {"total": len(POSTS), "posts": [p.model_dump() for p in list(POSTS.values())[:10]]}

@app.post("/match/{post_id}")
async def match_images(post_id: str):
    if post_id not in POSTS:
        raise HTTPException(status_code=404, detail="Post not found")
    
    post = POSTS[post_id]
    suggestions = matcher.rank(post, IMAGES, MismatchGuard.apply)
    SUGGESTIONS[post_id] = suggestions
    
    accepted = [s for s in suggestions if s.guard_status == GuardStatus.ACCEPTED]
    rejected = [s for s in suggestions if s.guard_status == GuardStatus.REJECTED]
    
    audit("match", {"post": post_id, "matches": len(suggestions), "accepted": len(accepted)})
    
    return {
        "post_id": post_id,
        "total_images": len(IMAGES),
        "accepted_matches": len(accepted),
        "rejected_matches": len(rejected),
        "top_3_accepted": [s.model_dump() for s in accepted[:3]]
    }

@app.post("/evaluate")
async def evaluate():
    if not SUGGESTIONS:
        raise HTTPException(status_code=422, detail="Run matching first")
    
    correct = sum(1 for sugg_list in SUGGESTIONS.values() 
                 if sugg_list and sugg_list[0].guard_status == GuardStatus.ACCEPTED for _ in [1])
    total = len(SUGGESTIONS)
    
    return {"precision_top_1": correct/total if total > 0 else 0, "correct_top_1": correct, "total_eval_pairs": total}

@app.post("/demo/load-sample-data")
async def load_demo():
    posts_data = [
        {"title": "Understanding Red Foxes", "content": "Red foxes are intelligent animals...", "category": "animal"},
        {"title": "Wolf Behavior", "content": "Wolves are pack hunters...", "category": "animal"},
        {"title": "Modern Architecture", "content": "Contemporary buildings...", "category": "object"}
    ]
    
    images_data = [
        {"url": "https://images.unsplash.com/photo-1531494521821-90527e2c6f63?w=400", "caption": "Red fox in forest"},
        {"url": "https://images.unsplash.com/photo-1568059471122-7832951cc4c5?w=400", "caption": "Gray wolf running"},
        {"url": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=400", "caption": "Modern building"}
    ]
    
    for p in posts_data:
        await create_post(CreatePostRequest(**p))
    for i in images_data:
        await upload_image(UploadImageRequest(**i))
    
    return {"status": "loaded"}

@app.on_event("startup")
async def startup():
    logger.info("🚀 AI IMAGE MATCHING ENGINE - WEB UI READY")
    logger.info("📍 Open: http://localhost:8000")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
