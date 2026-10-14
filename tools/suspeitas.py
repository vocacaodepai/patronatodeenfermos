"""Marca hospitais do CNES com coordenada suspeita. Uso: python3 suspeitas.py hosp.pkl municipios.csv saida.pkl"""
import sys, numpy as np, pandas as pd
hp, mp, out = sys.argv[1:4]
H = pd.read_pickle(hp).reset_index(drop=True)
M = pd.read_csv(mp, dtype={"codigo_ibge": str}); M["nome"] = M.nome.str.strip()
def hv(a, b, c, d):
    r = np.radians; x = np.sin((r(c) - r(a)) / 2) ** 2 + np.cos(r(a)) * np.cos(r(c)) * np.sin((r(d) - r(b)) / 2) ** 2
    return 12742 * np.arcsin(np.sqrt(x))
dec = lambda v: len(f"{v:.8f}".rstrip("0").split(".")[1])
H["pouca_precisao"] = H.lat.map(dec).le(3) | H.lng.map(dec).le(3)
H["g"] = H.lat.round(3).astype(str) + "," + H.lng.round(3).astype(str)
H["ponto_repetido"] = H.groupby("g").id.transform("count").ge(3)
# distância ao centro do bairro (mediana dos pares da mesma cidade+bairro)
H["chave"] = H.uf + "|" + H.cidade + "|" + H.bairro
med = H.groupby("chave").agg(mlat=("lat", "median"), mlng=("lng", "median"), n=("id", "count"))
H = H.join(med, on="chave")
H["d_bairro"] = hv(H.lat, H.lng, H.mlat, H.mlng)
H["fora_do_bairro"] = (H.n >= 3) & (H.d_bairro > 4)
# distância ao centro do município
Mc = M.set_index(["codigo_uf", "nome"]) if False else M
H = H.merge(M[["nome", "latitude", "longitude"]].rename(columns={"nome": "cidade", "latitude": "clat", "longitude": "clng"}).drop_duplicates("cidade"), on="cidade", how="left")
H["d_cidade"] = hv(H.lat, H.lng, H.clat, H.clng)
H["longe_cidade"] = H.d_cidade > 45
H["suspeita"] = (H.pouca_precisao | H.ponto_repetido | H.fora_do_bairro | H.longe_cidade) & ~H.aprox
print(len(H), "locais;", int(H.suspeita.sum()), "suspeitos:", {c: int(H[c].sum()) for c in ["pouca_precisao", "ponto_repetido", "fora_do_bairro", "longe_cidade"]})
H.to_pickle(out)
