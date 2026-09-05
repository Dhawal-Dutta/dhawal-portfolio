# Dhawal Dutta Portfolio

## Run locally

From this folder, run:

```bash
python3 server.py
```

Open `http://localhost:8000/index.html`.

## Add photo projects

Create a folder inside `projects/`. Add a `title.txt` file and image files such as `cover.jpg`, `01.jpg`, and `02.jpg`. The photo index and gallery discover them automatically after a refresh.

## Add video projects

Create a folder inside `video-projects/`. Add a `title.txt` file and one YouTube URL per line in `youtube.txt`. Local video files with `.mp4`, `.webm`, `.ogg`, or `.mov` extensions are also supported.

## Publish and maintain

1. Create a private or public GitHub repository and upload this entire folder.
2. In Render, create a new Web Service from that GitHub repository.
3. Render will use `render.yaml` and start the site with `python3 server.py`.
4. To update the live site, add or edit files, commit the changes, and push them to GitHub. Render will redeploy automatically.

Keep `title.txt` and `youtube.txt` inside their project folders. File and folder names are case-sensitive when deployed.