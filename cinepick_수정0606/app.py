from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict

import requests
from bson import ObjectId
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from pymongo import MongoClient
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from flask_cors import CORS
except ImportError:
    CORS = None

from dotenv import load_dotenv

from tmdb_client import (
    discover_movies,
    get_genres,
    get_movie_detail,
    get_popular_movies,
    get_recommendations,
    get_top_rated_movies,
    search_movies,
)

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "cinepick-dev-secret")

if CORS:
    CORS(app)

# ── MongoDB 연결 ───────────────────────────────────
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client     = MongoClient(MONGO_URI, tlsAllowInvalidCertificates=True)
db         = client["cinepick"]
users_col  = db["users"]
reviews_col  = db["reviews"]
posts_col    = db["posts"]
comments_col    = db["comments"]
notifs_col      = db["notifications"]
wishlist_col    = db["wishlist"]


# ── 로그인 필요 데코레이터 ─────────────────────────
from functools import wraps

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login", next=request.url))
        return f(*args, **kwargs)
    return decorated


# ── 페이지 라우트 ──────────────────────────────────

@app.route("/")
def home():
    popular_movies = get_popular_movies(limit=7)
    ai_movies = discover_movies(with_genres="878", sort_by="vote_average.desc", limit=10)

    # 인기글 (좋아요 순)
    raw_popular = list(posts_col.find().sort("likes", -1).limit(4))
    # 최신글 (날짜 순)
    raw_recent  = list(posts_col.find().sort("created_at", -1).limit(4))

    def format_post(p):
        return {
            "id":      str(p["_id"]),
            "title":   p.get("title", ""),
            "author":  p.get("author", ""),
            "date":    p.get("created_at", datetime.now()).strftime("%Y.%m.%d"),
            "likes":   p.get("likes", 0),
            "comments":p.get("comment_count", 0),
            "cat":     p.get("category", ""),
            "preview": p.get("content", "")[:60],
            "movie_poster": p.get("movie_poster", ""),
        }

    popular_posts = [format_post(p) for p in raw_popular]
    recent_posts  = [format_post(p) for p in raw_recent]

    return render_template("index.html",
        popular_movies=popular_movies,
        ai_movies=ai_movies,
        popular_posts=popular_posts,
        recent_posts=recent_posts,
    )


@app.route("/movie/<int:movie_id>")
def movie_detail(movie_id: int):
    movie = get_movie_detail(movie_id)

    # 해당 영화 DB 리뷰 조회
    raw_reviews = list(reviews_col.find({"movie_id": movie_id}).sort("created_at", -1).limit(20))
    movie_reviews = [{
        "id":     str(r["_id"]),
        "author": r.get("author", ""),
        "stars":  r.get("stars", 5),
        "text":   r.get("text", ""),
        "date":   r.get("created_at", datetime.now()).strftime("%Y.%m.%d"),
        "likes":  r.get("likes", 0),
        "user_id": r.get("user_id", ""),
    } for r in raw_reviews]

    return render_template("movie_detail.html", movie=movie, movie_reviews=movie_reviews)


@app.route("/movies")
def movies_list():
    query    = request.args.get("q", "").strip()
    genre_id = request.args.get("genre", "").strip()

    if query:
        movies     = search_movies(query, limit=24)
        page_title = f"'{query}' 검색 결과"
    elif genre_id:
        movies     = discover_movies(with_genres=genre_id, limit=24)
        page_title = "장르별 영화"
    else:
        movies     = get_popular_movies(limit=20)
        page_title = "인기 영화"

    return render_template(
        "movies.html",
        movies=movies,
        page_title=page_title,
        page_active="movies",
        query=query,
        genres=get_genres(),
    )


@app.route("/ranking")
def ranking():
    movies = get_top_rated_movies(limit=20)
    return render_template(
        "movies.html",
        movies=movies,
        page_title="평점 높은 영화",
        page_active="ranking",
        query="",
        genres=get_genres(),
    )


@app.route("/recommend")
def recommend():
    return render_template("recommend.html")


@app.route("/reviews")
def reviews():
    page     = request.args.get("page", 1, type=int)
    per_page = 10
    skip     = (page - 1) * per_page
    total    = reviews_col.count_documents({})
    total_pages = max(1, -(-total // per_page))  # 올림 나눗셈

    raw = list(reviews_col.find().sort("created_at", -1).skip(skip).limit(per_page))
    review_list = []
    for r in raw:
        review_list.append({
            "id":      str(r["_id"]),
            "movie":   r.get("movie_title", ""),
            "poster":  r.get("movie_poster", ""),
            "stars":   r.get("stars", 5),
            "author":  r.get("author", ""),
            "date":    r.get("created_at", datetime.now()).strftime("%Y.%m.%d"),
            "genre":   r.get("genre", ""),
            "text":    r.get("text", ""),
            "likes":   r.get("likes", 0),
        })
    return render_template("reviews.html",
        db_reviews=review_list,
        current_user=session.get("user_name"),
        page=page,
        total_pages=total_pages,
    )


@app.route("/community")
def community():
    # JS 필터링을 위해 전체 글 가져오기
    raw = list(posts_col.find().sort("created_at", -1).limit(200))
    post_list = []
    for p in raw:
        post_list.append({
            "id":       str(p["_id"]),
            "cat":      p.get("category", "잡담"),
            "title":    p.get("title", ""),
            "preview":  p.get("content", "")[:80],
            "author":   p.get("author", ""),
            "date":     p.get("created_at", datetime.now()).strftime("%Y.%m.%d"),
            "views":    str(p.get("views", 0)),
            "comments": str(p.get("comment_count", 0)),
            "likes":    str(p.get("likes", 0)),
            "img":      p.get("img", "https://placehold.co/70x70/1a1a1a/555?text=📝"),
            "movie_poster": p.get("movie_poster", ""),
        })
    return render_template("community.html",
        db_posts=post_list,
        current_user=session.get("user_name"),
    )


# ── 글 상세 ───────────────────────────────────────

@app.route("/community/<post_id>")
def post_detail(post_id):
    try:
        p = posts_col.find_one({"_id": ObjectId(post_id)})
    except Exception:
        return redirect(url_for("community"))
    if not p:
        return redirect(url_for("community"))

    # 조회수 증가
    posts_col.update_one({"_id": ObjectId(post_id)}, {"$inc": {"views": 1}})

    # 댓글 조회 (parent_id 없는 것만 + 대댓글 포함)
    raw_comments = list(comments_col.find({"post_id": post_id, "parent_id": None}).sort("created_at", 1))
    comment_list = []
    for c in raw_comments:
        cid = str(c["_id"])
        # 대댓글
        raw_replies = list(comments_col.find({"parent_id": cid}).sort("created_at", 1))
        replies = [{
            "id":     str(r["_id"]),
            "author": r.get("author", ""),
            "text":   r.get("text", ""),
            "likes":  r.get("likes", 0),
            "date":   r.get("created_at", datetime.now()).strftime("%Y.%m.%d %H:%M"),
        } for r in raw_replies]

        comment_list.append({
            "id":      cid,
            "author":  c.get("author", ""),
            "text":    c.get("text", ""),
            "likes":   c.get("likes", 0),
            "date":    c.get("created_at", datetime.now()).strftime("%Y.%m.%d %H:%M"),
            "replies": replies,
        })

    # 좋아요 세션 처리
    liked_post     = post_id in session.get("liked_posts", [])
    liked_comments = session.get("liked_comments", [])

    post_data = {
        "id":           post_id,
        "cat":          p.get("category", "잡담"),
        "title":        p.get("title", ""),
        "content":      p.get("content", ""),
        "author":       p.get("author", ""),
        "date":         p.get("created_at", datetime.now()).strftime("%Y.%m.%d %H:%M"),
        "views":        p.get("views", 0),
        "likes":        p.get("likes", 0),
        "comment_count":len(comment_list),
        "movie_poster": p.get("movie_poster", ""),
        "movie_title":  p.get("movie_title", ""),
    }

    return render_template("post_detail.html",
        post=post_data, comments=comment_list,
        liked_post=liked_post, liked_comments=liked_comments)


# ── 회원가입 ───────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        username = request.form.get("username", "").strip()

        if not email or not password or not username:
            return render_template("register.html", error="모든 항목을 입력해 주세요.")

        if users_col.find_one({"email": email}):
            return render_template("register.html", error="이미 사용 중인 이메일입니다.")

        users_col.insert_one({
            "email":      email,
            "password":   generate_password_hash(password),
            "username":   username,
            "created_at": datetime.now(),
        })
        return redirect(url_for("login", registered=1))

    return render_template("register.html")


# ── 로그인 ─────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        user = users_col.find_one({"email": email})
        if not user or not check_password_hash(user["password"], password):
            return render_template("login.html", error="이메일 또는 비밀번호가 올바르지 않습니다.")

        session["user_id"]   = str(user["_id"])
        session["user_name"] = user["username"]
        session["user_email"] = user["email"]

        next_url = request.args.get("next")
        return redirect(next_url or url_for("home"))

    registered = request.args.get("registered")
    return render_template("login.html", registered=registered)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ── 리뷰 작성 API ──────────────────────────────────

@app.route("/api/reviews", methods=["POST"])
@login_required
def api_write_review():
    body = request.get_json(silent=True) or {}
    movie_id    = body.get("movie_id")
    movie_title = body.get("movie_title", "")
    movie_poster= body.get("movie_poster", "")
    stars       = int(body.get("stars", 5))
    text        = (body.get("text") or "").strip()
    genre       = body.get("genre", "")

    if not text:
        return jsonify({"error": "리뷰 내용을 입력해 주세요."}), 400

    # movie_id가 숫자면 int로 변환
    try:
        movie_id_int = int(movie_id) if movie_id else None
    except (ValueError, TypeError):
        movie_id_int = None

    doc = {
        "movie_id":     movie_id_int,
        "movie_title":  movie_title,
        "movie_poster": movie_poster,
        "stars":        stars,
        "text":         text,
        "genre":        genre,
        "author":       session["user_name"],
        "user_id":      session["user_id"],
        "likes":        0,
        "created_at":   datetime.now(),
    }
    result = reviews_col.insert_one(doc)
    return jsonify({"ok": True, "id": str(result.inserted_id)})


@app.route("/api/reviews/<review_id>/like", methods=["POST"])
@login_required
def api_like_review(review_id):
    reviews_col.update_one({"_id": ObjectId(review_id)}, {"$inc": {"likes": 1}})
    return jsonify({"ok": True})


# ── 커뮤니티 글 작성 API ───────────────────────────

@app.route("/api/posts", methods=["POST"])
@login_required
def api_write_post():
    body     = request.get_json(silent=True) or {}
    title        = (body.get("title") or "").strip()
    content      = (body.get("content") or "").strip()
    category     = body.get("category", "잡담")
    movie_poster = body.get("movie_poster", "")
    movie_title  = body.get("movie_title", "")

    if not title or not content:
        return jsonify({"error": "제목과 내용을 입력해 주세요."}), 400

    doc = {
        "title":         title,
        "content":       content,
        "category":      category,
        "author":        session["user_name"],
        "user_id":       session["user_id"],
        "likes":         0,
        "views":         0,
        "comment_count": 0,
        "img":           "https://placehold.co/70x70/1a1a1a/555?text=📝",
        "movie_poster":  movie_poster,
        "movie_title":   movie_title,
        "created_at":    datetime.now(),
    }
    result = posts_col.insert_one(doc)
    return jsonify({"ok": True, "id": str(result.inserted_id)})


@app.route("/api/posts/<post_id>/like", methods=["POST"])
@login_required
def api_like_post(post_id):
    body   = request.get_json(silent=True) or {}
    unlike = body.get("unlike", False)
    inc    = -1 if unlike else 1
    posts_col.update_one({"_id": ObjectId(post_id)}, {"$inc": {"likes": inc}})
    liked = session.get("liked_posts", [])
    if unlike:
        liked = [x for x in liked if x != post_id]
    else:
        if post_id not in liked:
            liked.append(post_id)
    session["liked_posts"] = liked
    return jsonify({"ok": True})


# ── 마이페이지 ────────────────────────────────────

@app.route("/mypage")
@login_required
def mypage():
    user_id   = session["user_id"]
    user_name = session["user_name"]

    # 내가 쓴 리뷰
    raw_reviews = list(reviews_col.find({"user_id": user_id}).sort("created_at", -1))
    my_reviews = [{
        "id":     str(r["_id"]),
        "movie":  r.get("movie_title", ""),
        "poster": r.get("movie_poster", ""),
        "stars":  r.get("stars", 5),
        "text":   r.get("text", ""),
        "date":   r.get("created_at", datetime.now()).strftime("%Y.%m.%d"),
        "likes":  r.get("likes", 0),
    } for r in raw_reviews]

    # 찜한 영화
    raw_wishlist = list(wishlist_col.find({"user_id": user_id}).sort("created_at", -1))
    my_wishlist = [{
        "movie_id": w.get("movie_id"),
        "title":    w.get("title", ""),
        "poster":   w.get("poster", ""),
        "rating":   w.get("rating", 0),
    } for w in raw_wishlist]

    # 내가 쓴 커뮤니티 글
    raw_posts = list(posts_col.find({"user_id": user_id}).sort("created_at", -1))
    my_posts = [{
        "id":       str(p["_id"]),
        "title":    p.get("title", ""),
        "cat":      p.get("category", ""),
        "date":     p.get("created_at", datetime.now()).strftime("%Y.%m.%d"),
        "likes":    p.get("likes", 0),
        "comments": p.get("comment_count", 0),
    } for p in raw_posts]

    return render_template("mypage.html",
        user_name=user_name,
        my_reviews=my_reviews,
        my_wishlist=my_wishlist,
        my_posts=my_posts,
    )


# ── 찜하기 API ─────────────────────────────────────

@app.route("/api/wishlist/<int:movie_id>", methods=["POST"])
@login_required
def api_toggle_wishlist(movie_id):
    user_id = session["user_id"]
    body    = request.get_json(silent=True) or {}
    existing = wishlist_col.find_one({"user_id": user_id, "movie_id": movie_id})

    if existing:
        # 이미 찜 → 취소
        wishlist_col.delete_one({"_id": existing["_id"]})
        return jsonify({"ok": True, "wishlisted": False})
    else:
        # 찜 추가
        wishlist_col.insert_one({
            "user_id":    user_id,
            "movie_id":   movie_id,
            "title":      body.get("title", ""),
            "poster":     body.get("poster", ""),
            "rating":     body.get("rating", 0),
            "created_at": datetime.now(),
        })
        return jsonify({"ok": True, "wishlisted": True})


@app.route("/api/wishlist/<int:movie_id>", methods=["GET"])
@login_required
def api_check_wishlist(movie_id):
    user_id  = session["user_id"]
    existing = wishlist_col.find_one({"user_id": user_id, "movie_id": movie_id})
    return jsonify({"wishlisted": bool(existing)})


# ── 알림 헬퍼 ─────────────────────────────────────

def create_notif(to_user_id, notif_type, message, link):
    """알림을 생성합니다. to_user_id가 없으면 스킵합니다."""
    if not to_user_id:
        return
    notifs_col.insert_one({
        "user_id":    to_user_id,
        "type":       notif_type,   # "like_post" | "like_comment" | "comment" | "reply"
        "message":    message,
        "link":       link,
        "read":       False,
        "created_at": datetime.now(),
    })


# ── 알림 API ───────────────────────────────────────

@app.route("/api/notifications")
@login_required
def api_get_notifications():
    notifs = list(notifs_col.find(
        {"user_id": session["user_id"]},
    ).sort("created_at", -1).limit(20))
    result = []
    for n in notifs:
        result.append({
            "id":      str(n["_id"]),
            "type":    n.get("type", ""),
            "message": n.get("message", ""),
            "link":    n.get("link", "#"),
            "read":    n.get("read", False),
            "date":    n.get("created_at", datetime.now()).strftime("%m.%d %H:%M"),
        })
    unread = sum(1 for n in result if not n["read"])
    return jsonify({"notifications": result, "unread": unread})


@app.route("/api/notifications/<notif_id>/read", methods=["POST"])
@login_required
def api_read_notification(notif_id):
    notifs_col.update_one(
        {"_id": ObjectId(notif_id), "user_id": session["user_id"]},
        {"$set": {"read": True}}
    )
    return jsonify({"ok": True})


@app.route("/api/notifications/read-all", methods=["POST"])
@login_required
def api_read_all_notifications():
    notifs_col.update_many(
        {"user_id": session["user_id"], "read": False},
        {"$set": {"read": True}}
    )
    return jsonify({"ok": True})


# ── 댓글 API ──────────────────────────────────────

@app.route("/api/comments", methods=["POST"])
@login_required
def api_write_comment():
    body      = request.get_json(silent=True) or {}
    post_id   = body.get("post_id", "")
    text      = (body.get("text") or "").strip()
    parent_id = body.get("parent_id")  # None이면 댓글, 있으면 대댓글

    if not text:
        return jsonify({"error": "내용을 입력해 주세요."}), 400

    doc = {
        "post_id":    post_id,
        "parent_id":  parent_id,
        "text":       text,
        "author":     session["user_name"],
        "user_id":    session["user_id"],
        "likes":      0,
        "created_at": datetime.now(),
    }
    result = comments_col.insert_one(doc)
    # 게시글 댓글 수 증가
    posts_col.update_one({"_id": ObjectId(post_id)}, {"$inc": {"comment_count": 1}})

    # 알림 생성
    post = posts_col.find_one({"_id": ObjectId(post_id)})
    if post and parent_id is None:
        # 글 작성자에게 댓글 알림
        if post.get("user_id") != session["user_id"]:
            create_notif(
                post.get("user_id"),
                "comment",
                f"{session['user_name']}님이 '{post.get('title','')[:20]}' 글에 댓글을 달았어요.",
                f"/community/{post_id}"
            )
    elif parent_id:
        # 원댓글 작성자에게 대댓글 알림
        parent = comments_col.find_one({"_id": ObjectId(parent_id)})
        if parent and parent.get("user_id") != session["user_id"]:
            create_notif(
                parent.get("user_id"),
                "reply",
                f"{session['user_name']}님이 회원님의 댓글에 답글을 달았어요.",
                f"/community/{post_id}"
            )

    return jsonify({"ok": True, "id": str(result.inserted_id)})


@app.route("/api/comments/<comment_id>", methods=["DELETE"])
@login_required
def api_delete_comment(comment_id):
    comment = comments_col.find_one({"_id": ObjectId(comment_id)})
    if not comment:
        return jsonify({"error": "댓글을 찾을 수 없습니다."}), 404
    if comment.get("user_id") != session["user_id"]:
        return jsonify({"error": "삭제 권한이 없습니다."}), 403
    comments_col.delete_one({"_id": ObjectId(comment_id)})
    # 게시글 댓글 수 감소
    posts_col.update_one(
        {"_id": ObjectId(comment.get("post_id", ""))},
        {"$inc": {"comment_count": -1}}
    )
    return jsonify({"ok": True})


@app.route("/api/comments/<comment_id>/like", methods=["POST"])
@login_required
def api_like_comment(comment_id):
    body   = request.get_json(silent=True) or {}
    unlike = body.get("unlike", False)
    inc    = -1 if unlike else 1
    comments_col.update_one({"_id": ObjectId(comment_id)}, {"$inc": {"likes": inc}})
    # 세션에 좋아요 기록
    liked = session.get("liked_comments", [])
    if unlike:
        liked = [x for x in liked if x != comment_id]
    else:
        if comment_id not in liked:
            liked.append(comment_id)
    session["liked_comments"] = liked

    # 좋아요 시 알림
    if not unlike:
        comment = comments_col.find_one({"_id": ObjectId(comment_id)})
        if comment and comment.get("user_id") != session["user_id"]:
            create_notif(
                comment.get("user_id"),
                "like_comment",
                f"{session['user_name']}님이 회원님의 댓글을 좋아해요.",
                f"/community/{comment.get('post_id','')}"
            )

    return jsonify({"ok": True})


# ── 삭제 API ──────────────────────────────────────

@app.route("/api/reviews/<review_id>", methods=["DELETE"])
@login_required
def api_delete_review(review_id):
    review = reviews_col.find_one({"_id": ObjectId(review_id)})
    if not review:
        return jsonify({"error": "리뷰를 찾을 수 없습니다."}), 404
    if review.get("user_id") != session["user_id"]:
        return jsonify({"error": "삭제 권한이 없습니다."}), 403
    reviews_col.delete_one({"_id": ObjectId(review_id)})
    return jsonify({"ok": True})


@app.route("/api/posts/<post_id>", methods=["DELETE"])
@login_required
def api_delete_post(post_id):
    post = posts_col.find_one({"_id": ObjectId(post_id)})
    if not post:
        return jsonify({"error": "글을 찾을 수 없습니다."}), 404
    if post.get("user_id") != session["user_id"]:
        return jsonify({"error": "삭제 권한이 없습니다."}), 403
    posts_col.delete_one({"_id": ObjectId(post_id)})
    return jsonify({"ok": True})


# ── JSON API ───────────────────────────────────────

@app.route("/api/movies/popular")
def api_popular_movies():
    return jsonify({"results": get_popular_movies(limit=20)})


@app.route("/api/movies/search")
def api_search_movies():
    query = request.args.get("q", "")
    return jsonify({"results": search_movies(query, limit=20)})


@app.route("/api/movies/<int:movie_id>")
def api_movie_detail(movie_id: int):
    return jsonify(get_movie_detail(movie_id))


@app.route("/api/movies/<int:movie_id>/recommend")
def api_movie_recommend(movie_id: int):
    return jsonify({"results": get_recommendations(movie_id, limit=20)})


@app.route("/api/genres")
def api_genres():
    return jsonify({"genres": get_genres()})


# ── Groq AI 추천 API ───────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """당신은 영화 전문가 AI입니다.
사용자의 장르/키워드 요청을 받아 영화를 추천해 주세요.

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{
  "intro": "한 줄 추천 코멘트 (40자 이내)",
  "movies": [
    {
      "title": "영화 제목 (한국어)",
      "year": "개봉연도",
      "rating": "TMDb 평점 (숫자)",
      "poster": "",
      "reason": "이 영화를 추천하는 이유 (50자 이내)",
      "genres": ["장르1", "장르2"]
    }
  ]
}

- 영화는 5~8편 추천
- poster는 빈 문자열로 두세요
- 반드시 실존하는 영화만 추천
- JSON 외 다른 텍스트 절대 금지"""


def fetch_tmdb_poster(title):
    try:
        results = search_movies(title, limit=1)
        if results:
            m = results[0]
            return m.get("poster", ""), m.get("id")
    except Exception:
        pass
    return "", None


def call_groq(prompt: str) -> Dict[str, Any]:
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"다음 조건으로 영화를 추천해 주세요: {prompt}"},
        ],
        "temperature": 0.7,
        "max_tokens": 2048,
    }

    resp = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    raw_text = data["choices"][0]["message"]["content"].strip()

    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[-1]
        raw_text = raw_text.rsplit("```", 1)[0]

    result = json.loads(raw_text.strip())

    for movie in result.get("movies", []):
        if not movie.get("poster"):
            poster, movie_id = fetch_tmdb_poster(movie.get("title", ""))
            movie["poster"] = poster
            if movie_id:
                movie["id"] = movie_id

    return result


FALLBACK_DATA = {
    "intro": "GROQ_API_KEY를 .env에 추가하면 실제 AI 추천을 받을 수 있어요!",
    "movies": [
        {"title": "인터스텔라",      "year": "2014", "rating": "8.7", "poster": "https://image.tmdb.org/t/p/w342/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", "reason": "우주와 감동을 동시에 담은 SF 명작",   "genres": ["SF", "드라마"]},
        {"title": "인셉션",          "year": "2010", "rating": "8.8", "poster": "https://image.tmdb.org/t/p/w342/edv5CZvWj09upOsy2Y6IwDhK8bt.jpg",  "reason": "꿈 속의 꿈, 현실과 환상의 경계",   "genres": ["SF", "스릴러"]},
        {"title": "듄: 파트 2",      "year": "2024", "rating": "8.5", "poster": "https://image.tmdb.org/t/p/w342/8b8R8l88Qje9dn9OE8PY05Nxl1X.jpg",  "reason": "압도적인 스케일의 SF 서사시",       "genres": ["SF", "액션"]},
        {"title": "다크 나이트",     "year": "2008", "rating": "9.0", "poster": "https://image.tmdb.org/t/p/w342/qJ2tW6WMUDux911r6m7haRef0WH.jpg",  "reason": "히스 레저의 조커가 남긴 전설",     "genres": ["액션", "범죄"]},
        {"title": "인사이드 아웃 2", "year": "2024", "rating": "7.9", "poster": "https://image.tmdb.org/t/p/w342/vpnVM9B6NMmQpWeZvzLvDESb2QY.jpg",  "reason": "감정의 성장을 담은 따뜻한 이야기", "genres": ["애니메이션", "가족"]},
    ],
}


@app.route("/api/recommend/gemini", methods=["POST"])
def api_recommend_gemini():
    body   = request.get_json(silent=True) or {}
    prompt = (body.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "prompt가 필요합니다."}), 400

    if not GROQ_API_KEY:
        return jsonify(FALLBACK_DATA)

    try:
        result = call_groq(prompt)
        return jsonify(result)
    except json.JSONDecodeError:
        return jsonify({"error": "응답 파싱 실패"}), 500
    except Exception as e:
        print("Groq 에러:", e)
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def seed_dummy_data():
    """서버 시작 시 더미 데이터가 없으면 자동으로 삽입합니다."""
    if posts_col.count_documents({}) > 0:
        return  # 이미 데이터 있으면 스킵

    # 더미 유저 생성
    dummy_users = [
        {"username": "사막의별",   "email": "star@cinepick.com"},
        {"username": "우주여행가", "email": "space@cinepick.com"},
        {"username": "독립영화인", "email": "indie@cinepick.com"},
        {"username": "놀란빠",     "email": "nolan@cinepick.com"},
        {"username": "마블매니아", "email": "marvel@cinepick.com"},
        {"username": "조용히봐요", "email": "quiet@cinepick.com"},
    ]
    for u in dummy_users:
        if not users_col.find_one({"email": u["email"]}):
            users_col.insert_one({
                "email":      u["email"],
                "password":   generate_password_hash("cinepick1234"),
                "username":   u["username"],
                "created_at": datetime.now(),
            })

    # 더미 글 + 댓글 생성
    dummy_posts = [
        {
            "category": "영화 토론",
            "title": "듄: 파트 2 결말 해석 — 폴의 선택이 과연 옳았을까?",
            "content": "원작 소설과 비교했을 때 폴의 선택에 대한 해석이 다양한 것 같아요.\n\n영화에서는 그 부분이 좀 더 모호하게 표현된 것 같은데, 여러분들은 어떻게 보셨나요?\n\n특히 마지막 장면에서 폴이 내린 결정은 단순한 복수를 넘어서 정치적 야망으로 보이기도 하고... 원작에서는 이 부분이 더 비극적으로 묘사되는데 영화에서는 다소 영웅적으로 포장된 느낌이 들었습니다.",
            "author": "사막의별",
            "movie_poster": "https://image.tmdb.org/t/p/w342/8b8R8l88Qje9dn9OE8PY05Nxl1X.jpg",
            "movie_title": "듄: 파트 2",
            "views": 1248, "likes": 89,
            "comments": [
                {"author": "우주여행가", "text": "저도 같은 생각이에요! 원작에서는 폴이 훨씬 더 양가적인 감정을 가진 인물로 그려지는데 영화에서는 너무 영웅화된 것 같아요.", "replies": [
                    {"author": "사막의별", "text": "맞아요. 드니 빌뇌브 감독이 의도적으로 관객이 폴을 따르게 만든 것 같기도 하고요."},
                ]},
                {"author": "놀란빠", "text": "결말보다 오스틴 버틀러의 연기가 더 인상적이었습니다 ㅋㅋ 완전 소름이었어요", "replies": []},
                {"author": "마블매니아", "text": "3편이 나오면 더 명확해지지 않을까요? 원작 기준으로는 아직 갈 길이 많이 남았으니까요.", "replies": []},
            ]
        },
        {
            "category": "추천",
            "title": "인터스텔라처럼 감동적인 SF 영화 추천받고 싶어요",
            "content": "인터스텔라 재개봉 보고 완전히 반해버렸습니다.\n\n이런 감성의 SF 영화 더 있을까요? 우주 배경이어도 좋고, 시간 개념이 있는 영화도 좋아요. 가족 이야기가 곁들여진 것도 너무 좋습니다.\n\n컨택트, 마션 정도는 이미 봤어요!",
            "author": "우주여행가",
            "movie_poster": "https://image.tmdb.org/t/p/w342/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
            "movie_title": "인터스텔라",
            "views": 892, "likes": 64,
            "comments": [
                {"author": "사막의별", "text": "선생님의 별(2014) 강추드려요! 일본 영화인데 시간여행 + 가족 감동이 완벽하게 조합되어 있어요.", "replies": [
                    {"author": "우주여행가", "text": "오 제목 메모해뒀어요! 찾아볼게요 감사합니다 😊"},
                ]},
                {"author": "독립영화인", "text": "어라이벌(컨택트) 보셨다고 하셨는데 그 감독의 다른 작품인 블레이드 러너 2049도 비슷한 감성이에요.", "replies": []},
            ]
        },
        {
            "category": "잡담",
            "title": "혼자 영화 보는 분들 있으신가요? 솔직히 혼영이 더 좋은 것 같아요",
            "content": "처음엔 혼자 영화관 가는 게 민망했는데 이제는 오히려 더 집중도 잘 되고 원하는 자리 앉을 수 있어서 너무 좋더라고요.\n\n특히 팝콘 먹는 타이밍도 마음대로고, 중간에 화장실 가도 눈치 안 봐도 되고.\n\n다들 혼영 어떻게 생각하세요?",
            "author": "독립영화인",
            "movie_poster": "", "movie_title": "",
            "views": 2104, "likes": 203,
            "comments": [
                {"author": "조용히봐요", "text": "혼영 완전 찬성이요! 저는 이제 같이 보는 게 더 불편할 정도예요 ㅋㅋ", "replies": []},
                {"author": "마블매니아", "text": "혼영의 최대 장점은 감동 받아서 눈물 흘려도 아무도 모른다는 점...", "replies": [
                    {"author": "독립영화인", "text": "ㅋㅋㅋㅋ 이게 최고의 장점이죠 진짜로"},
                    {"author": "우주여행가", "text": "공감 100배입니다 ㅠㅠ"},
                ]},
                {"author": "놀란빠", "text": "저도 혼영파예요. 근데 IMAX는 혼자 보면 더 웅장하게 느껴지는 것 같아요.", "replies": []},
            ]
        },
        {
            "category": "영화 토론",
            "title": "놀란 감독 작품 순위 매겨보기 — 여러분의 픽은?",
            "content": "인셉션, 인터스텔라, 다크나이트, 테넷, 오펜하이머...\n\n다들 최고라고 하지만 개인마다 순위가 달라서 흥미롭더라고요.\n\n저는 개인적으로:\n1. 인터스텔라\n2. 인셉션\n3. 다크나이트\n4. 오펜하이머\n5. 테넷\n\n순서인데 여러분은 어떻게 생각하세요?",
            "author": "놀란빠",
            "movie_poster": "https://image.tmdb.org/t/p/w342/edv5CZvWj09upOsy2Y6IwDhK8bt.jpg",
            "movie_title": "인셉션",
            "views": 3572, "likes": 387,
            "comments": [
                {"author": "사막의별", "text": "저는 다크나이트가 1위예요. 히스 레저의 조커는 영화 역사상 최고의 악당이라고 생각해요.", "replies": [
                    {"author": "놀란빠", "text": "맞아요 조커는 레전드죠. 다크나이트도 진짜 명작인데 저한테는 인터스텔라의 감동이 더 컸어요."},
                ]},
                {"author": "마블매니아", "text": "테넷이 너무 저평가된 것 같아요! 시간 역행 개념이 너무 독창적인데.", "replies": [
                    {"author": "독립영화인", "text": "테넷은 두 번 봐야 이해되는 영화라서요 ㅋㅋ"},
                ]},
                {"author": "우주여행가", "text": "오펜하이머 실사 IMAX로 보신 분? 저는 그게 최고였어요.", "replies": []},
            ]
        },
        {
            "category": "소식",
            "title": "어벤져스 5 공식 예고편 공개! 감상 후기 남겨요",
            "content": "드디어 어벤져스 5 예고편이 공개됐네요!\n\n케빈 파이기가 언급한 것처럼 멀티버스 사가의 마무리라고 하는데, 예고편만 봐도 스케일이 어마어마한 것 같아요.\n\n여기서 잠깐 포착된 장면 중에 기존 어벤져스 멤버들이 다시 등장하는 것 같기도 하고...\n\n다들 어떻게 보셨나요?",
            "author": "마블매니아",
            "movie_poster": "https://image.tmdb.org/t/p/w342/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg",
            "movie_title": "어벤져스: 인피니티 워",
            "views": 8904, "likes": 721,
            "comments": [
                {"author": "놀란빠", "text": "예고편 보자마자 소름 돋았어요! 특히 마지막 장면...", "replies": []},
                {"author": "사막의별", "text": "MCU가 다시 살아나는 것 같아서 기대돼요. 페이즈4,5가 좀 산만했는데 이번엔 집중력 있게 가는 것 같고.", "replies": [
                    {"author": "마블매니아", "text": "맞아요! 러스토 형제가 다시 메가폰 잡았다고 하니까 기대감이 다르죠."},
                ]},
            ]
        },
        {
            "category": "잡담",
            "title": "영화관에서 팝콘 먹는 소리 정말 신경 쓰이시나요?",
            "content": "조용한 장면에서 바스락바스락...\n\n저만 엄청 거슬리나요? 아니면 다들 그냥 넘기시나요?\n\n나중에 알아보니 무음 팝콘이라는 것도 있더라고요 ㅋㅋ\n\n아니면 그냥 팝콘 대신 다른 거 드시는 분들도 계신가요?",
            "author": "조용히봐요",
            "movie_poster": "", "movie_title": "",
            "views": 4218, "likes": 312,
            "comments": [
                {"author": "독립영화인", "text": "저는 팝콘보다 옆 사람 핸드폰 불빛이 더 거슬려요 ㅠㅠ", "replies": []},
                {"author": "우주여행가", "text": "무음 팝콘 진짜 있어요?? 처음 들어봤는데 ㅋㅋㅋ", "replies": [
                    {"author": "조용히봐요", "text": "진짜 있더라고요! 해외에서 판매한다고 들었어요 ㅋㅋ"},
                ]},
                {"author": "마블매니아", "text": "저는 팝콘 소리는 괜찮은데 대화하는 사람들이 제일 싫어요.", "replies": []},
            ]
        },
    ]

    now = datetime.now()
    for i, p in enumerate(dummy_posts):
        # 유저 찾기
        user = users_col.find_one({"username": p["author"]})
        user_id = str(user["_id"]) if user else "dummy"

        post_doc = {
            "title":         p["title"],
            "content":       p["content"],
            "category":      p["category"],
            "author":        p["author"],
            "user_id":       user_id,
            "movie_poster":  p["movie_poster"],
            "movie_title":   p["movie_title"],
            "likes":         p["likes"],
            "views":         p["views"],
            "comment_count": sum(1 + len(c["replies"]) for c in p["comments"]),
            "img":           p["movie_poster"] or "https://placehold.co/70x70/1a1a1a/555?text=📝",
            "created_at":    datetime.fromtimestamp(now.timestamp() - (len(dummy_posts) - i) * 3600),
        }
        post_result = posts_col.insert_one(post_doc)
        post_id = str(post_result.inserted_id)

        # 댓글 + 대댓글 삽입
        for c in p["comments"]:
            c_user = users_col.find_one({"username": c["author"]})
            c_doc = {
                "post_id":    post_id,
                "parent_id":  None,
                "text":       c["text"],
                "author":     c["author"],
                "user_id":    str(c_user["_id"]) if c_user else "dummy",
                "likes":      0,
                "created_at": datetime.now(),
            }
            c_result = comments_col.insert_one(c_doc)
            c_id = str(c_result.inserted_id)

            for r in c.get("replies", []):
                r_user = users_col.find_one({"username": r["author"]})
                comments_col.insert_one({
                    "post_id":    post_id,
                    "parent_id":  c_id,
                    "text":       r["text"],
                    "author":     r["author"],
                    "user_id":    str(r_user["_id"]) if r_user else "dummy",
                    "likes":      0,
                    "created_at": datetime.now(),
                })

    print("[CinePick] 더미 데이터 삽입 완료!")


if __name__ == "__main__":
    seed_dummy_data()
    app.run(debug=True, port=5000)