"""Pruebas de generación con servidor HTTP falso, sin CUDA ni red externa."""
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import sys
import tempfile
import threading
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fresita_predict import generate_predictions,local_server,read_cases
from fresita_quality import evaluate_predictions

class LocalHandler(BaseHTTPRequestHandler):
    requests=[]
    status=200
    response_body={"choices":[{"message":{"content":"¡Qué onda!"}}]}
    def do_POST(self):
        raw=self.rfile.read(int(self.headers["Content-Length"]))
        self.__class__.requests.append((self.path,json.loads(raw)))
        body=json.dumps(self.__class__.response_body).encode("utf-8")
        self.send_response(self.__class__.status)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self,*_):pass

class PredictTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)
        self.dataset=self.root/"casos.jsonl"
        self.dataset.write_text(json.dumps({"categoria":"es_mx","pregunta":"Saluda en México",
            "referencia":"SECRETO-REFERENCIA"},ensure_ascii=False)+"\n",encoding="utf-8")
        LocalHandler.requests=[]
        LocalHandler.status=200
        LocalHandler.response_body={"choices":[{"message":{"content":"¡Qué onda!"}}]}
        self.server=ThreadingHTTPServer(("127.0.0.1",0),LocalHandler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.endpoint=f"http://127.0.0.1:{self.server.server_port}/v1"
    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.tmp.cleanup()
    def test_endpoint_bloquea_red_remota(self):
        for url in ("https://127.0.0.1:1234/v1","http://localhost:1234/v1",
                    "http://192.168.1.3:1234/v1","http://127.0.0.1:1234/v1/otro",
                    "http://127.0.0.1:1234/v1?x=1","http://usuario@127.0.0.1:1234/v1"):
            with self.subTest(url=url),self.assertRaises(ValueError):local_server(url)
    def test_predicciones_y_evaluacion_real(self):
        output,info=generate_predictions(self.dataset,self.root/"salida",
                                          endpoint=self.endpoint,model="modelo-local")
        self.assertEqual(info["ejemplos"],1)
        self.assertTrue(output.is_file())
        self.assertEqual(evaluate_predictions(output)["ejemplos_validos"],1)
        self.assertEqual(LocalHandler.requests[0][0],"/v1/chat/completions")
        sent=json.dumps(LocalHandler.requests[0][1],ensure_ascii=False)
        self.assertIn("Saluda en México",sent)
        self.assertNotIn("SECRETO-REFERENCIA",sent)
        self.assertEqual(LocalHandler.requests[0][1]["temperature"],0)
    def test_sin_ejecucion_implicita(self):
        self.assertEqual(len(LocalHandler.requests),0)
        self.assertEqual(len(read_cases(self.dataset)),1)
        self.assertEqual(len(LocalHandler.requests),0)
    def test_cancelar_sin_archivo_parcial(self):
        with self.assertRaises(InterruptedError):
            generate_predictions(self.dataset,self.root/"salida",endpoint=self.endpoint,
                                 model="modelo",cancelled=lambda:True)
        self.assertEqual(list((self.root/"salida").iterdir()),[])
        self.assertEqual(len(LocalHandler.requests),0)
    def test_error_http_no_deja_resultados(self):
        LocalHandler.status=503
        with self.assertRaisesRegex(ValueError,"HTTP 503"):
            generate_predictions(self.dataset,self.root/"salida",endpoint=self.endpoint,model="modelo")
        self.assertEqual(list((self.root/"salida").iterdir()),[])
    def test_respuesta_invalida(self):
        LocalHandler.response_body={"choices":[]}
        with self.assertRaisesRegex(ValueError,"incompatible"):
            generate_predictions(self.dataset,self.root/"salida",endpoint=self.endpoint,model="modelo")
    def test_rechaza_filas_incompletas(self):
        self.dataset.write_text('{"pregunta":"hola"}\n',encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"línea 1"):read_cases(self.dataset)
    def test_rechaza_lote_grande(self):
        line=self.dataset.read_text(encoding="utf-8")
        self.dataset.write_text(line*101,encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"100"):read_cases(self.dataset)
    def test_sin_sobrescritura(self):
        a,_=generate_predictions(self.dataset,self.root/"salida",endpoint=self.endpoint,model="modelo")
        b,_=generate_predictions(self.dataset,self.root/"salida",endpoint=self.endpoint,model="modelo")
        self.assertNotEqual(a,b)
        self.assertTrue(a.exists() and b.exists())
    def test_parametros_limitados(self):
        with self.assertRaisesRegex(ValueError,"max_tokens"):
            generate_predictions(self.dataset,self.root/"salida",endpoint=self.endpoint,
                                 model="modelo",max_tokens=9000)
        self.assertEqual(LocalHandler.requests,[])
