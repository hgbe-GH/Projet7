import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {FileBlob, PresentationFile} from '@oai/artifact-tool';

const sourceDir=path.dirname(fileURLToPath(import.meta.url));
const root=path.resolve(sourceDir,'../..');
const workspace=path.join(root,'outputs','pptx-build');
await fs.mkdir(workspace,{recursive:true});
const map=JSON.parse(await fs.readFile(`${sourceDir}/template-frame-map.json`,'utf8'));
const data=JSON.parse(await fs.readFile(`${root}/outputs/contenu-soutenance.json`,'utf8'));
const deck=await PresentationFile.importPptx(await FileBlob.load(`${sourceDir}/template-original.pptx`));
const edits=[];
let cumulative=0;
for(let index=0;index<deck.slides.items.length;index++){
  const slide=deck.slides.items[index];
  for(const target of map.outputSlides[index].editTargets){
    const shape=slide.shapes.items.find(s=>String(s.text)===target.oldText && Math.abs(s.position.left-target.bbox[0])<.1 && Math.abs(s.position.top-target.bbox[1])<.1);
    if(!shape)throw new Error(`Missing inherited target slide ${index+1}: ${target.oldText}`);
    // The text setter persists imported text edits in the PPTX package.
    // replace() updated previews but left the original OOXML unchanged.
    shape.text=target.newText;
    if(target.textStyle)shape.text.style=target.textStyle;
    if(String(shape.text)!==target.newText)throw new Error(`Replacement failed slide ${index+1}`);
    edits.push({slide:index+1,oldText:target.oldText,newText:target.newText});
  }
  const d=data[index];const start=cumulative;cumulative+=d.seconds;
  const fmt=n=>`${String(Math.floor(n/60)).padStart(2,'0')}:${String(n%60).padStart(2,'0')}`;
  slide.speakerNotes.textFrame.setText(`${fmt(start)}–${fmt(cumulative)} (${d.seconds} s)

À LIRE
${d.speech}

À MONTRER
${d.show}

COMPRENDRE
${d.simple}

DÉTAIL TECHNIQUE
${d.technical}

PIÈGE
${d.pitfall}

PREUVE
${d.proof}

TRANSITION
${d.transition}`);
}
await fs.mkdir(`${workspace}/final-preview`,{recursive:true});
for(let index=0;index<deck.slides.items.length;index++){
  const slide=deck.slides.items[index];const stem=`slide-${String(index+1).padStart(2,'0')}`;
  const png=await deck.export({slide,format:'png',scale:1});
  await fs.writeFile(`${workspace}/final-preview/${stem}.png`,new Uint8Array(await png.arrayBuffer()));
  const layout=await slide.export({format:'layout'});
  await fs.writeFile(`${workspace}/final-preview/${stem}.layout.json`,await layout.text());
}
await fs.writeFile(`${workspace}/final-edits.json`,JSON.stringify(edits,null,2));
const pptx=await PresentationFile.exportPptx(deck);
await pptx.save(`${root}/outputs/openagenda-rag-soutenance.pptx`);
console.log(`12 slides edited, ${edits.length} text edits, 12 notes synchronized, ${cumulative} seconds.`);
