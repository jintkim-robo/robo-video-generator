# per-subtitle-line TTS; speech end taken from edge-tts boundaries, audio trimmed to it
import json,asyncio,subprocess,os,edge_tts
CFG=json.load(open(os.environ.get('RVG_CONFIG','config.json')))
S=json.load(open('script.json')); TAIL=0.12
async def one(text,path):
    c=edge_tts.Communicate(text,CFG['voice'],rate=CFG['rate'],boundary='WordBoundary'); end=0
    with open(path+'.raw.mp3','wb') as f:
        async for ch in c.stream():
            if ch['type']=='audio': f.write(ch['data'])
            elif 'Boundary' in ch['type']: end=max(end,(ch['offset']+ch['duration'])/1e7)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',path+'.raw.mp3','-af',f'atrim=0:{end+TAIL},apad=whole_dur={end+TAIL}','-ar','44100','-ac','1',path],check=True)
    return end+TAIL
async def main():
    T=[]
    for i,s in enumerate(S):
        row=[]
        for j,l in enumerate(s['lines']):
            row.append(await one(l.get('tts',l['sub']),f'a{i}_{j}.wav'))
        T.append(row)
    json.dump(T,open('durs.json','w')); print(T, sum(map(sum,T)))
asyncio.run(main())
