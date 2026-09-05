import json
import mimetypes
import os
import re
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).parent
PROJECTS = ROOT / "projects"
VIDEO_PROJECTS = ROOT / "video-projects"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogg", ".mov"}


def label_from_slug(slug):
    return re.sub(r"\s+", " ", slug.replace("-", " ")).strip().title()


def project_data(slug, request_path=""):
    folder = PROJECTS / slug
    if not folder.is_dir() or folder.parent != PROJECTS:
        return None

    title_file = folder / "title.txt"
    title = title_file.read_text(encoding="utf-8").strip() if title_file.exists() else label_from_slug(slug)
    images = sorted(path for path in folder.iterdir() if path.suffix.lower() in IMAGE_EXTENSIONS)
    cover = next((path for path in images if path.stem.lower() == "cover"), images[0] if images else None)
    encoded_title = title.replace(" ", "+")
    cover_url = f"/placeholder?text={encoded_title}" if cover is None else f"/projects/{slug}/{cover.name}"
    gallery = [
        {"src": f"/projects/{slug}/{path.name}"}
        for path in images
        if path != cover
    ]
    if not gallery:
        gallery = [
            {"src": f"/placeholder?text={encoded_title}+01"},
            {"src": f"/placeholder?text={encoded_title}+02"},
            {"src": f"/placeholder?text={encoded_title}+03"},
        ]
    return {"slug": slug, "title": title, "cover": cover_url, "images": gallery}


def video_project_data(slug):
    folder = VIDEO_PROJECTS / slug
    if not folder.is_dir() or folder.parent != VIDEO_PROJECTS:
        return None

    title_file = folder / "title.txt"
    title = title_file.read_text(encoding="utf-8").strip() if title_file.exists() else label_from_slug(slug)
    videos = sorted(path for path in folder.iterdir() if path.suffix.lower() in VIDEO_EXTENSIONS)
    cover = next((path for path in folder.iterdir() if path.stem.lower() in {"cover", "poster"} and path.suffix.lower() in IMAGE_EXTENSIONS), None)
    youtube_file = folder / "youtube.txt"
    youtube_ids = []
    if youtube_file.exists():
        youtube_ids = [youtube_id(line.strip()) for line in youtube_file.read_text(encoding="utf-8").splitlines() if line.strip()]
        youtube_ids = [video_id for video_id in youtube_ids if video_id]
    encoded_title = title.replace(" ", "+")
    if cover is not None:
        cover_url = f"/video-projects/{slug}/{cover.name}"
    elif youtube_ids:
        cover_url = f"https://img.youtube.com/vi/{youtube_ids[0]}/hqdefault.jpg"
    else:
        cover_url = f"/placeholder?text={encoded_title}"
    return {
        "slug": slug,
        "title": title,
        "cover": cover_url,
        "videos": [
            {"src": f"/video-projects/{slug}/{path.name}", "type": mimetypes.guess_type(path.name)[0] or "video/mp4"}
            for path in videos
        ] + [{"youtube": video_id} for video_id in youtube_ids],
    }


def youtube_id(value):
    parsed = urlparse(value)
    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        return parsed.path.strip("/").split("/")[0]
    if parsed.hostname in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]
        if parsed.path.startswith("/shorts/"):
            return parsed.path.split("/")[2]
        if parsed.path.startswith("/embed/"):
            return parsed.path.split("/")[2]
    return None


class PortfolioHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        path = urlparse(self.path).path
        if path.startswith("/api/") or path.endswith(".html") or "." not in path.rsplit("/", 1)[-1]:
            self.send_header("Cache-Control", "no-cache, must-revalidate")
        else:
            self.send_header("Cache-Control", "public, max-age=86400")
        super().end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/api/projects":
            projects = [project_data(folder.name) for folder in sorted(PROJECTS.iterdir()) if folder.is_dir()]
            return self.send_json([project for project in projects if project])

        if path.startswith("/api/projects/"):
            project = project_data(path.removeprefix("/api/projects/").strip("/"))
            if project is None:
                return self.send_error(404, "Project not found")
            return self.send_json(project)

        if path == "/api/videos":
            projects = [video_project_data(folder.name) for folder in sorted(VIDEO_PROJECTS.iterdir()) if folder.is_dir()]
            return self.send_json([project for project in projects if project])

        if path.startswith("/api/videos/"):
            project = video_project_data(path.removeprefix("/api/videos/").strip("/"))
            if project is None:
                return self.send_error(404, "Video project not found")
            return self.send_json(project)

        if path == "/placeholder":
            text = parse_qs(parsed.query).get("text", ["placeholder"])[0]
            svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900"><rect width="1200" height="900" fill="#e5e5e8"/><text x="600" y="450" text-anchor="middle" dominant-baseline="middle" font-family="Georgia, serif" font-size="46" fill="#111">{text}</text></svg>'''
            payload = svg.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "image/svg+xml")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        return super().do_GET()

    def send_json(self, data):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", "8000"))
    print(f"Portfolio running at http://{host}:{port}")
    ThreadingHTTPServer((host, port), PortfolioHandler).serve_forever()
