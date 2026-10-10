"""Read-only, standard-library inspection of the supplied binary FBX files."""
import struct
import zlib
from pathlib import Path


def inspect_fbx(path):
    data = Path(path).read_bytes()
    if not data.startswith(b"Kaydara FBX Binary  \x00\x1a\x00"):
        raise ValueError("Not a hydrated binary FBX: " + str(path))
    version = struct.unpack_from("<I", data, 23)[0]
    wide = version >= 7500
    header = "<QQQB" if wide else "<IIIB"
    header_size = struct.calcsize(header)

    def prop(offset):
        kind = chr(data[offset])
        offset += 1
        formats = {"Y": "h", "C": "?", "I": "i", "F": "f", "D": "d", "L": "q"}
        if kind in formats:
            fmt = "<" + formats[kind]
            return struct.unpack_from(fmt, data, offset)[0], offset + struct.calcsize(fmt)
        if kind in "SR":
            size = struct.unpack_from("<I", data, offset)[0]
            value = data[offset + 4:offset + 4 + size]
            return (value.decode("utf-8") if kind == "S" else value), offset + 4 + size
        if kind in "fdlibc":
            count, encoding, size = struct.unpack_from("<III", data, offset)
            raw = data[offset + 12:offset + 12 + size]
            if encoding == 1:
                raw = zlib.decompress(raw)
            elif encoding != 0:
                raise ValueError("Unsupported FBX array encoding")
            fmt = {"f": "f", "d": "d", "l": "q", "i": "i", "b": "?", "c": "b"}[kind]
            return list(struct.unpack("<" + str(count) + fmt, raw)), offset + 12 + size
        raise ValueError("Unsupported FBX property " + kind)

    def node(offset):
        end, count, length, name_size = struct.unpack_from(header, data, offset)
        if end == 0:
            return None, offset + header_size
        if not offset < end <= len(data):
            raise ValueError("Invalid FBX node boundary")
        pos = offset + header_size
        name = data[pos:pos + name_size].decode("utf-8")
        pos += name_size
        props = []
        props_end = pos + length
        for _ in range(count):
            value, pos = prop(pos)
            props.append(value)
        if pos != props_end:
            raise ValueError("Invalid FBX property length")
        children = []
        while pos < end - header_size:
            child, pos = node(pos)
            if child is None:
                break
            children.append(child)
        return {"name": name, "props": props, "children": children}, end

    roots = []
    pos = 27
    while pos < len(data) - header_size:
        item, pos = node(pos)
        if item is None:
            break
        roots.append(item)

    def children(item, name):
        return [c for c in item["children"] if c["name"] == name]

    objects = next(n for n in roots if n["name"] == "Objects")
    meshes = [n for n in children(objects, "Geometry") if n["props"][-1] == "Mesh"]
    if len(meshes) != 1:
        raise ValueError("Expected exactly one mesh")
    mesh = meshes[0]
    vertices = children(mesh, "Vertices")[0]["props"][0]
    indices = children(mesh, "PolygonVertexIndex")[0]["props"][0]
    faces = []
    count = 0
    for index in indices:
        if not 0 <= (index if index >= 0 else -index - 1) < len(vertices) // 3:
            raise ValueError("Invalid vertex index")
        count += 1
        if index < 0:
            faces.append(count)
            count = 0
    if count or any(n < 3 for n in faces):
        raise ValueError("Invalid polygon topology")
    materials = children(objects, "Material")
    material_names = {m["props"][0]: m["props"][1].split("\x00")[0] for m in materials}
    connections = next(n for n in roots if n["name"] == "Connections")
    model_ids = {m["props"][0] for m in children(objects, "Model") if m["props"][-1] == "Mesh"}
    slots = [material_names[c["props"][1]] for c in children(connections, "C")
             if c["props"][0] == "OO" and c["props"][1] in material_names and c["props"][2] in model_ids]
    bounds_min = [min(vertices[i::3]) for i in range(3)]
    bounds_max = [max(vertices[i::3]) for i in range(3)]
    settings = next(n for n in roots if n["name"] == "GlobalSettings")
    properties = children(settings, "Properties70")[0]
    axis_units = {p["props"][0]: p["props"][-1] for p in children(properties, "P")
                  if p["props"][0] in ("UpAxis", "UpAxisSign", "FrontAxis", "FrontAxisSign", "CoordAxis", "CoordAxisSign", "UnitScaleFactor")}
    models = [m for m in children(objects, "Model") if m["props"][-1] == "Mesh"]
    transforms = [{p["props"][0]: p["props"][4:] for p in children(children(m, "Properties70")[0], "P")
                   if p["props"][0].startswith("Lcl ")} for m in models]
    material_properties = {m["props"][1].split("\x00")[0]:
                           {p["props"][0]: p["props"][4:] for p in children(children(m, "Properties70")[0], "P")}
                           for m in materials}
    return {"fbx_version": version, "mesh_count": len(meshes), "vertex_count": len(vertices) // 3,
            "polygon_count": len(faces), "triangles": sum(n - 2 for n in faces),
            "all_triangles": all(n == 3 for n in faces), "material_slots": slots,
            "has_normals": bool(children(mesh, "LayerElementNormal")),
            "uv_layer_count": len(children(mesh, "LayerElementUV")),
            "raw_vertex_bounds_min": bounds_min, "raw_vertex_bounds_max": bounds_max,
            "raw_vertex_dimensions": [b - a for a, b in zip(bounds_min, bounds_max)],
            "global_settings": axis_units, "model_transforms": transforms,
            "material_properties": material_properties}
