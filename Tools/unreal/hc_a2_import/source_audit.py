"""Read-only binary FBX inspection for the fixed HC-A2 sources; no Unreal dependency."""
import hashlib
import math
from pathlib import Path
import struct
import zlib

ASSET_NAMES = (
    "SM_PressurePlate_Base", "SM_PressurePlate_Top",
    "SM_PressurePlate_Top_Circle", "SM_PressurePlate_Top_Triangle",
    "SM_PressurePlate_Top_Cross", "SM_Statue", "SM_Statue_Small",
    "SM_Altar", "SM_ChamberGate_Frame", "SM_ChamberGate_Leaf",
)
DESTINATION = "/Game/Puzzles/Art/HCA2_Props"
SOURCE_DIR = "SourceArt/HC/HC-A2"
PARENT = "/Game/Shared/Style/M_Stylized"
MATERIALS = {
    "M_Stone": ("MI_HCA2_Stone", "#7A6E68"),
    "M_StoneCarving": ("MI_HCA2_StoneCarving", "#4A4652"),
    "M_Rope": ("MI_HCA2_Rope", "#C9A66B"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def text_sha256(path):
    """Hash UTF-8 text with LF newlines, matching Git text normalization."""
    return hashlib.sha256(Path(path).read_text(encoding="utf-8-sig").encode("utf-8")).hexdigest()


def source_path(root, relative):
    candidate = (root / relative).resolve()
    require(candidate.is_relative_to(root)
            and candidate.is_relative_to((root / SOURCE_DIR).resolve()),
            "Source escaped HC-A2: " + relative)
    return candidate


def fbx_summary(path):
    data = Path(path).read_bytes()
    require(not data.startswith(b"version https://git-lfs.github.com/spec/v1"),
            "Unhydrated LFS pointer: " + str(path))
    require(data[:23] == b"Kaydara FBX Binary  \x00\x1a\x00", "Expected binary FBX")
    version = struct.unpack_from("<I", data, 23)[0]
    require(version in (7400, 7500), "Unsupported FBX version")
    header = "<QQQB" if version >= 7500 else "<IIIB"
    header_size = struct.calcsize(header)

    def property_at(pos):
        kind = chr(data[pos])
        pos += 1
        formats = {"Y": "h", "C": "?", "I": "i", "F": "f", "D": "d", "L": "q"}
        if kind in formats:
            fmt = "<" + formats[kind]
            value = struct.unpack_from(fmt, data, pos)[0]
            return value, pos + struct.calcsize(fmt)
        if kind in ("S", "R"):
            length = struct.unpack_from("<I", data, pos)[0]
            pos += 4
            value = data[pos:pos + length]
            return (value.decode("utf-8") if kind == "S" else value), pos + length
        require(kind in "fdlibc", "Unknown FBX property: " + kind)
        count, encoding, length = struct.unpack_from("<III", data, pos)
        pos += 12
        require(encoding in (0, 1), "Unsupported array encoding")
        raw = data[pos:pos + length]
        if encoding:
            raw = zlib.decompress(raw)
        fmt = {"f": "f", "d": "d", "l": "q", "i": "i", "b": "?", "c": "b"}[kind]
        require(len(raw) == count * struct.calcsize("<" + fmt), "Bad FBX array size")
        return list(struct.unpack("<" + str(count) + fmt, raw)), pos + length

    def node_at(pos):
        end, count, prop_length, name_length = struct.unpack_from(header, data, pos)
        if end == 0:
            return None, pos + header_size
        require(pos < end <= len(data), "Invalid FBX node bounds")
        pos += header_size
        name = data[pos:pos + name_length].decode("utf-8")
        pos += name_length
        prop_end = pos + prop_length
        props = []
        for _ in range(count):
            value, pos = property_at(pos)
            props.append(value)
        require(pos == prop_end, "Bad FBX property length")
        children = []
        while pos < end - header_size:
            child, pos = node_at(pos)
            if child is None:
                break
            children.append(child)
        return (name, props, children), end

    nodes = []
    pos = 27
    while pos < len(data) - header_size:
        node, pos = node_at(pos)
        if node is None:
            break
        nodes.append(node)

    def find(items, name):
        return [n for n in items if n[0] == name]

    def child(node, name):
        matches = find(node[2], name)
        require(len(matches) == 1, "Missing/ambiguous FBX node: " + name)
        return matches[0]

    objects = child(("root", [], nodes), "Objects")
    geometry = find(objects[2], "Geometry")
    require(len(geometry) == 1, "Expected one render geometry")
    geo = geometry[0]
    vertices = child(geo, "Vertices")[1][0]
    indices = child(geo, "PolygonVertexIndex")[1][0]
    require(len(vertices) % 3 == 0 and all(math.isfinite(x) for x in vertices),
            "Invalid vertices")
    polygons, face = [], []
    for index in indices:
        vertex = -index - 1 if index < 0 else index
        require(0 <= vertex < len(vertices) // 3, "Bad vertex index")
        face.append(vertex)
        if index < 0:
            require(len(face) == 3, "Source is not triangulated")
            polygons.append(face)
            face = []
    require(not face and polygons, "Unterminated/empty polygons")
    lo = [min(vertices[i::3]) for i in range(3)]
    hi = [max(vertices[i::3]) for i in range(3)]
    mats = find(objects[2], "Material")
    materials = [n[1][1].split("\x00")[0].removeprefix("Material::") for n in mats]
    layers = find(geo[2], "LayerElementMaterial")
    require(len(layers) == 1, "Expected one material layer")
    assignments = child(layers[0], "Materials")[1][0]
    require(len(assignments) == len(polygons), "Material face count mismatch")
    require(all(0 <= x < len(materials) for x in assignments), "Invalid material index")
    uv_layers = find(geo[2], "LayerElementUV")
    require(len(uv_layers) == 1, "Expected exactly one source UV channel")
    uv = child(uv_layers[0], "UV")[1][0]
    uv_indices = child(uv_layers[0], "UVIndex")[1][0]
    require(len(uv) % 2 == 0 and all(math.isfinite(x) for x in uv), "Invalid UV values")
    require(len(uv_indices) == len(indices)
            and all(0 <= x < len(uv) // 2 for x in uv_indices), "Invalid UV indices")
    normals = find(geo[2], "LayerElementNormal")
    require(len(normals) == 1, "Expected exported normals")
    normal_values = child(normals[0], "Normals")[1][0]
    require(all(math.isfinite(x) for x in normal_values), "Invalid normals")
    settings = child(("root", [], nodes), "GlobalSettings")
    globals_ = {p[1][0]: p[1][4:] for p in child(settings, "Properties70")[2]}
    models = find(objects[2], "Model")
    transforms = {}
    for model in models:
        transforms[model[1][1].split("\x00")[0]] = {
            p[1][0]: p[1][4:] for p in child(model, "Properties70")[2]
            if p[1][0] in ("Lcl Translation", "Lcl Rotation", "Lcl Scaling")
        }
    return {
        "fbx_version": version, "vertices": len(vertices) // 3,
        "triangles": len(polygons), "material_slots": materials,
        "faces_per_slot": {name: assignments.count(i) for i, name in enumerate(materials)},
        "raw_bounds_min": lo, "raw_dimensions": [hi[i] - lo[i] for i in range(3)],
        "uv_channels": len(uv_layers), "normal_values": len(normal_values),
        "global_settings": {k: globals_[k] for k in
                            ("UpAxis", "UpAxisSign", "FrontAxis", "FrontAxisSign",
                             "CoordAxis", "CoordAxisSign", "UnitScaleFactor")},
        "model_transforms": transforms,
    }


def verify_sources(root, manifest):
    """Fail closed on hashes, paths, metadata, assemblies and destination changes."""
    import json
    root = Path(root).resolve()
    require(manifest["schema_version"] == 1, "Unsupported manifest schema")
    require(manifest["destination_root"] == DESTINATION, "Wrong destination root")
    require(manifest["parent_material"]["path"] == PARENT, "Unexpected parent material")
    require([a["name"] for a in manifest["assets"]] == list(ASSET_NAMES),
            "Expected exactly the ten HC-A2 assets in canonical order")
    require(manifest["assemblies"] == {
        "pressure_plate": {"top_raised_cm": [0, 0, 9], "top_pressed_cm": [0, 0, 2]},
        "chamber_gate": {"leaf_closed_cm": [0, 0, 0], "leaf_open_cm": [0, 0, 400],
                         "opening_yz_cm": [400, 400], "passage_axis": "X",
                         "slot_width_x_cm": 34, "open_leaf_top_z_cm": 850},
        "altar": {"relic_base_cm": [0, 0, 97]},
        "statues": {"available": ["SM_Statue", "SM_Statue_Small"],
                    "selection": "pending owner decision"},
    }, "Assembly contract changed")
    expected_materials = [
        {"slot": slot, "name": name, "destination": DESTINATION + "/Materials/" + name,
         "tint_srgb_hex": color, "parameter": "Tint"}
        for slot, (name, color) in MATERIALS.items()
    ]
    require(manifest["materials"] == expected_materials, "Material plan changed")
    report = []
    for asset in manifest["assets"]:
        name = asset["name"]
        require(asset["source"] == SOURCE_DIR + "/" + name + ".fbx", "Unexpected source")
        require(asset["destination"] == DESTINATION + "/" + name, "Destination escaped")
        source = source_path(root, asset["source"])
        require(source.is_file(), "Missing source: " + str(source))
        summary = fbx_summary(source)
        require(source.stat().st_size == asset["source_bytes"], "Source size changed: " + name)
        require(sha256(source) == asset["source_sha256"], "Source hash changed: " + name)
        metadata_path = SOURCE_DIR + "/" + name + ".validation.json"
        require(asset["validation_source"] == metadata_path, "Unexpected metadata source")
        metadata_file = source_path(root, metadata_path)
        require(text_sha256(metadata_file) == asset["validation_sha256"], "Metadata hash changed")
        metadata = json.loads(metadata_file.read_text(encoding="utf-8-sig"))
        require(asset["validation_hash_convention"] == "UTF-8 LF normalized", "Metadata hash convention changed")
        require(metadata == asset["validation_metadata"], "Metadata snapshot changed")
        require(metadata["output"] == asset["source"], "Metadata output mismatch")
        require(metadata["triangles_after"] == summary["triangles"], "Triangle count mismatch")
        require(metadata["pivot"] == "base center" and metadata["fbx_unit"] == "centimeters"
                and metadata["up_axis"] == "+Z" and metadata["UV_warning"] is None,
                "Unexpected source conventions")
        require(metadata["explicit_unit_correction_factor"] == 1.0, "Unexpected correction")
        require(summary == asset["fbx_inspection"], "FBX inspection changed")
        require(asset["material_slots"] == summary["material_slots"], "Material slot mismatch")
        require(asset["material_slots"] == list(MATERIALS)[:(3 if "Statue" in name else 2)],
                "Unexpected HC-A2 material slots")
        require(asset["nanite"] == (metadata["triangles_after"] > 2000),
                "Nanite threshold mismatch")
        globals_ = summary["global_settings"]
        require(globals_["UnitScaleFactor"] == [1.0] and globals_["UpAxis"] == [2]
                and globals_["UpAxisSign"] == [1], "Unexpected FBX unit/axis")
        transforms = list(summary["model_transforms"].values())
        require(len(transforms) == 1, "Unexpected model count")
        transform = transforms[0]
        require(transform.get("Lcl Scaling") == [100.0, 100.0, 100.0]
                and transform.get("Lcl Translation", [0, 0, 0]) == [0, 0, 0],
                "Expected supplied 100x FBX node scale with no translation")
        rotation = transform.get("Lcl Rotation", [0, 0, 0])
        require(abs(rotation[0]) < 0.001 and abs(rotation[1]) < 0.001
                and abs(abs(rotation[2]) - 180) < 0.001, "Unexpected FBX rotation")
        # FBX vertices are meters numerically, with a 100x MODEL scale.
        # The file's declared scene unit remains cm: bake node transform once,
        # keep import_uniform_scale=1.0; never add another 100x multiplier.
        dimensions = [x * 100 for x in summary["raw_dimensions"]]
        require(all(abs(a - b) < 0.02 for a, b in zip(
            dimensions, metadata["dimensions_cm"])), "Dimensions disagree with metadata")
        require(abs(summary["raw_bounds_min"][2]) < 0.0001, "Pivot is not on floor")
        require(all(abs(summary["raw_bounds_min"][i]
                        + summary["raw_dimensions"][i] / 2) < 0.0001
                    for i in (0, 1)), "Pivot is not centered")
        expected_auto = name.startswith("SM_PressurePlate_") or name == "SM_ChamberGate_Leaf"
        require(asset["collision"]["automatic"] == ("one_fitted_box" if expected_auto else "none"),
                "Unexpected automatic collision plan")
        report.append({
            "name": name, "source_sha256": asset["source_sha256"],
            "bytes": source.stat().st_size, "triangles": summary["triangles"],
            "dimensions_cm": metadata["dimensions_cm"],
            "material_slots": summary["material_slots"],
            "nanite": asset["nanite"], "destination": asset["destination"],
            "collision": asset["collision"],
        })
    project_file = root / "CoopGame.uproject"
    require(project_file.is_file(), "Missing CoopGame.uproject")
    project = json.loads(project_file.read_text(encoding="utf-8-sig"))
    require(project.get("EngineAssociation") == "5.8", "Expected project EngineAssociation 5.8")
    require(not project.get("Modules"), "Expected Blueprint-only project")
    master_file = root / "Content/Shared/Style/M_Stylized.uasset"
    require(master_file.is_file(), "Missing read-only M_Stylized")
    require(not master_file.read_bytes().startswith(b"version https://git-lfs"),
            "M_Stylized is not hydrated")
    require(sha256(master_file) == manifest["parent_material"]["sha256"],
            "M_Stylized differs from inspected revision; review before updating manifest")
    return report
