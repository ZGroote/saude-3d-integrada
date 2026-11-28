"""EXP-0025 rodada 3: CPD não rígido ósseo com barreira de leitura muscular."""
from __future__ import annotations

import csv
import importlib.metadata
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy.interpolate import RBFInterpolator
from scipy.spatial import cKDTree

OUT = Path(__file__).resolve().parent
ROOT = Path(__file__).resolve().parents[4]
R1_DIR = OUT.parent
sys.path.insert(0, str(R1_DIR))
import adaptar as cfg  # noqa: E402

cfg.OUT = OUT
SEED = 25031
CPD_W, CPD_BETA, CPD_LAMBDA, CPD_MAX_ITER = 0.1, 2.0, 3.0, 150
CPD_TOL = 1e-5
CPD_N = 1500
CPD_RANK = 128
Q_N = 500


def normalize_pair(source: np.ndarray, target: np.ndarray):
    """Shared center/radius normalization preserves relative pose and size."""
    center = (source.mean(axis=0) + target.mean(axis=0)) / 2.0
    pooled = np.vstack((source - center, target - center))
    radius = float(np.sqrt(np.mean(np.sum(pooled * pooled, axis=1))))
    if not np.isfinite(radius) or radius <= 0:
        raise ValueError("CPD recebeu par degenerado")
    return (source - center) / radius, (target - center) / radius, center, radius


def cpd_nonrigid(source: np.ndarray, target: np.ndarray, *, w=CPD_W, beta=CPD_BETA,
                 lam=CPD_LAMBDA, max_iter=CPD_MAX_ITER, tol=CPD_TOL, rank=CPD_RANK):
    """Myronenko & Song nonrigid CPD, source Y moves toward fixed target X."""
    y0, x, center, radius = normalize_pair(np.asarray(source, float), np.asarray(target, float))
    n, m = len(x), len(y0)
    yy = np.sum(y0 * y0, axis=1)
    xx = np.sum(x * x, axis=1)
    # Nyström low-rank Gaussian kernel: avoids a 1500x1500 dense solve on each
    # E/M iteration while retaining the CPD objective and fixed parameters.
    k = min(rank, m)
    landmarks = np.linspace(0, m - 1, k, dtype=np.int64)
    def rbf(a, b):
        d2 = np.maximum(np.sum(a*a, axis=1)[:, None] + np.sum(b*b, axis=1)[None, :] - 2*a@b.T, 0.0)
        return np.exp(-d2 / (2.0 * beta * beta))
    c_kernel = rbf(y0, y0[landmarks])
    w_kernel = rbf(y0[landmarks], y0[landmarks])
    eigval, eigvec = np.linalg.eigh(w_kernel)
    eigval = np.maximum(eigval, 1e-10)
    q = c_kernel @ (eigvec / np.sqrt(eigval)[None, :])
    ty = y0.copy()
    sigma2 = (n * np.sum(yy) + m * np.sum(xx) - 2 * np.sum(x.sum(axis=0) * y0.sum(axis=0))) / (3.0 * n * m)
    sigma2 = max(float(sigma2), 1e-6)
    iterations = 0
    for it in range(max_iter):
        dist = np.maximum(xx[:, None] + np.sum(ty * ty, axis=1)[None, :] - 2.0 * x @ ty.T, 0.0)
        p = np.exp(-dist / (2.0 * sigma2))
        c = (2.0 * np.pi * sigma2) ** 1.5 * w / (1.0 - w) * (m / n)
        p /= (p.sum(axis=1, keepdims=True) + c + 1e-300)
        p1 = p.sum(axis=0)
        pt1 = p.sum(axis=1)
        px = p.T @ x
        b = px - p1[:, None] * y0
        alpha = lam * sigma2
        reduced = alpha * np.eye(k) + q.T @ (p1[:, None] * q)
        weights = (b - p1[:, None] * q @ np.linalg.solve(reduced, q.T @ b)) / alpha
        ty = y0 + q @ (q.T @ weights)
        sigma_new = (np.sum(pt1 * xx) - 2.0 * np.sum(px * ty) + np.sum(p1 * np.sum(ty * ty, axis=1))) / (3.0 * max(float(p.sum()), 1e-300))
        sigma_new = max(float(sigma_new), 1e-8)
        iterations = it + 1
        relative = abs(sigma_new - sigma2) / max(sigma2, 1e-12)
        sigma2 = sigma_new
        if relative < tol:
            break
    model = {"source_norm": y0, "weights_norm": weights, "center_mm": center,
             "radius_mm": radius, "iterations": iterations, "sigma2_norm": sigma2,
             "w": w, "beta": beta, "lambda": lam, "kernel_rank": k,
             "kernel_landmark_indices": landmarks, "kernel_factor_q": q}
    return ty * radius + center, model


def cpd_map(query_mm: np.ndarray, model: dict) -> np.ndarray:
    q = (np.asarray(query_mm, dtype=float) - model["center_mm"]) / model["radius_mm"]
    y = model["source_norm"]
    # Project query kernel into the same Nyström feature space used by CPD.
    controls = model["source_norm"]
    landmark_ids = model["kernel_landmark_indices"]
    landmark_cloud = controls[landmark_ids]
    kl = np.exp(-np.maximum(np.sum(q*q,axis=1)[:,None] + np.sum(landmark_cloud*landmark_cloud,axis=1)[None,:] - 2*q@landmark_cloud.T,0.0)/(2.0*model["beta"]**2))
    wsmall = np.exp(-np.maximum(np.sum(landmark_cloud*landmark_cloud,axis=1)[:,None] + np.sum(landmark_cloud*landmark_cloud,axis=1)[None,:] - 2*landmark_cloud@landmark_cloud.T,0.0)/(2.0*model["beta"]**2))
    ev, evec = np.linalg.eigh(wsmall)
    ev = np.maximum(ev, 1e-10)
    phi = kl @ (evec / np.sqrt(ev)[None, :])
    mapped = q + phi @ (model["kernel_factor_q"].T @ model["weights_norm"])
    return mapped * model["radius_mm"] + model["center_mm"]


def self_check() -> float:
    rng = np.random.default_rng(25030)
    source = rng.normal(size=(260, 3))
    source /= np.linalg.norm(source, axis=1, keepdims=True)
    target = source.copy()
    target[:, 0] *= 1.2
    moved, model = cpd_nonrigid(source, target, max_iter=100)
    before = cKDTree(target).query(source)[0].mean()
    after = cKDTree(target).query(moved)[0].mean()
    reduction = 1.0 - after / before
    assert reduction >= 0.80, f"Self-check CPD falhou: redução {reduction:.1%} < 80%"
    return float(reduction)


def to_source_coords(points_b0: np.ndarray, fit: dict) -> np.ndarray:
    # inverse of p_B0 = scale * (p_source @ R) + t
    r = np.asarray(fit["rotation_row"], float)
    s = float(fit["scale"])
    t = np.asarray(fit["translation_mm"], float)
    return ((points_b0 - t) / s) @ np.linalg.inv(r)


def main() -> None:
    self_reduction = self_check()
    OUT.mkdir(parents=True, exist_ok=True)
    r1_manifest = json.loads((R1_DIR / "hashes_adaptadas.json").read_text(encoding="utf-8"))
    b0_records = [r for r in r1_manifest["adapted_meshes"] if r["metodo"] == "B0"]
    if len(b0_records) != 11:
        raise RuntimeError(f"Esperadas 11 B0; encontrei {len(b0_records)}")
    for record in b0_records:
        src = R1_DIR / record["arquivo"]
        if cfg.sha256(src) != record["sha256"]:
            raise RuntimeError(f"Hash de B0 divergente: {src.name}")
        dst = OUT / record["arquivo"]
        shutil.copyfile(src, dst)
        if cfg.sha256(dst) != record["sha256"]:
            raise RuntimeError(f"Cópia B0 com hash divergente: {dst.name}")

    source_bones, target_bones = {}, {}
    for name, (fma, side, denver_file) in cfg.BONE_MAP.items():
        _row, path = cfg.resolve_bp3d(fma, side)
        source_bones[name] = cfg.load_mesh(path)
        target_bones[name] = cfg.load_mesh(cfg.DENVER_DIR / denver_file, denver=True)
    b0fit = cfg.fit_similarity(source_bones, target_bones)

    qosso_rows = []
    models = {}
    model_sample_pairs = {}
    for bi, (name, (fma, side, denver_file)) in enumerate(cfg.BONE_MAP.items()):
        source_fit = cfg.sample_surface(source_bones[name], CPD_N, SEED + bi * 100)
        target_fit = cfg.sample_surface(target_bones[name], CPD_N, SEED + 50_000 + bi * 100)
        source_b0 = cfg.transform_points(source_fit, b0fit)
        mapped_fit, model = cpd_nonrigid(source_b0, target_fit)
        models[name] = model
        # Fit sample points are also converted to original BP3D coordinates for
        # the TPS displacement correspondences used if every Q-osso passes.
        model_sample_pairs[name] = (source_fit, mapped_fit)
        holdout_source = cfg.sample_surface(source_bones[name], Q_N, SEED + 100_000 + bi * 100)
        holdout_b0 = cfg.transform_points(holdout_source, b0fit)
        holdout_cpd = cpd_map(holdout_b0, model)
        projector = cfg.SurfaceProjector(target_bones[name])
        _qproj, d_b0 = projector.project(holdout_b0)
        _qproj_cpd, d_cpd = projector.project(holdout_cpd)
        row = {"osso": name, "fma": fma, "pontos_ajuste_fonte": CPD_N,
               "pontos_ajuste_alvo": CPD_N, "pontos_holdout": Q_N,
               "iteracoes_cpd": model["iterations"], "sigma2_final_normalizado": model["sigma2_norm"],
               "distancia_media_b0_mm": float(d_b0.mean()),
               "distancia_media_cpd_mm": float(d_cpd.mean()),
               "qosso_le_2mm": bool(d_cpd.mean() <= 2.0),
               "qosso_menor_que_b0": bool(d_cpd.mean() < d_b0.mean())}
        qosso_rows.append(row)
        print(f"Q-osso {name}: B0={d_b0.mean():.3f} mm; CPD={d_cpd.mean():.3f} mm; pass={row['qosso_le_2mm'] and row['qosso_menor_que_b0']}")

    with (OUT / "qosso.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(qosso_rows[0])); writer.writeheader(); writer.writerows(qosso_rows)
    qosso_pass = all(r["qosso_le_2mm"] and r["qosso_menor_que_b0"] for r in qosso_rows)
    base_manifest = {"experiment": "EXP-0025", "round": 3, "seed": SEED,
                     "status": "Q-osso passou" if qosso_pass else "INCONCLUSIVA: Q-osso falhou; nenhuma malha muscular M3 foi gerada nem músculo Denver foi lido",
                     "cpd": {"paper": "Myronenko & Song, IEEE TPAMI 32(12), 2010", "w": CPD_W, "beta": CPD_BETA,
                             "lambda": CPD_LAMBDA, "max_iter": CPD_MAX_ITER, "convergence_relative_sigma2": CPD_TOL,
                             "samples_per_bone_source_and_target": CPD_N, "nystrom_kernel_rank": CPD_RANK,
                             "normalization": "shared pair centroid and pooled RMS radius; beta in normalized coordinates",
                             "self_check_sphere_to_20pct_ellipsoid_mean_distance_reduction": self_reduction},
                     "qosso_holdout_points_per_bone": Q_N, "qosso_pass": qosso_pass,
                     "b0_sha_verified_and_copied": True,
                     "denver_bone_paths_read": [str(cfg.DENVER_DIR / f) for _, _, f in cfg.BONE_MAP.values()],
                     "denver_muscle_paths_read": [], "qosso": qosso_rows}
    if not qosso_pass:
        (OUT / "hashes_adaptadas_r3.json").write_text(json.dumps(base_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        print("Q-osso falhou; parada pré-registrada, avaliação muscular não executada.")
        return

    # Only after Q-osso passes: derive terminal insertion subsets and fit each
    # muscle TPS from original BP3D anchors to CPD-mapped positions.
    insertion_map, insertion_rows, mesh_records = {}, [], [dict(r, origem="rodada1") for r in b0_records]
    for group, components in cfg.MUSCLE_GROUPS.items():
        for ci, (fma, _denver_muscle) in enumerate(components):
            row, path = cfg.resolve_bp3d(fma, "left")
            muscle = cfg.load_mesh(path)
            verts = np.asarray(muscle.vertices, float)
            all_labels, all_dist = cfg.source_insertions(muscle, source_bones)
            centered = verts - verts.mean(axis=0)
            _u, _s, vh = np.linalg.svd(centered, full_matrices=False)
            proj = centered @ vh[0]
            low, high = float(proj.min()), float(proj.max())
            terminal = (proj <= low + .1 * (high-low)) | (proj >= high - .1 * (high-low))
            labels = {bone: np.intersect1d(ids, np.flatnonzero(terminal), assume_unique=True)
                      for bone, ids in all_labels.items()}
            attached = [bone for bone, ids in labels.items() if len(ids)]
            if not attached:
                raise RuntimeError(f"Q-osso passou, mas não há inserções terminais para {group}:{ci}")
            insertion_map[f"{group}:{ci}"] = {bone: ids.astype(int).tolist() for bone, ids in labels.items() if len(ids)}
            for bone, ids in labels.items():
                if len(ids):
                    insertion_rows.append({"grupo_muscular": group, "componente": ci, "fma_musculo": fma,
                                           "osso": bone, "vertices_insercao": len(ids),
                                           "vertices_musculo": len(verts), "fracao": len(ids)/len(verts),
                                           "distancia_max_bp3d_mm": float(all_dist[ids].max()),
                                           "fonte_literatura": "Gray's Anatomy, 42ª ed., capítulo/página: a conferir"})
            selected = set(attached)
            for bone in list(selected): selected.update(cfg.ADJACENCY.get(bone, set()))
            selected = [bone for bone in cfg.BONE_MAP if bone in selected]
            x_pairs, y_pairs = [], []
            for bone in selected:
                x, y = model_sample_pairs[bone]
                x_pairs.append(x); y_pairs.append(y)
            x = np.vstack(x_pairs); y = np.vstack(y_pairs)
            rbf = RBFInterpolator(x, y, kernel="thin_plate_spline", smoothing=2.0, neighbors=min(48, len(x)))
            m3_vertices = rbf(verts)
            fixed_parts=[]
            for bone in attached:
                ids=labels[bone]
                projected,_=cfg.SurfaceProjector(target_bones[bone]).project(m3_vertices[ids])
                m3_vertices[ids]=projected; fixed_parts.append(ids)
            fixed=np.unique(np.concatenate(fixed_parts)).astype(np.int64)
            m3_vertices=cfg.laplacian_relax(m3_vertices,muscle,fixed,iterations=12,factor=.22)
            for method, out_vertices in (("M3",m3_vertices),):
                mesh=trimesh.Trimesh(vertices=out_vertices,faces=muscle.faces.copy(),process=False)
                suffix="" if len(components)==1 else ("_long" if ci==0 else "_short")
                filename=f"{method}_{group}{suffix}.ply"; dest=OUT/filename; mesh.export(dest)
                mesh_records.append({"arquivo":filename,"metodo":method,"grupo":group,"componente":ci,"fma":fma,
                                    "vertices":len(mesh.vertices),"faces":len(mesh.faces),"watertight":bool(mesh.is_watertight),
                                    "sha256":cfg.sha256(dest)})
    with (OUT/"insercoes_m3.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(insertion_rows[0]));writer.writeheader();writer.writerows(insertion_rows)
    (OUT/"insercoes_vertices_m3.json").write_text(json.dumps(insertion_map,indent=2),encoding="utf-8")
    versions={}
    for pkg in ("numpy","scipy","trimesh","scikit-image"):
        try: versions[pkg]=importlib.metadata.version(pkg)
        except importlib.metadata.PackageNotFoundError: versions[pkg]="não instalado"
    base_manifest.update({"status":"M3 congelada após Q-osso passar, antes da avaliação muscular",
                          "input_versions":versions,"insertion_rule":"<=3 mm plus PCA terminal 10% each end",
                          "m3_method":"TPS from original BP3D bone points to CPD mapped positions; projection and Laplacian",
                          "insertion_fractions":{r["grupo_muscular"]+":"+str(r["componente"]):r["fracao"] for r in insertion_rows},
                          "adapted_meshes":mesh_records})
    (OUT/"hashes_adaptadas_r3.json").write_text(json.dumps(base_manifest,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"Q-osso passou; malhas gravadas={len(mesh_records)}; nenhum músculo Denver foi lido na adaptação.")


if __name__ == "__main__":
    main()
