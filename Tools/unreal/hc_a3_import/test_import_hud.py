"""Offline importer guard tests. Uses a fake Unreal module; never opens Unreal."""
import builtins
from contextlib import redirect_stdout
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import types
import unittest
from unittest.mock import patch
import zlib

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("import_hud",HERE/"import_hud.py")
mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
MANIFEST=json.loads((HERE/"manifest.json").read_text())

class Object:
    def __init__(self): self.props={}
    def set_editor_property(self,k,v): self.props[k]=v
    def get_editor_property(self,k): return self.props[k]
class Texture(Object):
    def get_path_name(self): return self.path
class Task(Object):
    def get_objects(self): return self.objects

def fake_unreal(version="5.8.3-58210709+++UE5+Release-5.8",project=None,exists=False,unexpected=False):
    calls={"factories":0,"imports":[],"saves":[]}
    def factory():
        calls["factories"]+=1
        return Object()
    def import_tasks(tasks):
        calls["imports"].extend(tasks)
        for task in tasks:
            texture=Texture()
            texture.path=mod.DEST+"/"+task.props["destination_name"]+"."+task.props["destination_name"]
            task.objects=[texture]
            task.props["imported_object_paths"]=[texture.path if not unexpected else "/Game/Core/Unexpected.Unexpected"]
    def save(texture,only_if_is_dirty):
        calls["saves"].append(texture.get_path_name()); return True
    enum=lambda **items:types.SimpleNamespace(**items)
    u=types.SimpleNamespace(
        SystemLibrary=enum(get_engine_version=lambda:version),
        Paths=enum(get_project_file_path=lambda:project or str(mod.REPO/"CoopGame.uproject")),
        EditorAssetLibrary=enum(does_asset_exist=lambda path:exists,save_loaded_asset=save),
        TextureCompressionSettings=enum(TC_EDITOR_ICON=7),TextureGroup=enum(TEXTUREGROUP_UI=16),
        TextureMipGenSettings=enum(TMGS_NO_MIPMAPS=13),TextureAddress=enum(TA_CLAMP=1),
        TextureFilter=enum(TF_BILINEAR=1),TextureFactory=factory,AssetImportTask=Task,Texture2D=Texture,
        AssetToolsHelpers=enum(get_asset_tools=lambda:enum(import_asset_tasks=import_tasks)))
    return u,calls

class ImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.plan=mod.validate(MANIFEST)
    def test_default_no_unreal_import_or_repo_writes(self):
        snapshot=lambda:{str(p.relative_to(mod.REPO)):(p.stat().st_size,p.stat().st_mtime_ns)
                         for p in mod.REPO.rglob("*") if p.is_file()}
        before=snapshot(); original=builtins.__import__
        def guarded(name,*args,**kwargs):
            if name=="unreal": raise AssertionError("Default imported Unreal")
            return original(name,*args,**kwargs)
        output=io.StringIO()
        with patch("builtins.__import__",guarded),redirect_stdout(output):
            self.assertEqual(mod.main([]),0)
        result=json.loads(output.getvalue())
        self.assertEqual(result["mode"],"dry-run"); self.assertFalse(result["writes_performed"])
        self.assertEqual(len(result["proposed_imports"]),3); self.assertEqual(before,snapshot())
    def test_sources_match_pr_and_real_transparency(self):
        for p in self.plan:
            self.assertEqual(p["sha256"],mod.HASHES[p["name"]])
            self.assertEqual(p["alpha_range"],[0,255]); self.assertEqual(p["max_edge_alpha"],0)
    def test_manifest_source_escape_rejected(self):
        m=copy.deepcopy(MANIFEST); m["assets"][0]["source"]="../../secret.png"
        with self.assertRaisesRegex(ValueError,"Source path"): mod.validate(m)
    def test_manifest_core_destination_rejected(self):
        m=copy.deepcopy(MANIFEST); m["assets"][0]["destination_path"]="/Game/Core"
        with self.assertRaisesRegex(ValueError,"destination"): mod.validate(m)
    def test_manifest_hash_change_rejected(self):
        m=copy.deepcopy(MANIFEST); m["assets"][0]["sha256"]="0"*64
        with self.assertRaisesRegex(ValueError,"Manifest hash"): mod.validate(m)
    def test_extra_asset_rejected(self):
        m=copy.deepcopy(MANIFEST); m["assets"].append(copy.deepcopy(m["assets"][0]))
        with self.assertRaisesRegex(ValueError,"exactly 3"): mod.validate(m)
    def test_alpha_discard_settings_rejected(self):
        m=copy.deepcopy(MANIFEST); m["texture_settings"]["compression_no_alpha"]=True
        with self.assertRaisesRegex(ValueError,"settings"): mod.validate(m)
    def test_corrupted_png_rejected(self):
        data=bytearray(Path(self.plan[0]["source"]).read_bytes()); data[30]^=1
        with self.assertRaisesRegex(ValueError,"CRC"): mod.png_alpha(bytes(data))
    def test_rgb_png_without_alpha_rejected(self):
        def chunk(tag,data):
            return struct.pack(">I",len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data)&0xffffffff)
        data=b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",512,512,8,2,0,0,0))+chunk(b"IEND",b"")
        with self.assertRaisesRegex(ValueError,"RGBA"): mod.png_alpha(data)
    def test_wrong_engine_no_mutations(self):
        u,calls=fake_unreal(version="5.8.2-123")
        with self.assertRaisesRegex(ValueError,"5.8.3"): mod.apply_imports(self.plan,unreal_module=u)
        self.assertEqual(calls,{"factories":0,"imports":[],"saves":[]})
    def test_wrong_project_no_mutations(self):
        u,calls=fake_unreal(project=str(mod.REPO/"OtherProject.uproject"))
        with self.assertRaisesRegex(ValueError,"project differs"): mod.apply_imports(self.plan,unreal_module=u)
        self.assertEqual(calls["factories"],0); self.assertFalse(calls["imports"])
    def test_existing_target_no_overwrite(self):
        u,calls=fake_unreal(exists=True)
        with self.assertRaisesRegex(ValueError,"overwrite"): mod.apply_imports(self.plan,unreal_module=u)
        self.assertEqual(calls["factories"],0); self.assertFalse(calls["saves"])
    def test_apply_scope_escape_no_mutations(self):
        u,calls=fake_unreal(); plan=copy.deepcopy(self.plan); plan[0]["destination_object"]="/Game/Core/BP_CoopCharacter.BP_CoopCharacter"
        with self.assertRaisesRegex(ValueError,"outside HC-A3"): mod.apply_imports(plan,unreal_module=u)
        self.assertEqual(calls["factories"],0)
    def test_apply_new_textures_only_fake_api(self):
        u,calls=fake_unreal()
        saved=mod.apply_imports(self.plan,unreal_module=u)
        self.assertEqual(saved,[p["destination_object"] for p in self.plan])
        self.assertEqual(calls["saves"],saved)
        for task in calls["imports"]:
            for key in ("save","replace_existing","replace_existing_settings","async_"): self.assertFalse(task.props[key])
            self.assertEqual(task.props["destination_path"],mod.DEST)
            self.assertFalse(task.props["factory"].props["create_material"])
        self.assertTrue(all(path.startswith(mod.DEST+"/") for path in saved))
    def test_unexpected_import_output_is_not_saved(self):
        u,calls=fake_unreal(unexpected=True)
        with self.assertRaisesRegex(ValueError,"Unexpected import output"): mod.apply_imports(self.plan,unreal_module=u)
        self.assertFalse(calls["saves"])

if __name__=="__main__":
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ImportTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    report={"tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
            "passed":result.wasSuccessful(),"real_unreal_used":False,"apply_path_evidence":"fake editor API only; actual import acceptance pending"}
    (HERE/"test-results.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
