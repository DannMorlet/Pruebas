"""Backend Unsloth: argumentos verificables sin instalar ML ni cargar GPU."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from workers.train_lora import validate_backend, load_unsloth_model, import_unsloth_safely


class FakeFastLanguageModel:
    loaded = None
    adapter = None

    @classmethod
    def from_pretrained(cls, **kwargs):
        cls.loaded = kwargs
        return object(), FakeTokenizer()

    @classmethod
    def get_peft_model(cls, model, **kwargs):
        cls.adapter = kwargs
        return model


class FakeTokenizer:
    pass


class BackendTests(unittest.TestCase):
    def test_compatibilidad_recetas_anteriores(self):
        self.assertEqual(validate_backend({}), "trl")
        self.assertEqual(validate_backend({"backend":"trl","checkpoint_interval":25}),"trl")

    def test_rechaza_backend_desconocido(self):
        with self.assertRaises(ValueError):
            validate_backend({"backend":"otro"})

    def test_unsloth_sin_checkpoints(self):
        self.assertEqual(validate_backend({"backend":"unsloth","checkpoint_interval":0}),"unsloth")
        for cfg in (
            {"backend":"unsloth","checkpoint_interval":25},
            {"backend":"unsloth","resume_checkpoint":"checkpoint-25"},
        ):
            with self.subTest(cfg=cfg), self.assertRaisesRegex(ValueError,"checkpoints"):
                validate_backend(cfg)

    def test_carga_lora_y_qlora_sin_duplicar_peft(self):
        for qlora in (False,True):
            with self.subTest(qlora=qlora):
                model,tok=load_unsloth_model("Qwen/Qwen3-0.6B",8,qlora,FakeFastLanguageModel)
                self.assertEqual(FakeFastLanguageModel.loaded["load_in_4bit"],qlora)
                self.assertEqual(FakeFastLanguageModel.loaded["max_seq_length"],256)
                self.assertEqual(FakeFastLanguageModel.adapter["r"],8)
                self.assertEqual(FakeFastLanguageModel.adapter["lora_alpha"],16)
                self.assertEqual(FakeFastLanguageModel.adapter["use_gradient_checkpointing"],"unsloth")
                self.assertIsInstance(tok,FakeTokenizer)

    def test_importacion_unsloth_correcta(self):
        class Modulo:
            FastLanguageModel = FakeFastLanguageModel
        modelo, fallo = import_unsloth_safely(lambda nombre: Modulo if nombre == "unsloth" else None)
        self.assertIs(modelo, FakeFastLanguageModel)
        self.assertFalse(fallo)

    def test_importacion_unsloth_fallida_sin_filtrar_rutas(self):
        def importar(_nombre):
            raise RuntimeError("C:/datos-privados/modelo/secreto.bin")
        modelo, fallo = import_unsloth_safely(importar)
        self.assertIsNone(modelo)
        self.assertTrue(fallo)

    def test_valida_argumentos_sin_descargas(self):
        for model,rank,qlora in (("",8,False),("x",0,False),("x",129,False),("x",8,"sí")):
            with self.subTest(model=model,rank=rank,qlora=qlora):
                with self.assertRaises(ValueError):
                    load_unsloth_model(model,rank,qlora,FakeFastLanguageModel)
