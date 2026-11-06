import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from unittest import mock
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import fresita_llama as llama

def asset(name, size=123):
    return {"name":name,"size":size,"digest":"sha256:"+"0"*64}
def release(tag="b12048"):
    return {"tag_name":tag,"assets":[
        asset(f"llama-{tag}-bin-win-cuda-13.4-x64.zip"),
        asset("cudart-llama-bin-win-cuda-13.4-x64.zip")]}
def make_zip(files):
    out=io.BytesIO()
    with zipfile.ZipFile(out,"w") as z:
        for path,data in files.items():
            z.writestr(path,data)
    out.seek(0)
    return out

class LlamaTests(unittest.TestCase):
    def test_latest_prefiere_compatible(self):
        found=llama.select_release([release("b12049") | {"assets":[]},release()])
        self.assertEqual(found["tag"],"b12048")
        self.assertEqual(len(found["assets"]),2)
    def test_no_acepta_digest_ausente(self):
        a=release()
        a["assets"][0].pop("digest")
        with self.assertRaises(ValueError):
            llama.select_release([a])
    def test_archivo_descarga_origen_ggml(self):
        self.assertTrue(llama.select_release([release()])["assets"][0]["url"].startswith(
            "https://github.com/ggml-org/llama.cpp/releases/download/b12048/"))
    def test_rechaza_zip_slip(self):
        with tempfile.TemporaryDirectory() as d:
            z=Path(d)/"t.zip"; z.write_bytes(make_zip({"../escape.txt":"mal"}).read())
            with self.assertRaises(ValueError):
                llama._extract_safe(z,Path(d)/"out")
            self.assertFalse((Path(d)/"escape.txt").exists())
    def test_descomprime_valido(self):
        with tempfile.TemporaryDirectory() as d:
            z=Path(d)/"t.zip";z.write_bytes(make_zip({"bin/test.txt":"bien"}).read())
            llama._extract_safe(z,Path(d)/"out")
            self.assertEqual((Path(d)/"out"/"bin"/"test.txt").read_text(),"bien")
    def test_selecciona_ultimo_instalado(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for tag in ("b12045","b12048"):
                folder=root/tag;folder.mkdir()
                (folder/"llama-server.exe").write_bytes(b"binario")
                (folder/"fresita_llama_manifest.json").write_text(
                    json.dumps({"llama_server":"llama-server.exe","tag":tag}))
            with mock.patch.object(llama,"_verify_pe64",return_value=None):
                result=llama.installed_server(root)
            self.assertEqual(result[1],"b12048")
    def test_arranque_usa_loopback_y_no_shell(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            exe=root/"llama-server.exe";exe.write_bytes(b"x")
            model=root/"model.gguf";model.write_bytes(b"GGUF")
            with mock.patch.object(llama,"_verify_pe64"):
                with mock.patch.object(llama.subprocess,"Popen") as popen:
                    llama.start_server(exe,model,8080)
            command=popen.call_args.args[0]
            self.assertEqual(command[command.index("--host")+1],"127.0.0.1")
            self.assertFalse(popen.call_args.kwargs.get("shell",False))
    def test_rechaza_otro_formato(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);exe=root/"llama-server.exe";exe.write_bytes(b"x")
            model=root/"other.bin";model.write_bytes(b"x")
            with mock.patch.object(llama,"_verify_pe64"):
                with self.assertRaises(ValueError):
                    llama.start_server(exe,model)
