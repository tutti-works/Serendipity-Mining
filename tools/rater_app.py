from __future__ import annotations

import argparse
import json
import random
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
    index: Optional[int] = None
    rating: int
    plan_name: Optional[str] = None
    uid: Optional[str] = None


class RaterState:
    def __init__(self, profile: str, plan_names: List[str], output_dir: Path) -> None:
        self.profile = profile
        self.plan_names = plan_names
        self.primary_plan = plan_names[0] if plan_names else "explore"
        self.output_dir = output_dir
        self.manifest_path = output_dir / "manifest.jsonl"
        self.images_root = output_dir / "images"
        self.ratings_paths = {
            name: output_dir / "ratings" / f"{name}.jsonl" for name in plan_names
        }
        self.lock = threading.Lock()
        self.ratings_lock = threading.Lock()
        self.default_seed = random.randint(0, 1_000_000)
        self.plan_by_key: Dict[str, dict] = {}
        self.items: List[dict] = []
        self.items_by_key: Dict[str, dict] = {}
        self.ratings: Dict[str, int] = {}
        self.tag_options: Dict[str, List[str]] = {}
        self.load_all()

    def load_all(self) -> None:
        with self.lock:
            self.plan_by_key = self.load_plans()
            self.ratings = self.load_ratings()
            self.items = self.load_items()
            self.items_by_key = {item["uid"]: item for item in self.items}
            self.tag_options = self.build_tag_options()

    def load_plans(self) -> Dict[str, dict]:
        mapping: Dict[str, dict] = {}
        for plan_name in self.plan_names:
            plan_path = self.output_dir / f"{plan_name}.jsonl"
            if not plan_path.exists():
                raise FileNotFoundError(f"plan not found: {plan_path}")
            for line in plan_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                    idx = int(data["index"])
                except Exception:
                    continue
                key = f"{plan_name}:{idx}"
                mapping[key] = data
        return mapping

    def load_ratings(self) -> Dict[int, int]:
        mapping: Dict[str, int] = {}
        for plan_name, ratings_path in self.ratings_paths.items():
            if not ratings_path.exists():
                continue
            for line in ratings_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except Exception:
                    continue
                rec_plan = data.get("plan_name") or plan_name
                if rec_plan not in self.plan_names:
                    continue
                idx = data.get("index")
                rating = data.get("rating")
                if not isinstance(idx, int) or rating not in (0, 1, 2):
                    continue
                key = f"{rec_plan}:{idx}"
                mapping[key] = int(rating)
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

    def is_preferred_filename(self, filename: str, plan_name: str) -> bool:
        return filename.startswith(f"batch_{plan_name}_")

    def build_tag_options(self) -> Dict[str, List[str]]:
        tags_by_cat: Dict[str, set] = {}
        for item in self.items:
            slot_tags = item.get("slot_tags") or {}
            for cat, tag in slot_tags.items():
                tags_by_cat.setdefault(cat, set()).add(tag)
        return {cat: sorted(tags) for cat, tags in tags_by_cat.items()}

    def load_items(self) -> List[dict]:
        if not self.manifest_path.exists():
            return []
        items_by_key: Dict[str, dict] = {}
        for line in self.manifest_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            plan_name = rec.get("plan_name")
            if plan_name not in self.plan_names:
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
            if not isinstance(index, int):
                continue
            key = f"{plan_name}:{index}"
            plan_item = self.plan_by_key.get(key)
            if not plan_item:
                continue
            words = self.build_words(axis_id, plan_item.get("slots") or {})
            item = {
                "index": index,
                "axis_id": axis_id,
                "image_url": f"/images/{axis_id}/{fname}",
                "words": words,
                "final_image_filename": fname,
                "slot_tags": plan_item.get("slot_tags") or {},
                "plan_name": plan_name,
                "uid": key,
            }
            existing = items_by_key.get(key)
            if not existing:
                items_by_key[key] = item
                continue
            existing_pref = self.is_preferred_filename(existing["final_image_filename"], plan_name)
            new_pref = self.is_preferred_filename(fname, plan_name)
            if new_pref and not existing_pref:
                items_by_key[key] = item
                continue
            if new_pref == existing_pref:
                items_by_key[key] = item
        return list(items_by_key.values())

    def ordered_items(self, seed: Optional[int], items: Optional[List[dict]] = None) -> List[dict]:
        base = items if items is not None else self.items
        rated_items = [item for item in base if item["uid"] in self.ratings]
        unrated_items = [item for item in base if item["uid"] not in self.ratings]
        rated_items.sort(key=lambda x: (x["plan_name"], x["index"]))
        use_seed = self.default_seed if seed is None else seed
        rng = random.Random(use_seed)
        rng.shuffle(unrated_items)
        return rated_items + unrated_items

    def filtered_items(self, tag_filter: Optional[str], rating_filter: Optional[str]) -> List[dict]:
        items = list(self.items)
        if tag_filter and tag_filter != "all":
            if ":" in tag_filter:
                cat, tag = tag_filter.split(":", 1)
                items = [item for item in items if item.get("slot_tags", {}).get(cat) == tag]
        if rating_filter and rating_filter != "all":
            if rating_filter == "unrated":
                items = [item for item in items if item["uid"] not in self.ratings]
            else:
                try:
                    rating_val = int(rating_filter)
                except ValueError:
                    rating_val = None
                if rating_val is not None:
                    items = [
                        item
                        for item in items
                        if self.ratings.get(item["uid"]) == rating_val
                    ]
        return items

    def resolve_key(self, index: Optional[int], plan_name: Optional[str], uid: Optional[str]) -> Optional[str]:
        if uid:
            return uid
        if plan_name and index is not None:
            return f"{plan_name}:{index}"
        if len(self.plan_names) == 1 and index is not None:
            return f"{self.primary_plan}:{index}"
        return None

    def write_rating(self, index: Optional[int], rating: int, plan_name: Optional[str], uid: Optional[str]) -> dict:
        key = self.resolve_key(index, plan_name, uid)
        if not key:
            raise KeyError("missing key")
        item = self.items_by_key.get(key)
        if not item:
            raise KeyError(key)
        target_plan = item["plan_name"]
        record = {
            "rated_at": datetime.utcnow().isoformat(),
            "profile": self.profile,
            "plan_name": target_plan,
            "index": item["index"],
            "axis_id": item["axis_id"],
            "rating": rating,
            "words": item["words"],
        }
        with self.ratings_lock:
            ratings_path = self.ratings_paths.get(target_plan)
            if not ratings_path:
                ratings_path = self.output_dir / "ratings" / f"{target_plan}.jsonl"
                self.ratings_paths[target_plan] = ratings_path
            ratings_path.parent.mkdir(parents=True, exist_ok=True)
            with open(ratings_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            self.ratings[key] = rating
        return record

    def rating_counts(self) -> tuple[int, int]:
        rated = sum(1 for key in self.ratings.keys() if key in self.items_by_key)
        total = len(self.items)
        return rated, total


def build_app(state: RaterState) -> FastAPI:
    app = FastAPI()
    app.mount("/images", StaticFiles(directory=state.images_root), name="images")

    @app.get("/", response_class=HTMLResponse)
    def index() -> str:
        return HTML_TEMPLATE

    @app.get("/api/page")
    def api_page(
        offset: int = 0,
        limit: int = 4,
        seed: Optional[int] = None,
        tag: Optional[str] = None,
        rating: Optional[str] = None,
    ):
        filtered = state.filtered_items(tag, rating)
        items = state.ordered_items(seed, filtered)
        page = items[offset : offset + limit]
        payload = []
        for item in page:
            payload.append(
                {
                    "index": item["index"],
                    "plan_name": item["plan_name"],
                    "uid": item["uid"],
                    "axis_id": item["axis_id"],
                    "image_url": item["image_url"],
                    "words": item["words"],
                    "rating": state.ratings.get(item["uid"]),
                }
            )
        rated_count, total_count = state.rating_counts()
        return {
            "items": payload,
            "total": len(items),
            "offset": offset,
            "limit": limit,
            "filter_tag": tag,
            "filter_rating": rating,
            "rated_count": rated_count,
            "total_count": total_count,
        }

    @app.post("/api/rate")
    def api_rate(req: RateRequest):
        if req.rating not in (0, 1, 2):
            raise HTTPException(status_code=400, detail="rating must be 0, 1, or 2")
        try:
            record = state.write_rating(req.index, req.rating, req.plan_name, req.uid)
        except KeyError:
            raise HTTPException(status_code=404, detail="index not found")
        rated_count, total_count = state.rating_counts()
        return {"ok": True, "record": record, "rated_count": rated_count, "total_count": total_count}

    @app.get("/api/report")
    def api_report():
        axis_stats: Dict[str, Dict[str, int]] = {}
        for key, rating in state.ratings.items():
            item = state.items_by_key.get(key)
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

    @app.get("/api/filters")
    def api_filters():
        return {"tags": state.tag_options}

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
    .controls { display: flex; align-items: center; gap: 8px; }
    .controls label { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #ccc; }
    .controls select { background: #0f0f0f; color: #eee; border: 1px solid #333; padding: 2px 6px; }
  </style>
</head>
<body>
    <div class="topbar">
    <div>Rater (0/1/2)</div>
    <div class="controls">
      <label>Tag
        <select id="tagFilter">
          <option value="all">all</option>
        </select>
      </label>
      <label>Rating
        <select id="ratingFilter">
          <option value="all">all</option>
          <option value="unrated">unrated</option>
          <option value="0">0</option>
          <option value="1">1</option>
          <option value="2">2</option>
        </select>
      </label>
    </div>
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
    let currentTotal = 0;

    async function fetchPage() {
      const url = new URL("/api/page", window.location.origin);
      url.searchParams.set("offset", offset);
      url.searchParams.set("limit", limit);
      const tag = document.getElementById("tagFilter").value;
      const rating = document.getElementById("ratingFilter").value;
      if (tag) url.searchParams.set("tag", tag);
      if (rating) url.searchParams.set("rating", rating);
      if (seed) url.searchParams.set("seed", seed);
      const res = await fetch(url);
      const data = await res.json();
      render(data.items);
      currentTotal = data.total || 0;
      updateStatus(data.rated_count, data.total_count, currentTotal);
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
        tile.dataset.plan = item.plan_name;
        tile.dataset.uid = item.uid;
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
      const planName = tile.dataset.plan;
      const uid = tile.dataset.uid;
      const res = await fetch("/api/rate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ index, rating: value, plan_name: planName, uid }),
      });
      if (res.ok) {
        const payload = await res.json();
        const badge = tile.querySelector(".rating") || document.createElement("div");
        badge.className = "rating";
        badge.textContent = value;
        tile.appendChild(badge);
        updateStatus(payload.rated_count, payload.total_count, currentTotal);
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

    function updateStatus(ratedCount, totalCount, filteredTotal) {
      const el = document.getElementById("status");
      if (!el) return;
      const extra = filteredTotal !== undefined ? ` | filtered ${filteredTotal}` : "";
      el.textContent = `rated ${ratedCount} / ${totalCount}${extra}`;
    }

    async function loadFilters() {
      const res = await fetch("/api/filters");
      if (!res.ok) return;
      const data = await res.json();
      const select = document.getElementById("tagFilter");
      const tags = data.tags || {};
      for (const cat of Object.keys(tags).sort()) {
        for (const tag of tags[cat]) {
          const opt = document.createElement("option");
          opt.value = `${cat}:${tag}`;
          opt.textContent = `${cat}:${tag}`;
          select.appendChild(opt);
        }
      }
    }

    document.getElementById("tagFilter").addEventListener("change", () => {
      offset = 0;
      selected = 0;
      fetchPage();
    });
    document.getElementById("ratingFilter").addEventListener("change", () => {
      offset = 0;
      selected = 0;
      fetchPage();
    });

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

    loadFilters().then(fetchPage);
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Serendipity Mining local rater")
    parser.add_argument("--profile", type=str, default="4cats", help="Profile name (e.g., 3labs, 4cats)")
    parser.add_argument("--plan-name", type=str, default="explore", help="Plan name (e.g., explore)")
    parser.add_argument(
        "--plan-names",
        type=str,
        default="",
        help="Comma-separated plan names to load together (overrides --plan-name).",
    )
    parser.add_argument("--output", type=str, default="./out", help="Output root (default: ./out)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host")
    parser.add_argument("--port", type=int, default=8000, help="Port")
    args = parser.parse_args()

    output_root = Path(args.output)
    output_dir = output_root if output_root.name == args.profile else output_root / args.profile
    if args.plan_names:
        plan_names = [p.strip() for p in args.plan_names.split(",") if p.strip()]
    else:
        plan_names = [args.plan_name]
    state = RaterState(args.profile, plan_names, output_dir)
    app = build_app(state)

    import uvicorn

    uvicorn.run(app, host=args.host, port=args.port, workers=1)


if __name__ == "__main__":
    main()
