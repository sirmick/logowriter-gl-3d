// Compiles and runs every playlist program headless, with rendering stubbed out.
// Reports segment count, peak turtle count, approximate run time at screensaver speed, and 3D bounds.
import fs from 'fs';
const html=fs.readFileSync(new URL('../index.html',import.meta.url),'utf8');
const core=html.split('//<core3d>')[1].split('//</core3d>')[0];
const stub=`const GL={total:0,bb:[],seg(x0,y0,z0,x1,y1,z1){this.total++;const b=this.bb;for(const p of [[x0,y0,z0],[x1,y1,z1]])for(let k=0;k<3;k++){if(!(p[k]>=b[k]))b[k]=p[k];if(!(p[k]<=b[k+3]))b[k+3]=p[k]}},clear(){this.total=0;this.bb=[]}};`;
const X=new Function(stub+core+'return {R,GL,PROGRAMS,resetWorld,loadProgram,startTask,step}')();
const {R,GL}=X;let fail=0;
for(const p of X.PROGRAMS){
  try{
    X.resetWorld();X.loadProgram(p.src);X.startTask('STARTUP');
    let frames=0,maxT=0;const b=Math.max(1,Math.floor(p.speed));
    while(R.tasks.length&&frames<200000){R.frameNo=frames;R.k=0;for(const t of R.tasks)X.step(t,b);R.tasks=R.tasks.filter(t=>!t.done);R.turtles=R.turtles.filter(T=>T.alive);maxT=Math.max(maxT,R.turtles.length);frames++}
    const sec=(p.speed<1?frames/p.speed:frames)/60;
    console.log(p.name.padEnd(24),'segs',String(GL.total).padStart(7),'maxT',String(maxT).padStart(5),'~sec',sec.toFixed(1).padStart(6),'bb',GL.bb.map(Math.round).join(','));
  }catch(e){fail++;console.log(p.name,'ERROR line',e.line,e.message)}
}
process.exit(fail?1:0);
