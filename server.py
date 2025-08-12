# server.py
import json
import random
import time
from typing import Optional, Dict

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session, select, SQLModel, create_engine
from models import User, GameSession
from auth_utils import hash_password, verify_password, create_token, decode_token

# --- Config ---
DATABASE_URL = "sqlite:///./game_db.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
GAME_NAME = "Kings of Realms: Factions War — Pro Demo"

origins = ["*"]  # pour le dev, tu peux restreindre

app = FastAPI(title=GAME_NAME)
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# ---- initial DB create
def init_db():
    SQLModel.metadata.create_all(engine)
init_db()

# ---- constants
FACTIONS = {
    "Gangs": ["Razor", "Viper", "Knuck"],
    "Militaires": ["Captain", "Sergeant", "Tanko"],
    "Cyborgs": ["Unit-01", "Mecha-X", "Neuro"],
    "AnimauxMod": ["Fangy", "Spore", "Gorepaw"],
    "Aliens": ["Zylo", "Kra'th", "Mimic"],
    "Orques": ["Gruk", "Ragnar", "Bonecrusher"]
}
BUILDINGS = ["Townhall", "Barracks", "GoldMine", "ElixirCollector", "Walls"]

# ---- Helpers
def get_user_by_username(username: str) -> Optional[User]:
    with Session(engine) as s:
        q = select(User).where(User.username == username)
        return s.exec(q).first()

def get_session_by_sid(session_id: str) -> Optional[GameSession]:
    with Session(engine) as s:
        q = select(GameSession).where(GameSession.session_id == session_id)
        return s.exec(q).first()

def create_initial_village() -> dict:
    buildings = [
        {"name": "Townhall", "level": 1, "x": 512, "y": 200, "building_until": None},
        {"name": "Barracks", "level": 1, "x": 312, "y": 420, "building_until": None},
        {"name": "GoldMine", "level": 1, "x": 712, "y": 420, "building_until": None},
        {"name": "ElixirCollector", "level": 1, "x": 512, "y": 520, "building_until": None},
        {"name": "Walls", "level": 1, "x": 512, "y": 320, "building_until": None}
    ]
    heroes = []
    x = 150
    for faction, names in FACTIONS.items():
        heroes.append({"faction": faction, "name": random.choice(names), "level": 1, "x": x, "y": 650})
        x += 150
    return {"buildings": buildings, "heroes": heroes, "resources": {"gold": 1000, "elixir": 1000}, "build_queue": []}

def ensure_game_session(session_id: str, owner_id: Optional[int] = None) -> GameSession:
    gs = get_session_by_sid(session_id)
    if gs is None:
        gs = GameSession(session_id=session_id, owner_id=owner_id, data={"village": create_initial_village(), "story": [f"Session {session_id} created."]})
        with Session(engine) as s:
            s.add(gs); s.commit(); s.refresh(gs)
    return gs

def save_game_session(gs: GameSession):
    gs.updated_at = time.time()
    with Session(engine) as s:
        s.add(gs); s.commit()

# ---- Pydantic request models
class ActionRequest(BaseModel):
    session_id: str
    action: str
    params: Dict = {}

# ---- Auth endpoints
@app.post("/register")
def register(form: OAuth2PasswordRequestForm = Depends()):
    username = form.username
    password = form.password
    if get_user_by_username(username):
        raise HTTPException(status_code=400, detail="Username already taken")
    user = User(username=username, hashed_password=hash_password(password))
    with Session(engine) as s:
        s.add(user); s.commit(); s.refresh(user)
    token = create_token({"sub": username})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_username(form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

def get_current_user(request: Request) -> Optional[User]:
    auth = request.headers.get("Authorization")
    if not auth:
        return None
    try:
        scheme, token = auth.split()
        payload = decode_token(token)
        username = payload.get("sub")
        return get_user_by_username(username)
    except Exception:
        return None

# ---- Core game endpoints
@app.post("/action")
async def action(req: ActionRequest, request: Request):
    # identify user (optional)
    user = get_current_user(request)
    gs = ensure_game_session(req.session_id, owner_id=(user.id if user else None))
    data = gs.data
    village = data.get("village", {})
    story = data.setdefault("story", [])

    # process build queue (apply finished)
    now = time.time()
    new_queue = []
    for item in village.get("build_queue", []):
        if item.get("finish_at", 0) <= now:
            # apply upgrade
            name = item["name"]
            found = False
            for b in village.get("buildings", []):
                if b["name"] == name:
                    b["level"] += 1
                    b["building_until"] = None
                    found = True
                    break
            if not found:
                village.setdefault("buildings", []).append({"name": name, "level": 1, "x": 400, "y": 400, "building_until": None})
            story.append(f"Construction de {name} terminée.")
        else:
            new_queue.append(item)
    village["build_queue"] = new_queue

    # handle actions
    if req.action == "get_status":
        gs.data = data; save_game_session(gs)
        return {"village": village, "story": story}

    if req.action == "build":
        bld = req.params.get("building")
        if bld not in BUILDINGS:
            raise HTTPException(400, "Bâtiment inconnu")
        cost = 200 + random.randint(0, 150)
        if village["resources"]["gold"] < cost:
            raise HTTPException(400, "Pas assez d'or")
        village["resources"]["gold"] -= cost
        duration = 6 + random.randint(0, 10)
        finish_at = time.time() + duration
        village.setdefault("build_queue", []).append({"name": bld, "finish_at": finish_at, "action": "upgrade"})
        story.append(f"Construction démarrée : {bld}. Fin en {duration}s. (-{cost} gold)")
        gs.data = data; save_game_session(gs)
        return {"message": "Construction lancée", "village": village}

    if req.action == "train_hero":
        faction = req.params.get("faction")
        if faction not in FACTIONS:
            raise HTTPException(400, "Faction inconnue")
        cost = 300
        if village["resources"]["elixir"] < cost:
            raise HTTPException(400, "Pas assez d'élixir")
        village["resources"]["elixir"] -= cost
        name = random.choice(FACTIONS[faction])
        new_hero = {"faction": faction, "name": name, "level": 1, "x": random.randint(100, 900), "y": random.randint(600, 720)}
        village.setdefault("heroes", []).append(new_hero)
        story.append(f"Héros {name} entraîné ({faction}). -{cost} elixir")
        gs.data = data; save_game_session(gs)
        return {"message": f"Héros {name} entraîné", "village": village}

    if req.action == "raid":
        enemy_power = random.randint(500, 1500)
        my_power = sum(h.get("level", 1) * random.randint(80, 160) for h in village.get("heroes", []))
        if my_power >= enemy_power:
            reward = random.randint(200, 800)
            village["resources"]["gold"] += reward
            summary = f"Raid réussi: {my_power} vs {enemy_power}. +{reward} gold"
            success = True
        else:
            if village.get("heroes"):
                loss = random.choice(village["heroes"])
                loss["level"] = max(1, loss.get("level", 1) - 1)
                summary = f"Raid échoué: {my_power} vs {enemy_power}. {loss['name']} blessé."
            else:
                summary = f"Raid échoué: {my_power} vs {enemy_power}."
            success = False
        story.append(summary)
        gs.data = data; save_game_session(gs)
        return {"result": {"success": success, "summary": summary}, "village": village}

    raise HTTPException(400, "Action inconnue")


# ---- export / import endpoints (auth optional but available) ----
@app.get("/export/{session_id}")
def export_session(session_id: str, request: Request):
    user = get_current_user(request)
    gs = get_session_by_sid(session_id)
    if not gs:
        raise HTTPException(404, "Session introuvable")
    # si appartient à un user, vérifier droit
    if gs.owner_id and user and gs.owner_id != user.id:
        raise HTTPException(403, "Pas le droit")
    return gs.data

@app.post("/import/{session_id}")
def import_session(session_id: str, payload: dict, request: Request):
    user = get_current_user(request)
    gs = get_session_by_sid(session_id)
    if gs and gs.owner_id and user and gs.owner_id != user.id:
        raise HTTPException(403, "Pas le droit")
    if not gs:
        gs = GameSession(session_id=session_id, owner_id=(user.id if user else None), data=payload)
        with Session(engine) as s:
            s.add(gs); s.commit(); s.refresh(gs)
    else:
        gs.data = payload; save_game_session(gs)
    return {"ok": True}


# ---- static files served from current dir (index.html...) ----
app.mount("/", StaticFiles(directory=".", html=True), name="static")
print('Hello')