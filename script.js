// script.js (amélioré)
let token = localStorage.getItem("token") || null;
const sessionId = localStorage.getItem("session_id") || generateSessionId();
if (!localStorage.getItem("session_id")) localStorage.setItem("session_id", sessionId);

function generateSessionId() { return 'sess-' + Math.random().toString(36).substr(2,9); }

async function apiFetch(path, method='POST', body=null){
    const headers = {"Content-Type":"application/json"};
    if (token) headers["Authorization"] = "Bearer " + token;
    const resp = await fetch(path, {method, headers, body: body ? JSON.stringify(body) : undefined});
    return resp.ok ? await resp.json() : await resp.json().then(j=>{throw j;});
}

async function sendAction(action, params={}){
    return await apiFetch("/action", "POST", {session_id: sessionId, action, params});
}

async function updateStatus(){
    try{
        const data = await sendAction("get_status");
        updateStory(data.story || []);
        updateResources(data.village.resources || {});
        updateBuildQueue(data.village.build_queue || []);
        updateHeroList(data.village.heroes || []);
        if (window.updateGameScene) window.updateGameScene(data.village);
    }catch(e){
        console.error(e);
        // show error quietly
    }
}

// auth helpers
async function register(username, password){
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);
    const res = await fetch("/register", {method:"POST", body: form});
    if (!res.ok) throw await res.json();
    const json = await res.json();
    token = json.access_token; localStorage.setItem("token", token);
}

async function login(username, password){
    const form = new URLSearchParams();
    form.append("username", username);
    form.append("password", password);
    const res = await fetch("/token", {method:"POST", body: form});
    if (!res.ok) throw await res.json();
    const json = await res.json();
    token = json.access_token; localStorage.setItem("token", token);
}

// existing functions for UI (build, trainHero, raid, updateStory...)
// copy from previous script.js provided earlier (updateStory, updateResources, updateBuildQueue, updateHeroList, build, trainHero, raid)

setInterval(updateStatus, 3000);
updateStatus();
