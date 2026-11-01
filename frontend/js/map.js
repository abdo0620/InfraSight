// Danger zone drawing, shared by the main map (js/mapview.js) and the ticket's "Danger and zone" tab.
// Zones are organic polygons (irregular, like a real spread of danger), filled with stacked semi-transparent layers
// that go from yellow at the edge (moderate) through orange to deep red at the core (severe). The higher the level,
// the further the ramp goes. Shapes are seeded by position, so a zone keeps the same shape at every redraw.
(function(){
const RAMP=[[0,[250,204,21]],[.5,[249,115,22]],[.8,[220,38,38]],[1,[127,29,29]]];   // yellow, orange, red, deep red
const DEPTH=[0,.15,.35,.6,.85,1];          // how far into the ramp the core goes, per level 1-5
const SHELLS=[1,.8,.62,.45,.3];            // size of each layer, outer to inner
const ramp=t=>{let i=1;while(i<RAMP.length-1&&t>RAMP[i][0])i++;const[a,ca]=RAMP[i-1],[b,cb]=RAMP[i],k=(t-a)/(b-a||1);
  return "rgb("+ca.map((v,j)=>Math.round(v+(cb[j]-v)*k)).join(",")+")"};
// seeded random numbers: same seed, same shape
const rng=seed=>{let h=1779033703;for(const c of String(seed))h=Math.imul(h^c.charCodeAt(0),3432918353);
  return()=>{h=Math.imul(h^h>>>16,2246822507);h=Math.imul(h^h>>>13,3266489909);return((h^=h>>>16)>>>0)/4294967296}};
// local metres <-> lat/lng around a reference point
const frame=(lat0,lng0)=>{const ky=111320,kx=111320*Math.cos(lat0*Math.PI/180);
  return{xy:p=>[(p[1]-lng0)*kx,(p[0]-lat0)*ky],ll:q=>[lat0+q[1]/ky,lng0+q[0]/kx]}};
// wavy factor around 1: a few sine waves with random phases
const waves=(r,amps)=>{const ph=amps.map(()=>r()*6.283),fr=amps.map((_,i)=>[2,3,5,7,11][i]);return x=>1+amps.reduce((s,a,i)=>s+a*Math.sin(fr[i]*x+ph[i]),0)};

// blob around a point: radius r (m), irregularity 0-1, scaled by s, drifting towards (dx, dy) for inner layers
function blob(f,r,irr,rnd,s,drift){const w=waves(rnd,[.13,.09,.06,.04,.025].map(a=>a*irr)),n=56,out=[];
  for(let i=0;i<n;i++){const a=i/n*6.283,k=Math.max(.55,w(a))*r*s;out.push(f.ll([drift[0]*(1-s)+Math.cos(a)*k,drift[1]*(1-s)+Math.sin(a)*k]))}return out}

// corridor along a street piece: half-width varies along the street, rounded ends
function corridor(f,line,half,rnd,s){const P=line.map(f.xy),pts=[];
  for(let i=0;i<P.length-1;i++){const[a,b]=[P[i],P[i+1]],d=Math.hypot(b[0]-a[0],b[1]-a[1]),n=Math.max(1,Math.ceil(d/6));
    for(let j=0;j<n;j++)pts.push([a[0]+(b[0]-a[0])*j/n,a[1]+(b[1]-a[1])*j/n])}
  pts.push(P[P.length-1]);if(pts.length<2)return null;
  const p1=rnd()*6.283,p2=rnd()*6.283;let dist=0;const L=[],R=[],W=[];
  pts.forEach((p,i)=>{if(i)dist+=Math.hypot(p[0]-pts[i-1][0],p[1]-pts[i-1][1]);
    const q=pts[Math.min(i+1,pts.length-1)],o=pts[Math.max(i-1,0)],tx=q[0]-o[0],ty=q[1]-o[1],tl=Math.hypot(tx,ty)||1,
      w=half*s*Math.max(.5,1+.32*Math.sin(dist/23+p1)+.18*Math.sin(dist/8+p2));
    W.push(w);L.push([p[0]-ty/tl*w,p[1]+tx/tl*w]);R.push([p[0]+ty/tl*w,p[1]-tx/tl*w])});
  const cap=(c,from,w)=>{const out=[];for(let k=1;k<8;k++){const a=from-k/8*Math.PI;out.push([c[0]+Math.cos(a)*w,c[1]+Math.sin(a)*w])}return out};
  const ang=(a,b)=>Math.atan2(b[1]-a[1],b[0]-a[0]),e=pts.length-1;
  return[...L,...cap(pts[e],ang(pts[e],L[e]),W[e]),...R.reverse(),...cap(pts[0],ang(pts[0],R[R.length-1]),W[0])].map(f.ll)}

// stacked layers: outer layer with the edge line, inner layers deeper in the ramp
function layers(ringsAt,level,blocked){const depth=Math.max(DEPTH[level]||.6,blocked?.85:0),g=L.featureGroup();
  SHELLS.forEach((s,i)=>{const col=ramp(depth*i/(SHELLS.length-1));
    ringsAt(s).forEach(ring=>ring&&L.polygon(ring,i?{stroke:false,fillColor:col,fillOpacity:.1+.045*i,interactive:false}
      :{color:ramp(Math.min(depth,.5)),weight:1.5,opacity:.9,fillColor:col,fillOpacity:.13}).addTo(g))});
  return g}

window.drawZone=function(z,lat,lng){
  const f=frame(lat,lng),seed=lat.toFixed(5)+","+lng.toFixed(5),lines=z.shape==="street"&&z.street&&z.street.lines;
  let g;
  if(lines)g=layers(s=>{const rnd=rng(seed);return lines.map(l=>corridor(f,l,14,rnd,s))},z.level,z.blocked);
  else{const area=z.shape==="area",r0=rng(seed+"d"),a=r0()*6.283,drift=[Math.cos(a)*z.radius_m*.25,Math.sin(a)*z.radius_m*.25];
    g=layers(s=>[blob(f,z.radius_m,area?1:.6,rng(seed),s,drift)],z.level,z.blocked)}
  return g.addLayer(L.circleMarker([lat,lng],{radius:4,color:"#fff",weight:2,fillColor:ramp(DEPTH[z.level]||.6),fillOpacity:1}))};

// hand-drawn zone: smooth the clicked points, make the outline irregular, same colour layers
window.drawOrganicPolygon=function(points,level,seed){
  let P=points.map(p=>[p[0],p[1]]);
  for(let k=0;k<3;k++)P=P.flatMap((p,i)=>{const q=P[(i+1)%P.length];return[[.75*p[0]+.25*q[0],.75*p[1]+.25*q[1]],[.25*p[0]+.75*q[0],.25*p[1]+.75*q[1]]]});
  const c=[P.reduce((s,p)=>s+p[0],0)/P.length,P.reduce((s,p)=>s+p[1],0)/P.length],f=frame(c[0],c[1]),
    Q=P.map(f.xy),w=waves(rng(seed),[.06,.045,.03,.02,.012]);
  return layers(s=>[Q.map(q=>{const k=w(Math.atan2(q[1],q[0]))*s;return f.ll([q[0]*k,q[1]*k])})],level,false)};

// organic outline around a point, for other zones on the map (hotspots)
window.organicRing=(lat,lng,r,seed)=>blob(frame(lat,lng),r,.8,rng(seed),1,[0,0]);

let zoneMap=null;
const DETOUR={color:"#6ea8fe",weight:5,opacity:.9,dashArray:"8 6"};   // detour around a blocked street
window.DETOUR_STYLE=DETOUR;
window.renderZoneMap=function(el,z){
  if(zoneMap){zoneMap.stop();zoneMap.remove();zoneMap=null}
  if(typeof L==="undefined"||z.lat==null){el.innerHTML='<p class="mu" style="padding:12px">No map position for this report.</p>';return}
  el.style.height="260px";
  zoneMap=L.map(el,{zoomControl:false,attributionControl:false,zoomAnimation:false,fadeAnimation:false,markerZoomAnimation:false});  // no animation: the tab is redrawn often
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,subdomains:["a","b","c"]}).addTo(zoneMap);
  zoneMap.setView([z.lat,z.lng],17);
  const layer=window.drawZone(z,z.lat,z.lng).addTo(zoneMap),b=layer.getBounds();
  if(z.detour)b.extend(L.polyline(z.detour,DETOUR).addTo(zoneMap).getBounds());
  zoneMap.fitBounds(b.pad(.2),{maxZoom:18,animate:false});
};
})();
