"""
SYNTHEX AI — Intelligent Flask Chatbot Backend
Run: pip install flask requests && python app.py
Open: http://localhost:5000
"""

from flask import Flask, request, jsonify, send_from_directory
import requests, random, time, re, os, json

app = Flask(__name__, static_folder=".")

# ═══════════════════════════════════════════════════════
#  MEMORY SYSTEM
# ═══════════════════════════════════════════════════════
memory = {}  # { normalized_q: { count, last_answer, topic } }

def remember(q, answer, topic="general"):
    key = normalize(q)
    memory[key] = {
        "count": memory.get(key, {}).get("count", 0) + 1,
        "last_answer": answer,
        "topic": topic
    }

def recall(q):
    return memory.get(normalize(q), {})

def normalize(q):
    return re.sub(r"[^a-z0-9 ]", "", q.lower().strip())

# ═══════════════════════════════════════════════════════
#  INTROS / CLOSERS — rotated every response
# ═══════════════════════════════════════════════════════
INTROS = [
    "Here's what you need to know —",
    "Sharp breakdown incoming:",
    "Let me cut right to it:",
    "Real talk on this one:",
    "Straight signal, no noise:",
    "Breaking it down precisely:",
    "Good question — here's the core of it:",
]

CLOSERS = [
    "Stay curious — that's how you level up.",
    "You're asking the right things.",
    "Keep digging — depth rewards you.",
    "That's the signal. Everything else is noise.",
    "Build on this. Don't just read it.",
    "Now you know. Use it.",
]

# ═══════════════════════════════════════════════════════
#  KNOWLEDGE BASE — keyword → structured response
# ═══════════════════════════════════════════════════════
KB = {
    "python": {
        "title": "Python Programming",
        "points": [
            "High-level, interpreted language — easy to read, fast to write",
            "Dominant in AI/ML, web backends, automation, and data science",
            "Key libraries: NumPy, Pandas, TensorFlow, Flask, FastAPI",
            "Dynamic typing — variables don't need explicit type declarations",
            "Runs on CPython interpreter; also has PyPy for speed"
        ],
        "tip": "Master list comprehensions and generators early — they separate beginners from intermediates.",
        "example": "Google, Instagram, NASA, and Spotify all use Python in production."
    },
    "machine learning": {
        "title": "Machine Learning",
        "points": [
            "Subset of AI — systems learn from data without explicit programming",
            "Three types: Supervised, Unsupervised, Reinforcement Learning",
            "Core algorithms: Linear Regression, Decision Trees, Neural Networks",
            "Model quality depends on data quality more than algorithm choice",
            "Evaluation metrics: accuracy, precision, recall, F1-score"
        ],
        "tip": "80% of ML work is data cleaning — get comfortable with Pandas early.",
        "example": "Netflix recommendations, spam filters, and fraud detection are all ML in action."
    },
    "cybersecurity": {
        "title": "Cybersecurity",
        "points": [
            "Practice of protecting systems, networks, and data from digital attacks",
            "Core domains: Network Security, App Security, Cloud Security, Ethical Hacking",
            "CIA Triad: Confidentiality, Integrity, Availability",
            "Tools: Wireshark, Metasploit, Burp Suite, Nmap",
            "Certifications: CEH, OSCP, CompTIA Security+"
        ],
        "tip": "Start on TryHackMe or HackTheBox — theory without labs is worthless.",
        "example": "The 2017 WannaCry ransomware attack hit 200,000+ machines in 150 countries in 24 hours."
    },
    "artificial intelligence": {
        "title": "Artificial Intelligence",
        "points": [
            "AI = machines simulating human intelligence — reasoning, learning, problem-solving",
            "Branches: ML, Deep Learning, NLP, Computer Vision, Robotics",
            "Modern AI is largely statistical — not truly 'thinking', but predicting",
            "Large Language Models (LLMs) like GPT use transformer architecture",
            "AI is a tool — its impact depends entirely on how it's applied"
        ],
        "tip": "Learn what AI cannot do as much as what it can — that's where real judgment lives.",
        "example": "ChatGPT, Google Search ranking, Tesla Autopilot, and medical imaging diagnosis."
    },
    "blockchain": {
        "title": "Blockchain Technology",
        "points": [
            "Distributed ledger — data stored in linked, cryptographically secured blocks",
            "Decentralized: no single authority controls the chain",
            "Consensus mechanisms: Proof of Work (PoW), Proof of Stake (PoS)",
            "Smart contracts: self-executing code on the blockchain (Ethereum)",
            "Beyond crypto: used in supply chain, healthcare, identity verification"
        ],
        "tip": "Understand hash functions and Merkle trees before anything else in blockchain.",
        "example": "Bitcoin processes ~7 tx/sec. Visa does ~24,000. That scalability gap is blockchain's core challenge."
    },
    "networking": {
        "title": "Computer Networking",
        "points": [
            "OSI Model: 7 layers from Physical to Application",
            "TCP/IP is the foundational protocol of the modern internet",
            "Key protocols: HTTP/S, DNS, DHCP, SSH, FTP, SMTP",
            "Subnetting divides networks for efficiency and security",
            "Firewalls, VPNs, and IDS/IPS are core defense tools"
        ],
        "tip": "Learn subnetting until it's second nature — it appears in every sysadmin and security role.",
        "example": "Every website request you make goes through DNS resolution, TCP handshake, and HTTP exchange."
    },
    "linux": {
        "title": "Linux Operating System",
        "points": [
            "Open-source Unix-like OS — powers 96% of the world's servers",
            "Distributions: Ubuntu, Kali, Debian, Arch, CentOS, Fedora",
            "Everything is a file in Linux — even hardware devices",
            "Shell commands are faster and more powerful than any GUI for most tasks",
            "Permissions system: read (r), write (w), execute (x) for user/group/other"
        ],
        "tip": "Spend 30 min a day in the terminal for 30 days — you'll never fear the command line again.",
        "example": "Android, most smart TVs, and all cloud servers run on Linux kernels."
    },
    "flask": {
        "title": "Flask Web Framework",
        "points": [
            "Lightweight Python web framework — minimal by design",
            "Built on Werkzeug (WSGI) and Jinja2 (templating)",
            "RESTful APIs are Flask's strongest use case",
            "No ORM or form validation built-in — pick your own tools",
            "Scales well with Gunicorn + Nginx in production"
        ],
        "tip": "Use Flask blueprints from day one if your app will have more than 3 routes.",
        "example": "Pinterest and LinkedIn both started their backends on Flask."
    },
    "data science": {
        "title": "Data Science",
        "points": [
            "Extracting insights and decisions from structured and unstructured data",
            "Core stack: Python, Pandas, NumPy, Matplotlib, Scikit-learn",
            "Pipeline: Data collection → Cleaning → EDA → Modeling → Deployment",
            "Statistics is the foundation — probability, distributions, hypothesis testing",
            "Jupyter Notebooks are standard for exploration and prototyping"
        ],
        "tip": "A clean, well-visualized analysis beats a complex model with dirty data every time.",
        "example": "Spotify's 'Discover Weekly' is a data science product that runs on 30M+ users' listening history."
    },
    "api": {
        "title": "APIs (Application Programming Interfaces)",
        "points": [
            "APIs define how software components communicate with each other",
            "REST is the dominant pattern — uses HTTP methods: GET, POST, PUT, DELETE",
            "JSON is the standard data format for modern web APIs",
            "Authentication: API keys, OAuth 2.0, JWT tokens",
            "Rate limiting prevents abuse — always handle 429 errors in your code"
        ],
        "tip": "Always read the error response body — it tells you exactly what went wrong.",
        "example": "Every time you 'Login with Google', you're using OAuth — an API authentication standard."
    },
    "git": {
        "title": "Git Version Control",
        "points": [
            "Distributed version control system — tracks every change in your codebase",
            "Core concepts: commit, branch, merge, rebase, pull request",
            "GitHub/GitLab are hosting platforms — Git is the underlying tool",
            "Branching strategy matters: GitFlow, trunk-based development",
            "Interactive rebase lets you rewrite history cleanly before merging"
        ],
        "tip": "Commit early, commit often, write meaningful messages — your future self will thank you.",
        "example": "The Linux kernel has 1,000+ contributors. Git makes that collaboration possible."
    },
    "cloud": {
        "title": "Cloud Computing",
        "points": [
            "Delivery of computing services over the internet — on demand, pay-as-you-go",
            "Big 3: AWS (market leader), Azure (enterprise), GCP (AI/ML strength)",
            "Service models: IaaS, PaaS, SaaS",
            "Core services: compute (EC2), storage (S3), database (RDS), functions (Lambda)",
            "DevOps and cloud go hand-in-hand — CI/CD, containers, Kubernetes"
        ],
        "tip": "Get AWS Solutions Architect Associate first — it maps to real-world architecture decisions.",
        "example": "Netflix runs entirely on AWS — 15% of all internet traffic at peak hours."
    },
    "deep learning": {
        "title": "Deep Learning",
        "points": [
            "Subset of ML using multi-layered neural networks to learn from data",
            "Key architectures: CNNs (images), RNNs/LSTMs (sequences), Transformers (language)",
            "Frameworks: PyTorch (research favorite), TensorFlow/Keras (production)",
            "Requires large datasets and GPU compute to train effectively",
            "Transfer learning: reuse pre-trained models to solve new problems faster"
        ],
        "tip": "Don't train from scratch — fine-tune existing models. It's 100x faster and often better.",
        "example": "GPT-4, DALL-E, AlphaFold — all deep learning. AlphaFold solved protein folding in 1 year."
    },
}

# ═══════════════════════════════════════════════════════
#  WIKIPEDIA SEARCH
# ═══════════════════════════════════════════════════════
def wiki_search(query):
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(query)
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            data = r.json()
            extract = data.get("extract", "")
            title   = data.get("title", query)
            if extract and len(extract) > 80:
                # Trim to 3 sentences max
                sentences = re.split(r'(?<=[.!?])\s+', extract.strip())
                summary   = " ".join(sentences[:3])
                return title, summary
    except Exception:
        pass
    return None, None

# ═══════════════════════════════════════════════════════
#  DYNAMIC FALLBACK GENERATOR
# ═══════════════════════════════════════════════════════
def dynamic_answer(topic, wiki_summary=None):
    words = topic.strip().split()
    cap   = topic.title()

    if wiki_summary:
        points = [
            wiki_summary,
            f"This is an active and relevant area in modern technology and knowledge systems",
            f"Understanding {cap} requires breaking it into core principles first",
            f"Practical application of {cap} separates theory from real skill",
            f"Cross-disciplinary knowledge often unlocks deeper insight into {cap}",
        ]
    else:
        points = [
            f"{cap} is a structured domain with its own principles, patterns, and practices",
            f"The fundamentals of {cap} are learnable — start with the 20% that covers 80% of use cases",
            f"Real understanding of {cap} comes from doing, not just reading",
            f"Most experts in {cap} agree: consistent practice beats occasional deep dives",
            f"Breaking {cap} into sub-topics makes it far less overwhelming",
        ]

    tip     = f"Start with one clear goal related to {cap}. Scope beats breadth when learning anything new."
    example = f"{cap} has real-world applications across industries — identifying them helps you see its actual value."

    return {
        "title":   cap,
        "points":  points,
        "tip":     tip,
        "example": example
    }

# ═══════════════════════════════════════════════════════
#  CORE ANSWER ENGINE
# ═══════════════════════════════════════════════════════
def build_response(kb_data, intro, closer, repeat=False, count=1):
    pts = kb_data["points"]
    if repeat and count > 1:
        # Give deeper slice of points + extra depth line
        pts = pts + [f"Going deeper: {kb_data['title']} rewards those who revisit it — each pass reveals a new layer."]
    return {
        "intro":   intro,
        "title":   kb_data["title"],
        "points":  pts,
        "tip":     kb_data["tip"],
        "example": kb_data["example"],
        "closer":  closer,
    }

def answer_query(q):
    lower = q.lower().strip()
    mem   = recall(q)
    count = mem.get("count", 0)
    intro  = random.choice(INTROS)
    closer = random.choice(CLOSERS)

    # ── Greetings ──
    greetings = ["yo", "hi", "hello", "hey", "sup", "what's up", "hola"]
    if lower in greetings:
        return {
            "kind": "plain",
            "text": "Hey — Synthex AI online.\nAsk me anything. I don't do vague answers.",
            "closer": closer
        }

    # ── Identity ──
    if any(x in lower for x in ["who made you", "who created you", "who built you", "your creator"]):
        return {
            "kind": "plain",
            "text": "I'm Synthex AI — built for clarity, speed, and confident answers.\nCreated by Mr. Gaurav — AI & Cybersecurity Student.",
            "closer": closer
        }

    # ── Capability questions ──
    if any(x in lower for x in ["what can you do", "what do you know", "your capabilities", "help me"]):
        return {
            "kind": "plain",
            "text": "I can answer questions on:\n• AI / ML / Deep Learning\n• Python, Flask, Git, APIs\n• Cybersecurity, Networking, Linux\n• Cloud, Data Science, Blockchain\n• Any topic — I'll reason through it.\n\nJust ask. Don't hold back.",
            "closer": closer
        }

    # ── Knowledge base match ──
    for keyword, data in KB.items():
        if keyword in lower:
            repeat = count > 0
            resp   = build_response(data, intro, closer, repeat=repeat, count=count + 1)
            resp["kind"] = "block"
            result_text  = json.dumps(resp)
            remember(q, result_text, topic=keyword)
            return resp

    # ── Wikipedia fallback ──
    topic = re.sub(r"(what is|what are|tell me about|explain|define|how does|who is|why is)\s*", "", lower).strip()
    if not topic:
        topic = lower

    wiki_title, wiki_summary = wiki_search(topic)
    kb_data = dynamic_answer(wiki_title or topic, wiki_summary)
    resp = {
        "kind":    "block",
        "intro":   intro,
        "title":   kb_data["title"],
        "points":  kb_data["points"],
        "tip":     kb_data["tip"],
        "example": kb_data["example"],
        "closer":  closer,
    }
    remember(q, json.dumps(resp), topic=topic)
    return resp

# ═══════════════════════════════════════════════════════
#  FLASK ROUTES
# ═══════════════════════════════════════════════════════
@app.route("/")
def index():
    return send_from_directory(".", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    q    = data.get("message", "").strip()
    if not q:
        return jsonify({"error": "Empty message"}), 400
    resp = answer_query(q)
    return jsonify(resp)

if __name__ == "__main__":
    print("\n  ╔══════════════════════════════╗")
    print("  ║   SYNTHEX AI — STARTING...   ║")
    print("  ║   http://localhost:5000       ║")
    print("  ╚══════════════════════════════╝\n")
    app.run(debug=True, port=5000)
