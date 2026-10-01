"""Serveur de préparation local : supports et proxy limité à health/ask."""
from __future__ import annotations

import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OUT = Path(__file__).resolve().parents[2] / 'outputs'


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control','no-store')
        super().end_headers()

    def json_response(self, code, payload):
        body=json.dumps(payload,ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path=='/':
            self.send_response(302);self.send_header('Location','/guide-soutenance-openagenda-rag.html');self.end_headers();return
        if self.path=='/api/health':
            return self.proxy('GET','/health')
        if self.path.startswith('/api/'):
            return self.json_response(404,{'detail':'Route non disponible dans le serveur de préparation.'})
        return super().do_GET()

    def do_POST(self):
        if self.path!='/api/ask':
            return self.json_response(404,{'detail':'Seul /api/ask est disponible.'})
        try:
            length=int(self.headers.get('Content-Length','0'))
            if not 0<length<=16000:
                raise ValueError()
            payload=json.loads(self.rfile.read(length))
            question=payload.get('question')
            if not isinstance(question,str) or not question.strip():
                raise ValueError()
        except (ValueError,TypeError,AttributeError):
            return self.json_response(400,{'detail':'Une question texte non vide est requise.'})
        return self.proxy('POST','/ask',{'question':question.strip()})

    def proxy(self,method,path,payload=None):
        data=json.dumps(payload).encode() if payload is not None else None
        request=Request('http://127.0.0.1:8000'+path,data=data,method=method,headers={'Content-Type':'application/json'})
        try:
            with urlopen(request,timeout=40) as response:
                return self.json_response(response.status,json.loads(response.read()))
        except HTTPError as exc:
            detail=exc.read().decode(errors='replace')
            if '429' in detail:
                message='Mistral signale une limite d’usage (429). L’API renvoie une indisponibilité contrôlée (503). Aucun résultat généré.'
            elif exc.code in (400,422):
                message='La requête a été refusée par la validation de l’API.'
            elif exc.code==503:
                message='L’API signale une indisponibilité de l’index ou du fournisseur Mistral.'
            else:
                message=f'L’API RAG renvoie une erreur HTTP {exc.code}. Aucun résultat généré.'
            return self.json_response(exc.code,{'detail':message})
        except (URLError,TimeoutError,ValueError):
            return self.json_response(503,{'detail':'L’API locale ne répond pas ou son délai est dépassé. Vérifier Docker et /health.'})


if __name__=='__main__':
    print('Guide : http://127.0.0.1:8765/guide-soutenance-openagenda-rag.html',flush=True)
    server=ThreadingHTTPServer(('127.0.0.1',8765),partial(Handler,directory=str(OUT)))
    server.serve_forever()
