#!/usr/bin/env python3
"""QuizVerse full-stack demo backend. Python stdlib + SQLite; no pip installs required."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
import sqlite3, json, hashlib, secrets, time, os, mimetypes

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DB = ROOT / "data" / "quizverse.db"
PORT = int(os.environ.get("PORT", "8000"))
SESSIONS = {}
ADMIN_USER = "admin"
ADMIN_PASS = "Admin@123"
STUDENT_USER = "student"
STUDENT_PASS = "Student@123"

SEED_QUIZZES = [
 {"title":"Java Fundamentals","category":"Programming","description":"Core Java concepts and syntax.","minutes":5,"questions":[
  {"q":"Which keyword creates an object in Java?","o":["class","new","this","void"],"a":1,"e":"The new keyword creates an object."},
  {"q":"What is the usual Java entry-point method?","o":["start()","run()","main()","init()"],"a":2,"e":"Java applications start at main()."},
  {"q":"Which is not a primitive Java type?","o":["int","boolean","String","char"],"a":2,"e":"String is a class, not a primitive."},
  {"q":"What does OOP stand for?","o":["Object-Oriented Programming","Open Output Process","Ordered Operating Program","Object Output Protocol"],"a":0,"e":"OOP means Object-Oriented Programming."},
  {"q":"Which keyword prevents reassignment?","o":["static","final","private","const"],"a":1,"e":"final prevents reassignment."}]},
 {"title":"DBMS Basics","category":"Database","description":"Keys, SQL and relational database concepts.","minutes":5,"questions":[
  {"q":"What uniquely identifies a row in a table?","o":["Foreign key","Primary key","Duplicate key","Column label"],"a":1,"e":"A primary key uniquely identifies each row."},
  {"q":"Which SQL command retrieves data?","o":["GET","OPEN","SELECT","FETCH TABLE"],"a":2,"e":"SELECT retrieves data from tables."},
  {"q":"A foreign key helps establish what?","o":["Text formatting","Relationship between tables","Faster CPU","File extension"],"a":1,"e":"Foreign keys link records across tables."},
  {"q":"Which constraint prevents NULL values?","o":["UNIQUE","NOT NULL","DEFAULT","ORDER BY"],"a":1,"e":"NOT NULL requires a value."},
  {"q":"What does DBMS stand for?","o":["Database Management System","Digital Base Mapping Software","Data Backup Machine Service","Database Memory Structure"],"a":0,"e":"DBMS means Database Management System."}]},
 {"title":"Web Development Basics","category":"Web","description":"HTML, CSS and browser fundamentals.","minutes":5,"questions":[
  {"q":"What does HTML stand for?","o":["HyperText Markup Language","HighText Machine Language","Hyper Trainer Marking Language","Hyperlink Tool Markup Language"],"a":0,"e":"HTML structures web content."},
  {"q":"Which tag creates a hyperlink?","o":["<link>","<a>","<href>","<url>"],"a":1,"e":"The anchor tag creates links."},
  {"q":"Which language styles a web page?","o":["SQL","CSS","C++","Java"],"a":1,"e":"CSS controls appearance and layout."},
  {"q":"Which JavaScript keyword declares a block-scoped variable?","o":["dim","let","define","varname"],"a":1,"e":"let declares a block-scoped variable."},
  {"q":"Which HTTP method usually retrieves data?","o":["POST","PATCH","GET","DELETE"],"a":2,"e":"GET requests a resource."}]},
 {"title":"Electronics Quick Test","category":"Electronics","description":"Basic electrical and electronic concepts.","minutes":5,"questions":[
  {"q":"What is the SI unit of electric current?","o":["Volt","Ohm","Ampere","Watt"],"a":2,"e":"Current is measured in amperes."},
  {"q":"Which component stores energy in an electric field?","o":["Resistor","Capacitor","Fuse","Diode"],"a":1,"e":"A capacitor stores energy in an electric field."},
  {"q":"What does LED stand for?","o":["Low Energy Device","Light Emitting Diode","Linear Electric Display","Light Electronic Driver"],"a":1,"e":"LED means Light Emitting Diode."},
  {"q":"Which device converts electrical energy to rotation?","o":["DC motor","Fuse","Resistor","Transformer only"],"a":0,"e":"A motor converts electrical energy to mechanical motion."},
  {"q":"A diode ideally allows current in which direction?","o":["Both equally","Forward direction","Neither direction","Only through its case"],"a":1,"e":"A forward-biased diode conducts current."}]}
]

def connect():
    c=sqlite3.connect(DB, timeout=10)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def pw_hash(p, salt=None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", p.encode(), salt.encode(), 120000).hex()
    return salt + "$" + digest

def pw_ok(p, stored):
    try:
        salt, digest=stored.split("$",1)
        return secrets.compare_digest(hashlib.pbkdf2_hmac("sha256",p.encode(),salt.encode(),120000).hex(),digest)
    except Exception: return False

def init_db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    with connect() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('admin','student')), created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS quizzes(id INTEGER PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL, description TEXT DEFAULT '', minutes INTEGER NOT NULL DEFAULT 5, questions_json TEXT NOT NULL, created_by INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(created_by) REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, quiz_id INTEGER NOT NULL, quiz_title TEXT NOT NULL, score INTEGER NOT NULL, correct INTEGER NOT NULL, total INTEGER NOT NULL, answers_json TEXT NOT NULL, review_json TEXT NOT NULL, duration_seconds INTEGER NOT NULL DEFAULT 0, created_at TEXT DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(quiz_id) REFERENCES quizzes(id));
        """)
        for username,password,role in [(ADMIN_USER,ADMIN_PASS,"admin"),(STUDENT_USER,STUDENT_PASS,"student")]:
            row=c.execute("SELECT id FROM users WHERE username=?",(username,)).fetchone()
            if not row: c.execute("INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",(username,pw_hash(password),role))
        if c.execute("SELECT COUNT(*) n FROM quizzes").fetchone()["n"]==0:
            admin_id=c.execute("SELECT id FROM users WHERE username=?",(ADMIN_USER,)).fetchone()["id"]
            for q in SEED_QUIZZES:
                c.execute("INSERT INTO quizzes(title,category,description,minutes,questions_json,created_by) VALUES(?,?,?,?,?,?)",
                    (q["title"],q["category"],q["description"],q["minutes"],json.dumps(q["questions"]),admin_id))

def json_response(handler, status, obj):
    data=json.dumps(obj, ensure_ascii=False).encode()
    handler.send_response(status)
    handler.send_header("Content-Type","application/json; charset=utf-8")
    handler.send_header("Cache-Control","no-store")
    handler.send_header("Content-Length",str(len(data)))
    handler.end_headers()
    handler.wfile.write(data)

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(STATIC),**kwargs)
    def log_message(self, fmt,*args): print("[HTTP]",fmt%args)
    def read_json(self):
        try:
            n=int(self.headers.get("Content-Length","0"))
            if n>1_000_000: raise ValueError("Request too large")
            return json.loads(self.rfile.read(n).decode() or "{}")
        except Exception as e: raise ValueError("Invalid JSON request body") from e
    def auth(self, roles=None):
        token=self.headers.get("Authorization","").removeprefix("Bearer ").strip()
        sess=SESSIONS.get(token)
        if not sess: return None
        if roles and sess["role"] not in roles: return None
        return sess
    def do_GET(self):
        path=urlparse(self.path).path
        if path.startswith("/api/"):
            try: self.api_get(path)
            except Exception as e: json_response(self,500,{"error":"Server error","detail":str(e)})
            return
        if path=="/": self.path="/index.html"
        return super().do_GET()
    def do_POST(self):
        path=urlparse(self.path).path
        try:
            data=self.read_json()
            if path=="/api/login":
                username=str(data.get("username","")).strip()
                password=str(data.get("password",""))
                with connect() as c: u=c.execute("SELECT * FROM users WHERE username=?",(username,)).fetchone()
                if not u or not pw_ok(password,u["password_hash"]):
                    return json_response(self,401,{"error":"Incorrect username or password."})
                token=secrets.token_urlsafe(32); user={"id":u["id"],"username":u["username"],"role":u["role"]}
                SESSIONS[token]=user
                return json_response(self,200,{"token":token,"user":user})
            sess=self.auth()
            if not sess: return json_response(self,401,{"error":"Please sign in again."})
            if path=="/api/logout":
                token=self.headers.get("Authorization","").removeprefix("Bearer ").strip(); SESSIONS.pop(token,None)
                return json_response(self,200,{"ok":True})
            if path=="/api/attempts":
                quiz_id=int(data.get("quizId",0)); answers=data.get("answers",[])
                with connect() as c:
                    q=c.execute("SELECT * FROM quizzes WHERE id=?",(quiz_id,)).fetchone()
                    if not q: return json_response(self,404,{"error":"Quiz not found"})
                    questions=json.loads(q["questions_json"])
                    if not isinstance(answers,list) or len(answers)!=len(questions): return json_response(self,400,{"error":"Answer count does not match quiz."})
                    correct=sum(1 for i,x in enumerate(questions) if answers[i] is not None and answers[i]==x["a"])
                    score=round(correct*100/len(questions))
                    review=[{"q":x["q"],"options":x["o"],"correctIndex":x["a"],"selectedIndex":answers[i],"explanation":x.get("e","")} for i,x in enumerate(questions)]
                    duration=max(0,min(86400,int(data.get("durationSeconds",0))))
                    cur=c.execute("INSERT INTO attempts(user_id,quiz_id,quiz_title,score,correct,total,answers_json,review_json,duration_seconds) VALUES(?,?,?,?,?,?,?,?,?)",
                       (sess["id"],q["id"],q["title"],score,correct,len(questions),json.dumps(answers),json.dumps(review),duration))
                    aid=cur.lastrowid
                return json_response(self,201,{"id":aid,"score":score,"correct":correct,"total":len(questions),"review":review})
            import re
            add_match=re.fullmatch(r"/api/quizzes/(\d+)/questions",path)
            if add_match:
                if sess["role"]!="admin": return json_response(self,403,{"error":"Admin access required."})
                qid=int(add_match.group(1))
                new_questions=data.get("questions")
                self.validate_questions(new_questions)
                with connect() as c:
                    row=c.execute("SELECT questions_json FROM quizzes WHERE id=?",(qid,)).fetchone()
                    if not row: return json_response(self,404,{"error":"Quiz not found."})
                    existing=json.loads(row["questions_json"])
                    if len(existing)+len(new_questions)>50: return json_response(self,400,{"error":"A quiz can contain at most 50 questions."})
                    combined=existing+new_questions
                    c.execute("UPDATE quizzes SET questions_json=? WHERE id=?",(json.dumps(combined),qid))
                return json_response(self,200,{"message":f"Added {len(new_questions)} question(s). The quiz now has {len(combined)} questions.","questionCount":len(combined)})
            if path=="/api/quizzes":
                if sess["role"]!="admin": return json_response(self,403,{"error":"Admin access required."})
                title=str(data.get("title","")).strip(); category=str(data.get("category","")).strip(); desc=str(data.get("description","")).strip()
                minutes=int(data.get("minutes",5)); questions=data.get("questions")
                if not title or not category: return json_response(self,400,{"error":"Title and category are required."})
                if not 1<=minutes<=60: return json_response(self,400,{"error":"Duration must be 1 to 60 minutes."})
                self.validate_questions(questions)
                with connect() as c:
                    cur=c.execute("INSERT INTO quizzes(title,category,description,minutes,questions_json,created_by) VALUES(?,?,?,?,?,?)",(title,category,desc,minutes,json.dumps(questions),sess["id"]))
                    qid=cur.lastrowid
                return json_response(self,201,{"id":qid,"message":"Quiz created successfully."})
            return json_response(self,404,{"error":"Unknown endpoint"})
        except ValueError as e: return json_response(self,400,{"error":str(e)})
        except Exception as e: return json_response(self,500,{"error":"Server error","detail":str(e)})
    def validate_questions(self, qs):
        if not isinstance(qs,list) or not 1<=len(qs)<=50: raise ValueError("Add 1–50 questions.")
        for i,q in enumerate(qs):
            if not isinstance(q,dict) or not str(q.get("q","")).strip(): raise ValueError(f"Question {i+1}: text required.")
            opts=q.get("o")
            if not isinstance(opts,list) or len(opts)!=4 or any(not str(x).strip() for x in opts): raise ValueError(f"Question {i+1}: exactly four options required.")
            if not isinstance(q.get("a"),int) or q["a"] not in range(4): raise ValueError(f"Question {i+1}: correct answer index must be 0–3.")
    def do_DELETE(self):
        path=urlparse(self.path).path
        sess=self.auth(["admin"])
        if not sess: return json_response(self,401,{"error":"Admin sign-in required."})
        m=__import__("re").fullmatch(r"/api/quizzes/(\d+)",path)
        if not m: return json_response(self,404,{"error":"Unknown endpoint"})
        qid=int(m.group(1))
        with connect() as c:
            if not c.execute("SELECT id FROM quizzes WHERE id=?",(qid,)).fetchone(): return json_response(self,404,{"error":"Quiz not found"})
            if c.execute("SELECT COUNT(*) n FROM attempts WHERE quiz_id=?",(qid,)).fetchone()["n"]:
                return json_response(self,409,{"error":"This quiz has attempts; keep it for result history."})
            c.execute("DELETE FROM quizzes WHERE id=?",(qid,))
        return json_response(self,200,{"ok":True})
    def api_get(self,path):
        if path=="/api/health": return json_response(self,200,{"status":"ok","app":"QuizVerse","database":"SQLite","port":PORT})
        sess=self.auth()
        if not sess: return json_response(self,401,{"error":"Sign in required."})
        if path=="/api/me": return json_response(self,200,{"user":sess})
        if path=="/api/quizzes":
            with connect() as c: rows=c.execute("SELECT * FROM quizzes ORDER BY id DESC").fetchall()
            return json_response(self,200,{"quizzes":[{"id":r["id"],"title":r["title"],"category":r["category"],"description":r["description"],"minutes":r["minutes"],"questions":[{"q":x["q"],"o":x["o"]} for x in json.loads(r["questions_json"])]} for r in rows]})
        if path=="/api/my-attempts":
            with connect() as c: rows=c.execute("SELECT a.*,u.username FROM attempts a JOIN users u ON u.id=a.user_id WHERE user_id=? ORDER BY a.id DESC",(sess["id"],)).fetchall()
            return json_response(self,200,{"attempts":[self.attempt_dict(r) for r in rows]})
        if path=="/api/leaderboard":
            with connect() as c:
                rows=c.execute("SELECT u.username,COUNT(a.id) attempts,ROUND(AVG(a.score)) avg_score,MAX(a.score) best FROM users u LEFT JOIN attempts a ON a.user_id=u.id WHERE u.role='student' GROUP BY u.id ORDER BY avg_score DESC,attempts DESC").fetchall()
            return json_response(self,200,{"leaderboard":[dict(r) for r in rows]})
        if path=="/api/admin/summary":
            if sess["role"]!="admin": return json_response(self,403,{"error":"Admin access required."})
            with connect() as c:
                users=c.execute("SELECT COUNT(*) n FROM users WHERE role='student'").fetchone()["n"]
                quizzes=c.execute("SELECT COUNT(*) n FROM quizzes").fetchone()["n"]
                attempts=c.execute("SELECT COUNT(*) n FROM attempts").fetchone()["n"]
                avg=c.execute("SELECT ROUND(AVG(score)) n FROM attempts").fetchone()["n"] or 0
                recent=c.execute("SELECT a.*,u.username FROM attempts a JOIN users u ON u.id=a.user_id ORDER BY a.id DESC LIMIT 30").fetchall()
                allq=c.execute("SELECT id,title,category,minutes,created_at FROM quizzes ORDER BY id DESC").fetchall()
                students=c.execute("SELECT id,username,created_at FROM users WHERE role='student' ORDER BY username").fetchall()
            return json_response(self,200,{"stats":{"students":users,"quizzes":quizzes,"attempts":attempts,"averageScore":avg},"recentAttempts":[self.attempt_dict(r) for r in recent],"quizzes":[dict(r) for r in allq],"students":[dict(r) for r in students]})
        return json_response(self,404,{"error":"Unknown endpoint"})
    def attempt_dict(self,r):
        return {"id":r["id"],"username":r["username"],"quizTitle":r["quiz_title"],"score":r["score"],"correct":r["correct"],"total":r["total"],"date":r["created_at"],"durationSeconds":r["duration_seconds"],"review":json.loads(r["review_json"])}
    def end_headers(self):
        self.send_header("X-Content-Type-Options","nosniff")
        super().end_headers()

if __name__=="__main__":
    init_db()
    print("="*58)
    print(" QuizVerse full-stack server")
    print(f" Open: http://localhost:{PORT}")
    print(f" Admin: {ADMIN_USER} / {ADMIN_PASS}")
    print(f" Student: {STUDENT_USER} / {STUDENT_PASS}")
    print(" Database: data/quizverse.db (SQLite)")
    print(" Keep this window open while presenting.")
    print("="*58)
    ThreadingHTTPServer(("127.0.0.1",PORT),Handler).serve_forever()
