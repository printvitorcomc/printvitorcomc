// Render frames with librsvg and encode the loop as a browser-native animation.
// npm install --no-save sharp@0.35.5
const fs = require('node:fs/promises');
const path = require('node:path');
const sharp = require(process.env.ASCII_SHARP_MODULE || 'sharp');
const root = path.resolve(__dirname, '..');
sharp.concurrency(2);
sharp.cache(false);

// Canonicalise colours that become noisy when antialiased, low-alpha SVG
// pixels are unpremultiplied. The artwork itself only uses these two inks.
function canonicalise(pixels, theme) {
  const ink=theme==='dark'?[230,237,243]:[23,23,23];
  const field=theme==='dark'?[53,64,76]:[195,202,209];
  for(let p=0;p<pixels.length;p+=4){
    const a=pixels[p+3];
    if(!a){pixels[p]=pixels[p+1]=pixels[p+2]=0;continue;}
    let di=0,df=0;
    for(let k=0;k<3;k++){di+=(pixels[p+k]-ink[k])**2;df+=(pixels[p+k]-field[k])**2;}
    const colour=di<df?ink:field;
    const alpha=Math.min(255,Math.round(a/4)*4);
    for(let k=0;k<3;k++)pixels[p+k]=alpha?colour[k]:0;
    pixels[p+3]=alpha;
  }
  return pixels;
}

async function main() {
  const timing = JSON.parse(await fs.readFile(path.join(root, '.ascii-frames/timing.json')));
  const { width, height } = timing;
  // The source knot updates at 16 FPS; glyph textures update at 8 FPS.
  // Keep both cadences and the exact ten-second loop.
  const fps=16, stride=timing.fps/fps, count=timing.count/stride;
  const delay=Array.from({length:count},(_,i)=>Math.round((i+1)*1000/fps)-Math.round(i*1000/fps));
  const raw = { width, height: height * count, channels: 4, pageHeight: height };
  for (const theme of ['dark', 'light']) {
    const folder = path.join(root, '.ascii-frames', theme);
    const rgbaPath = path.join(root, '.ascii-frames', `${theme}.rgba`);
    let pixels;
    try { pixels = await fs.readFile(rgbaPath); } catch {
      const frames = [];
      for (let i = 0; i < timing.count; i++) {
        frames.push(await sharp(path.join(folder, `${String(i).padStart(4, '0')}.svg`)).ensureAlpha().raw().toBuffer());
        if (i % 80 === 0) console.log(`${theme}: rendered ${i}/${timing.count}`);
      }
      pixels = Buffer.concat(frames);
      await fs.writeFile(rgbaPath, pixels);
    }
    const frameBytes=width*height*4;
    pixels=canonicalise(Buffer.concat(Array.from({length:count},(_,i)=>pixels.subarray(i*stride*frameBytes,(i*stride+1)*frameBytes))),theme);
    const out = path.join(root, 'assets', `ascii-profile-${theme}`);
    console.log(`${theme}: encoding WebP`);
    await sharp(pixels, {raw}).webp({lossless:true, effort:4, loop:0, delay, minSize:true}).toFile(out+'.webp');
    const still=canonicalise(await sharp(path.join(folder,'still.svg')).ensureAlpha().raw().toBuffer(),theme);
    await sharp(still,{raw:{width,height,channels:4}}).webp({lossless:true,effort:4}).toFile(out+'-still.webp');
    if (theme === 'dark' && process.argv.includes('--compare')) {
      console.log('Encoding GIF comparison');
      await fs.mkdir(path.join(root,'previews'),{recursive:true});
      const gifDelay=delay.map((_,i)=>10*(Math.round((i+1)*100/fps)-Math.round(i*100/fps)));
      await sharp(pixels,{raw}).flatten({background:'#0d1117'}).gif({loop:0,delay:gifDelay,colours:64,dither:0,effort:5}).toFile(path.join(root,'previews','comparison.gif'));
    }
    console.log(JSON.stringify({theme,bytes:(await fs.stat(out+'.webp')).size}));
  }
}
main().catch(error => { console.error(error); process.exitCode=1; });
