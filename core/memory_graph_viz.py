"""
3-D Error Memory Brain

Hybrid mathematical model:
- vector representations (Chroma embeddings or features)
- K-means error communities
- Mexican-hat relational field
- tanh-normalized edge weights
- linear regression outcome prediction

Privacy: anonymized error patterns only (no resume text).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from core.error_memory import load_memory, _get_chroma_collection


def _feature_vector(pat: Dict[str, Any]) -> List[float]:
    code = str(pat.get("error_code", ""))
    source = 1.0 if pat.get("source") == "user" else 0.0
    seed = 1.0 if pat.get("seed") else 0.0
    success = float(pat.get("success_rate", 0.0) or 0.0)
    seen = math.log1p(float(pat.get("times_seen", 0) or 0))
    gain = float(pat.get("avg_score_gain", 0.0) or 0.0)
    h1 = sum(ord(c) for c in code) % 17 / 17.0
    h2 = sum(ord(c) * 3 for c in code) % 13 / 13.0
    h3 = 1.0 if code.startswith("U") else 0.0
    return [source, seed, success, seen / 5.0, gain / 20.0, h1, h2, h3]


def _get_vectors(patterns: List[Dict[str, Any]]) -> List[List[float]]:
    collection = _get_chroma_collection()
    if collection is not None:
        try:
            ids = [str(p.get("id")) for p in patterns]
            got = collection.get(ids=ids, include=["embeddings"])
            emb = got.get("embeddings") or []
            got_ids = got.get("ids") or []
            id_to_emb = {
                str(pid): list(emb[i])
                for i, pid in enumerate(got_ids)
                if i < len(emb) and emb[i] is not None
            }
            out = []
            for p in patterns:
                e = id_to_emb.get(str(p.get("id")))
                out.append(e if e else _feature_vector(p))
            return out
        except Exception as e:
            print(f"Embedding fetch failed: {e}")
    return [_feature_vector(p) for p in patterns]


def _pca_3d(vectors: List[List[float]]) -> List[Tuple[float, float, float]]:
    import numpy as np
    x = np.array(vectors, dtype=float)
    x = x - x.mean(axis=0, keepdims=True)
    _, _, vt = np.linalg.svd(x, full_matrices=False)
    proj = x @ vt[:3].T
    for i in range(3):
        span = proj[:, i].max() - proj[:, i].min()
        if span > 1e-8:
            proj[:, i] = (proj[:, i] - proj[:, i].mean()) / span
    return [(float(a), float(b), float(c)) for a, b, c in proj]


def mexican_hat(r: float, sigma: float = 0.35) -> float:
    """
    Ricker wavelet / Mexican-hat radial basis.
    Positive near center, negative in a ring, ~0 far away.
    """
    if sigma <= 0:
        return 0.0
    x = (r / sigma) ** 2
    return float((1.0 - x) * math.exp(-x / 2.0))


def _pairwise_distances(coords: List[Tuple[float, float, float]]):
    import numpy as np
    p = np.array(coords, dtype=float)
    # (n,n) euclidean
    d = ((p[:, None, :] - p[None, :, :]) ** 2).sum(axis=2) ** 0.5
    return d


def _kmeans_labels(vectors: List[List[float]], k: int = 3) -> List[int]:
    import numpy as np
    try:
        from sklearn.cluster import KMeans
        n = len(vectors)
        k = max(1, min(k, n))
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        return list(km.fit_predict(np.array(vectors, dtype=float)))
    except Exception:
        # fallback: bucket by code prefix
        labels = []
        for v, _ in zip(vectors, range(len(vectors))):
            labels.append(0 if v[-1] >= 0.5 else 1)  # U vs S heuristic from feature
        return labels


def _fit_gain_regression(patterns: List[Dict[str, Any]]):
    """
    Simple linear regression:
    predicted_gain ~ success_rate + log(times_seen) + seed_flag
    Returns model coeffs or None.
    """
    import numpy as np
    rows, y = [], []
    for p in patterns:
        if p.get("seed"):
            continue
        if float(p.get("times_seen") or 0) < 1:
            continue
        rows.append([
            1.0,
            float(p.get("success_rate") or 0.0),
            math.log1p(float(p.get("times_seen") or 0.0)),
            1.0 if str(p.get("error_code", "")).startswith("U") else 0.0,
        ])
        y.append(float(p.get("avg_score_gain") or 0.0))

    if len(rows) < 3:
        return None

    X = np.array(rows, dtype=float)
    yy = np.array(y, dtype=float)
    try:
        beta, *_ = np.linalg.lstsq(X, yy, rcond=None)
        return beta
    except Exception:
        return None


def _predict_gain(beta, pat: Dict[str, Any]) -> Optional[float]:
    if beta is None:
        return None
    x = [
        1.0,
        float(pat.get("success_rate") or 0.0),
        math.log1p(float(pat.get("times_seen") or 0.0)),
        1.0 if str(pat.get("error_code", "")).startswith("U") else 0.0,
    ]
    return float(sum(b * xi for b, xi in zip(beta, x)))


def build_error_mind_figure(max_nodes: int = 40, k_clusters: int = 3, sigma: float = 0.35):
    """
    Build Plotly 3D Error Memory Brain figure.
    """
    try:
        import plotly.graph_objects as go
        import numpy as np
    except Exception:
        return None, {}

    data = load_memory()
    patterns = data.get("patterns", [])
    if not patterns:
        return None, {}

    learned = [p for p in patterns if not p.get("seed")]
    seeds = [p for p in patterns if p.get("seed")]
    selected = (learned + seeds)[:max_nodes]

    vectors = _get_vectors(selected)
    coords = _pca_3d(vectors)
    labels = _kmeans_labels(vectors, k=k_clusters)
    dist = _pairwise_distances(coords)

    # relationship matrix via Mexican Hat * success coupling, then tanh
    n = len(selected)
    edges = []
    edge_weights = []
    for i in range(n):
        for j in range(i + 1, n):
            dij = float(dist[i, j])
            m = mexican_hat(dij, sigma=sigma)
            # coupling by shared community + success
            same_cluster = 1.0 if labels[i] == labels[j] else 0.35
            s_ij = same_cluster * (
                0.5
                + 0.25 * float(selected[i].get("success_rate") or 0)
                + 0.25 * float(selected[j].get("success_rate") or 0)
            )
            raw = m * s_ij
            # also boost exact same error code
            if selected[i].get("error_code") == selected[j].get("error_code"):
                raw += 0.25
            r = math.tanh(raw * 2.0)
            # keep meaningful edges only
            if abs(r) >= 0.12:
                edges.append((i, j))
                edge_weights.append(r)

    beta = _fit_gain_regression(selected)

    # edge traces by sign
    def edge_trace(mask_positive: bool):
        ex, ey, ez = [], [], []
        for (i, j), w in zip(edges, edge_weights):
            if mask_positive and w < 0:
                continue
            if (not mask_positive) and w >= 0:
                continue
            ex += [coords[i][0], coords[j][0], None]
            ey += [coords[i][1], coords[j][1], None]
            ez += [coords[i][2], coords[j][2], None]
        color = "rgba(37,99,235,0.55)" if mask_positive else "rgba(220,38,38,0.35)"
        return go.Scatter3d(
            x=ex, y=ey, z=ez,
            mode="lines",
            line=dict(color=color, width=4 if mask_positive else 2),
            hoverinfo="none",
            name="Positive relations" if mask_positive else "Inhibitory relations",
        )

    # node data
    cluster_colors = ["#2563EB", "#D97706", "#16A34A", "#7C3AED", "#0891B2"]
    xs, ys, zs = zip(*coords)
    colors, sizes, texts = [], [], []
    for idx, p in enumerate(selected):
        c = cluster_colors[labels[idx] % len(cluster_colors)]
        colors.append(c)
        sizes.append(9 + 10 * float(p.get("success_rate") or 0) + min(float(p.get("times_seen") or 1), 15) * 0.3)
        pred = _predict_gain(beta, p)
        pred_txt = f"{pred:.2f}" if pred is not None else "n/a"
        texts.append(
            f"<b>{p.get('error_code')}</b><br>"
            f"cluster: {labels[idx]}<br>"
            f"source: {p.get('source')}<br>"
            f"success: {float(p.get('success_rate') or 0):.2f}<br>"
            f"seen: {p.get('times_seen')}<br>"
            f"avg gain: {float(p.get('avg_score_gain') or 0):.2f}<br>"
            f"predicted gain: {pred_txt}<br>"
            f"{'seed' if p.get('seed') else 'learned'}"
        )

    node_trace = go.Scatter3d(
        x=list(xs), y=list(ys), z=list(zs),
        mode="markers+text",
        text=[str(p.get("error_code", "")) for p in selected],
        textposition="top center",
        marker=dict(size=sizes, color=colors, opacity=0.92, line=dict(width=1, color="#0F172A")),
        hovertext=texts,
        hoverinfo="text",
        name="Error patterns",
    )

    fig = go.Figure(data=[edge_trace(True), edge_trace(False), node_trace])
    fig.update_layout(
        title="3-D Error Memory Brain",
        scene=dict(
            xaxis=dict(title="Semantic axis X", showbackground=False),
            yaxis=dict(title="Semantic axis Y", showbackground=False),
            zaxis=dict(title="Semantic axis Z", showbackground=False),
            bgcolor="#F8FAFC",
        ),
        margin=dict(l=0, r=0, t=50, b=0),
        paper_bgcolor="#F8FAFC",
        height=600,
        legend=dict(orientation="h"),
    )

    summary = {
        "nodes": n,
        "edges": len(edges),
        "clusters": len(set(labels)),
        "regression_ready": beta is not None,
        "cluster_counts": {int(c): int(labels.count(c)) for c in set(labels)},
    }
    return fig, summary