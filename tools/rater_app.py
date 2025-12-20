from __future__ import annotations

import argparse
import json
import random
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


AXIS_WORDS = {
    "mat_object": ("MATERIAL", "OBJECT"),
    "anachronism": ("ERA_STYLE", "TECH_THING"),
    "abstract_concrete": ("ABSTRACT_CONCEPT", "CONCRETE_THING"),
    "scale_landscape": ("SUBJECT_A", "SUBJECT_B"),
}


class RateRequest(BaseModel):
    index: int
    rating: int


class RaterState:
    def __init__(self, profile: str, plan_name: str, output_dir: Path) -> None:
        self.profile = profile
        self.plan_name = plan_name
        self.output_dir = output_dir
        self.plan_path = output_dir / f"{plan_name}.jsonl"
        self.manifest_path = output_dir / "manifest.jsonl"
        self.images_root = output_dir / "images"
        self.ratings_path = output_dir / "ratings" / f"{plan_name}.jsonl"
        self.lock = threading.Lock()
        self.ratings_lock = threading.Lock()
        self.default_seed = random.randint(0, 1_000_000)
        self.plan_by_index: Dict[int, dict] = {}
        self.items: List[dict] = []
        self.items_by_index: Dict[int, dict] = {}
        self.ratings: Dict[int, int] = {}
        self.load_all()

    def load_all(self) -> None:
        with self.lock:
            self.plan_by_index = self.load_plan()
            self.ratings = self.load_ratings()
            self.items = self.load_items()
            self.items_by_index = {item["index"]: item for item in self.items}

    def load_plan(self) -> Dict[int, dict]:
        if not self.plan_path.exists():
            raise FileNotFoundError(f"plan not found: {self.plan_path}")
        mapping: Dict[int, dict] = {}
        for line in self.plan_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                mapping[int(data["index"])] = data
            except Exception:
                continue
        return mapping

    def load_ratings(self) -> Dict[int, int]:
        if not self.ratings_path.exists():
            return {}
        mapping: Dict[int, int] = {}
        for line in self.ratings_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                mapping[int(data["index"])] = int(data["rating"])
            except Exception:
                continue
        return mapping

    def build_words(self, axis_id: str, slots: dict) -> str:
        keys = AXIS_WORDS.get(axis_id)
        words: List[str] = []
        if keys:
            for key in keys:
                if key in slots:
                    words.append(str(slots[key]))
        else:
            for key in sorted(slots.keys())[:2]:
                words.append(str(slots[key]))
        return " x ".join(words)

    def load_items(self) -> List[dict]:
        if not self.manifest_path.exists():
            return []
        items: List[dict] = []
        for line in self.manifest_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            if rec.get("plan_name") != self.plan_name:
                continue
            if rec.get("status") != "success":
                continue
            fname = rec.get("final_image_filename")
            axis_id = rec.get("axis_id")
            if not fname or not axis_id:
                continue
            img_path = self.images_root / axis_id / fname
            if not img_path.exists():
                continue
            index = rec.get("index")
            plan_item = self.plan_by_index.get(index)
            if not plan_item:
                continue
            words = self.build_words(axis_id, plan_item.get("slots") or {})
            items.append(
                {
                    "index": index,
                    "axis_id": axis_id,
                    "image_url": f"/images/{axis_id}/{fname}",
                    "words": words,
                    "final_image_filename": fname,
                }
            )
        return items

    def ordered_items(self, seed: Optional[int]) -> List[dict]:
        order = list(self.items)
        use_seed = self.default_seed if seed is None else seed
        rng = random.Random(use_seed)
        rng.shuffle(order)
        return order

    def write_rating(self, index: int, rating: int) -> dict:
        item = self.items_by_index.get(index)
        if not item:
            raise KeyError(index)
        record = {
            "rated_at": datetime.utcnow().isoformat(),
            "profile": self.profile,
            "plan_name": self.plan_name,
            "index": index,
            "axis_id": item["axis_id"],
            "rating": rating,
            "words": item["words"],
        }
        with self.ratings_lock:
            self.ratings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ratings_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.ratings[index] = rating
        return record

    def rating_counts(self) -> tuple[int, int]:
        rated = sum(1 for idx in self.ratings.keys() if idx in self.items_by_index)
        total = len(self.items)
        return rated, total


def build_app(state: RaterState) -> FastAPI:
    app = FastAPI()
    app.mount("/images", StaticFiles(directory=state.images_root), name="images")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return HTML_TEMPLATE

    @app.get("/api/page")
    def api_page(offset: int = 0, limit: int = 4, seed: Optional[int] = None):
        items = state.ordered_items(seed)
        page = items[offset : offset + limit]
        payload = []
        for item in page:
            payload.append(
                {
                    "index": item["index"],
                    "axis_id": item["axis_id"],
                    "image_url": item["image_url"],
                    "words": item["words"],
                    "rating": state.ratings.get(item["index"]),
                }
            )
        rated_count, total_count = state.rating_counts()
        return {
            "items": payload,
            "total": len(items),
            "offset": offset,
            "limit": limit,
            "rated_count": rated_count,
            "total_count": total_count,
        }

    @app.post("/api/rate")
    def api_rate(req: RateRequest):
        if req.rating not in (0, 1, 2):
            raise HTTPException(status_code=400, detail="rating must be 0, 1, or 2")
        try:
            record = state.write_rating(req.index, req.rating)
        except KeyError:
            raise HTTPException(status_code=404, detail="index not found")
        rated_count, total_count = state.rating_counts()
        return {"ok": True, "record": record, "rated_count": rated_count, "total_count": total_count}

    @app.get("/api/report")
    def api_report():
        axis_stats: Dict[str, Dict[str, int]] = {}
        for idx, rating in state.ratings.items():
            item = state.items_by_index.get(idx)
            if not item:
                continue
            axis_id = item["axis_id"]
            axis_stats.setdefault(axis_id, {"0": 0, "1": 0, "2": 0, "total": 0})
            axis_stats[axis_id][str(rating)] += 1
            axis_stats[axis_id]["total"] += 1
        report = {}
        for axis_id, stats in axis_stats.items():
            total = stats["total"]
            score = (stats["2"] / total) if total else 0.0
            report[axis_id] = {"counts": stats, "score": score}
        return JSONResponse(report)

    @app.post("/api/reload")
    def api_reload():
        state.load_all()
        return {"ok": True, "items": len(state.items)}

    return app


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Serendipity Mining Rater</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; background: #111; color: #eee; }
    .topbar { padding: 10px 16px; background: #1b1b1b; display: flex; gap: 16px; align-items: center; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; grid-gap: 12px; padding: 12px; }
    .tile { position: relative; border: 2px solid #333; background: #000; cursor: pointer; }
    .tile.selected { border-color: #4da3ff; }
    .tile img { display: block; width: 100%; height: auto; }
    .words { padding: 6px 8px; font-size: 14px; color: #ddd; background: #0f0f0f; }
    .rating { position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.7); color: #fff;
              font-size: 28px; padding: 4px 8px; border-radius: 6px; }
    .hint { font-size: 12px; color: #aaa; }
  </style>
</head>
<body>
    <div class="topbar">
    <div>Rater (0/1/2)</div>
    <div id="status" class="hint">rated 0 / 0</div>
    <div class="hint">Arrows: move, 0/1/2: rate, n/space: next, p: prev, r: reload</div>
  </div>
  <div id="grid" class="grid"></div>
  <script>
    const limit = 4;
    let offset = 0;
    let selected = 0;
    const params = new URLSearchParams(window.location.search);
    const seed = params.get("seed");

    async function fetchPage() {
      const url = new URL("/api/page", window.location.origin);
      url.searchParams.set("offset", offset);
      url.searchParams.set("limit", limit);
      if (seed) url.searchParams.set("seed", seed);
      const res = await fetch(url);
      const data = await res.json();
      render(data.items);
      updateStatus(data.rated_count, data.total_count);
      if (data.items.length === 0 && offset > 0) {
        offset = Math.max(0, offset - limit);
        return fetchPage();
      }
    }

    function render(items) {
      const grid = document.getElementById("grid");
      grid.innerHTML = "";
      items.forEach((item, idx) => {
        const tile = document.createElement("div");
        tile.className = "tile" + (idx === selected ? " selected" : "");
        tile.dataset.index = item.index;
        tile.dataset.pos = idx;
        const img = document.createElement("img");
        img.src = item.image_url;
        const words = document.createElement("div");
        words.className = "words";
        words.textContent = item.words;
        tile.appendChild(img);
        if (item.rating !== null && item.rating !== undefined) {
          const badge = document.createElement("div");
          badge.className = "rating";
          badge.textContent = item.rating;
          tile.appendChild(badge);
        }
        tile.appendChild(words);
        tile.addEventListener("click", () => {
          selected = idx;
          updateSelection();
        });
        grid.appendChild(tile);
      });
    }

    function updateSelection() {
      document.querySelectorAll(".tile").forEach((tile, idx) => {
        if (idx === selected) tile.classList.add("selected");
        else tile.classList.remove("selected");
      });
    }

    async function rateSelected(value) {
      const tiles = document.querySelectorAll(".tile");
      if (tiles.length === 0) return;
      const tile = tiles[selected];
      const index = parseInt(tile.dataset.index, 10);
      const res = await fetch("/api/rate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index, rating: value }),
      });
      if (res.ok) {
        const payload = await res.json();
        const badge = tile.querySelector(".rating") || document.createElement("div");
        badge.className = "rating";
        badge.textContent = value;
        tile.appendChild(badge);
        updateStatus(payload.rated_count, payload.total_count);
        moveSelection(1);
        if (allRated()) nextPage();
      }
    }

    function allRated() {
      return Array.from(document.querySelectorAll(".tile")).every(tile => tile.querySelector(".rating"));
    }

    function moveSelection(delta) {
      const tiles = document.querySelectorAll(".tile");
      if (tiles.length === 0) return;
      selected = (selected + delta + tiles.length) % tiles.length;
      updateSelection();
    }

    function moveByArrow(key) {
      if (key === "ArrowRight") moveSelection(1);
      if (key === "ArrowLeft") moveSelection(-1);
      if (key === "ArrowDown") moveSelection(2);
      if (key === "ArrowUp") moveSelection(-2);
    }

    function nextPage() { offset += limit; selected = 0; fetchPage(); }
    function prevPage() { offset = Math.max(0, offset - limit); selected = 0; fetchPage(); }

    async function reloadPage() {
      await fetch("/api/reload", { method: "POST" });
      fetchPage();
    }

    function updateStatus(ratedCount, totalCount) {
      const el = document.getElementById("status");
      if (!el) return;
      el.textContent = `rated ${ratedCount} / ${totalCount}`;
    }

    document.addEventListener("keydown", (e) => {
      if (["ArrowLeft","ArrowRight","ArrowUp","ArrowDown"].includes(e.key)) {
        e.preventDefault();
        moveByArrow(e.key);
        return;
      }
      if (e.key === "0" || e.key === "1" || e.key === "2") {
        rateSelected(parseInt(e.key, 10));
        return;
      }
      if (e.key === "n" || e.key === " " ) {
        nextPage();
        return;
      }
      if (e.key === "p") {
        prevPage();
        return;
      }
      if (e.key === "r") {
        reloadPage();
      }
    });

    fetchPage();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Serendipity Mining local rater")
    parser.add_argument("--profile", type=str, default="4cats", help="Profile name (e.g., 3labs, 4cats)")
    parser.add_argument("--plan-name", type=str, default="explore", help="Plan name (e.g., explore)")
    parser.add_argument("--output", type=str, default="./out", help="Output root (default: ./out)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host")
    parser.add_argument("--port", type=int, default=8000, help="Port")
    args = parser.parse_args()

    output_root = Path(args.output)
    output_dir = output_root if output_root.name == args.profile else output_root / args.profile
    state = RaterState(args.profile, args.plan_name, output_dir)
    app = build_app(state)

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, workers=1)


if __name__ == "__main__":
    main()
