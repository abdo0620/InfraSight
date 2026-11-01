// Client for the InfraSight backend: login token and ticket actions. All AI prompts run on the server.
(function(){
// Same server as the page (the backend serves both, see start.bat). If the page comes from another server
// (VS Code Live Server, a file), fall back to the backend on port 8000. Set window.INFRASIGHT_API to force one.
const BACKEND="http://localhost:8000/api",TK="infrasight.token";
let API=window.INFRASIGHT_API||(location.protocol=="file:"?BACKEND:location.origin+"/api"),ORIGIN=API.replace(/\/api$/,"");
let token=null;try{token=localStorage.getItem(TK)}catch(e){}
const keep=t=>{token=t;try{t?localStorage.setItem(TK,t):localStorage.removeItem(TK)}catch(e){}};
const detail=(j,s)=>typeof j.detail=="string"?j.detail:Array.isArray(j.detail)?j.detail.map(d=>d.msg).join(". "):"Request failed ("+s+")";
async function call(method,path,body){const h={};if(token)h.Authorization="Bearer "+token;let b=body;
if(body&&!(body instanceof FormData)){h["Content-Type"]="application/json";b=JSON.stringify(body)}
let r;try{r=await fetch(API+path,{method,headers:h,body:b})}catch(e){throw{status:0,message:"The InfraSight server cannot be reached. Try again in a moment."}}
if(path=="/meta"&&r.status==404&&API!=BACKEND&&!window.INFRASIGHT_API){API=BACKEND;ORIGIN=API.replace(/\/api$/,"");return call(method,path,body)}  // page not served by the backend
if(r.status==401&&token&&!path.startsWith("/auth/login")){keep(null);location.reload()}
const j=(r.headers.get("content-type")||"").includes("json")?await r.json():await r.text();
if(!r.ok)throw{status:r.status,message:detail(j,r.status)};return j}
const abs=u=>u&&u[0]=="/"?ORIGIN+u:u;   // photo links are relative to the backend
const fix=t=>{t.img=abs(t.img);t.zone_img=abs(t.zone_img);t.preview_img=abs(t.preview_img);if(t.after)t.after.img=abs(t.after.img);(t.log||[]).forEach(l=>l.img=abs(l.img));return t};
const auth=async p=>{const j=await p;keep(j.token);return j.user};
window.CF={get API(){return API},
signedIn:()=>!!token,
login:(username,password)=>auth(call("POST","/auth/login",{username,password})),
register:(username,name,password,lang)=>auth(call("POST","/auth/register",{username,name,password,lang})),
setLang:lang=>call("PUT","/auth/me",{lang}),
logout:()=>keep(null),
me:()=>call("GET","/auth/me"),
meta:()=>call("GET","/meta"),
state:async()=>{const j=await call("GET","/state");j.tickets.forEach(fix);return j},
create:async fd=>{const j=await call("POST","/tickets",fd);fix(j.ticket);return j},
report:ref=>call("POST",`/tickets/${ref}/report`).then(fix),
assist:(ref,i)=>call("POST",`/tickets/${ref}/stages/${i}/assist`).then(fix),
check:(ref,stage,item,done)=>call("PUT",`/tickets/${ref}/checklist`,{stage,item,done}).then(fix),
advance:ref=>call("POST",`/tickets/${ref}/advance`).then(fix),
applySev:ref=>call("POST",`/tickets/${ref}/apply-severity`).then(fix),
reportHtml:ref=>call("GET",`/tickets/${ref}/report.html`),
saveZones:z=>call("PUT","/zones",z),
merge:(ref,into)=>call("POST",`/tickets/${ref}/merge`,{into}).then(fix),
damage:ref=>call("POST",`/tickets/${ref}/damage`).then(fix),
afterPhoto:(ref,file)=>{const fd=new FormData();fd.append("image",file);return call("POST",`/tickets/${ref}/after-photo`,fd).then(fix)},
detour:ref=>call("POST",`/tickets/${ref}/detour`).then(fix),
preview:ref=>call("POST",`/tickets/${ref}/preview`).then(fix),
one:ref=>call("GET",`/tickets/${ref}`).then(fix),
hotspots:()=>call("GET","/hotspots"),
forecast:()=>call("POST","/hotspots/forecast"),
brief:()=>call("GET","/brief"),
makeBrief:()=>call("POST","/brief"),
notes:()=>call("GET","/notifications"),
readNotes:()=>call("POST","/notifications/read"),
download:(filename,data)=>{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([data],{type:"text/html"}));a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000)}};
})();
