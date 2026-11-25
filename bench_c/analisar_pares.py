#!/usr/bin/env python3
"""analisar_pares.py - análise PAREADA das coletas alternadas (coleta_pareada.sh).

Uso:  python3 analisar_pares.py resultados/pareado_AAAAMMDD_HHMMSS

Para cada bloco (pasta b1, b2, ...) resume cada métrica pela MEDIANA das rodadas válidas
(a rodada 0, de aquecimento, é descartada). Depois, em cada bloco, calcula a diferença
percentual entre os ambientes e resume as diferenças dos blocos com média e intervalo de
confiança de 95% (distribuição t de Student). Como os ambientes de um bloco são medidos
com poucos minutos de intervalo, a deriva lenta da máquina afeta todos quase igualmente e
tende a se cancelar na diferença.

Ambientes: N = native, D = docker-bind (seccomp padrão), S = docker-noseccomp,
           C = native-scope (nativo em scope raso do systemd: mesma posição de cgroup do container).

Comparações (percentual sobre o ambiente de base). Com o ambiente C presente:
  C-N : nativo em scope raso contra nativo no terminal (efeito do ambiente de execução / cgroup)
  D-C : Docker padrão contra nativo equivalente       (overhead TOTAL do Docker, baseline justo)
  S-C : Docker sem seccomp contra nativo equivalente  (custo do isolamento: namespaces etc.)
  D-S : Docker padrão contra Docker sem seccomp       (custo do filtro seccomp)
Sem o ambiente C (coletas antigas): D-N, S-N e D-S.

Leitura do sinal:
  métricas de TEMPO (ns/op, ns/página, ns/roundtrip): positivo = o primeiro ambiente é mais LENTO
  métricas de THROUGHPUT (MiB/s):                     positivo = o primeiro ambiente é mais RÁPIDO
  '*' = o intervalo de confiança de 95% não inclui zero (efeito detectável nesses dados)

Saídas na própria pasta: medianas_por_bloco.csv e analise_pares.csv.
Só usa a biblioteca padrão do Python.
"""
import csv
import glob
import math
import os
import statistics as st
import sys

# valor crítico t (bilateral, 95%) para 1..30 graus de liberdade; acima disso, ~normal
T95 = [12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
       2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
       2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042]

AMBIENTES = {"N": "native", "D": "docker-bind", "S": "docker-noseccomp", "C": "native-scope"}
COMP_COM_C = [("C", "N", "C-N"), ("D", "C", "D-C"), ("S", "C", "S-C"), ("D", "S", "D-S")]
COMP_SEM_C = [("D", "N", "D-N"), ("S", "N", "S-N"), ("D", "S", "D-S")]


def carregar(arquivo):
    """Devolve {(benchmark, metrica, unidade): mediana das rodadas válidas}."""
    valores = {}
    with open(arquivo, newline="") as f:
        for r in csv.DictReader(f):
            if int(r["run"]) == 0:      # aquecimento
                continue
            chave = (r["benchmark"], r["metric"], r["unit"])
            valores.setdefault(chave, []).append(float(r["value"]))
    return {k: st.median(v) for k, v in valores.items()}


def intervalo(diffs):
    """(média, meia-largura do IC95%, n). A meia-largura é None se n < 2."""
    n = len(diffs)
    m = st.mean(diffs)
    if n < 2:
        return m, None, n
    t = T95[n - 2] if n - 1 <= len(T95) else 1.96
    return m, t * st.stdev(diffs) / math.sqrt(n), n


def numero_do_bloco(caminho):
    try:
        return int(os.path.basename(caminho)[1:])
    except ValueError:
        return 10 ** 9


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        print(__doc__)
        sys.exit(2)
    pasta = sys.argv[1]

    blocos = {}
    for p in sorted(glob.glob(os.path.join(pasta, "b*")), key=numero_do_bloco):
        if not os.path.isdir(p):
            continue
        dados = {}
        for sigla, nome in AMBIENTES.items():
            arq = os.path.join(p, nome + ".csv")
            if os.path.exists(arq):
                dados[sigla] = carregar(arq)
        if dados:
            blocos[os.path.basename(p)] = dados
    if not blocos:
        print("nenhum bloco (pastas b1, b2, ...) com CSVs encontrado em", pasta)
        sys.exit(1)

    tem_c = any("C" in d for d in blocos.values())
    comparacoes = COMP_COM_C if tem_c else COMP_SEM_C

    metricas = []
    for dados in blocos.values():
        for tabela in dados.values():
            for chave in tabela:
                if chave not in metricas:
                    metricas.append(chave)

    # ---- medianas por bloco (útil para gráficos) ----
    with open(os.path.join(pasta, "medianas_por_bloco.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["bloco", "ambiente", "benchmark", "metric", "unit", "mediana"])
        for bloco, dados in blocos.items():
            for sigla, tabela in dados.items():
                for (b, m, u), v in tabela.items():
                    w.writerow([bloco, AMBIENTES[sigla], b, m, u, f"{v:.3f}"])

    # ---- diferenças pareadas ----
    linhas_csv = []
    resultado = {}
    for chave in metricas:
        for a, base, rotulo in comparacoes:
            diffs = []
            for dados in blocos.values():
                if a in dados and base in dados and chave in dados[a] and chave in dados[base]:
                    x, y = dados[a][chave], dados[base][chave]
                    if y != 0:
                        diffs.append(100.0 * (x - y) / y)
            if diffs:
                m, h, n = intervalo(diffs)
                sig = h is not None and abs(m) > h
                resultado[(chave, rotulo)] = (m, h, n, sig)
                linhas_csv.append([chave[0], chave[1], chave[2], rotulo, n, f"{m:.3f}",
                                   "" if h is None else f"{h:.3f}", int(sig)])

    with open(os.path.join(pasta, "analise_pares.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["benchmark", "metric", "unit", "comparacao", "n_blocos",
                    "media_pct", "ic95_pct", "significativo"])
        w.writerows(linhas_csv)

    # ---- relatório em texto ----
    print(f"pasta: {pasta}   blocos: {len(blocos)} ({', '.join(blocos)})")
    contagem = {s: sum(1 for d in blocos.values() if s in d) for s in AMBIENTES}
    print("blocos por ambiente: " + ", ".join(f"{AMBIENTES[s]}={c}" for s, c in contagem.items()))
    if len(blocos) < 3:
        print("AVISO: com menos de 3 blocos o intervalo de confiança é muito largo; use 5 ou mais.")
    print()
    cab = f"{'métrica':40s}{'nativo':>12s}{'dif. entre blocos':>19s}" + "".join(f"{r:>16s}" for _, _, r in comparacoes)
    print(cab)
    print("-" * len(cab))
    for chave in metricas:
        nat = [d["N"][chave] for d in blocos.values() if "N" in d and chave in d["N"]]
        if nat:
            media_nat = st.mean(nat)
            cv = f"{100 * st.stdev(nat) / media_nat:.1f}%" if len(nat) > 1 and media_nat else "-"
            col_nat = f"{media_nat:12.1f}{cv:>19s}"
        else:
            col_nat = f"{'-':>12s}{'-':>19s}"
        nome = f"{chave[0]}/{chave[1]} [{chave[2]}]"
        cols = ""
        for _, _, rotulo in comparacoes:
            r = resultado.get((chave, rotulo))
            if r is None:
                cols += f"{'-':>16s}"
            else:
                m, h, n, sig = r
                txt = f"{m:+.1f}%" + ("" if h is None else f"±{h:.1f}") + ("*" if sig else "")
                cols += f"{txt:>16s}"
        print(f"{nome[:40]:40s}{col_nat}{cols}")
    print()
    print("'nativo' = média das medianas dos blocos; 'dif. entre blocos' = variação (CV) do nativo")
    print("entre blocos, ou seja, a deriva da máquina. '*' = IC95% não inclui zero.")
    print(f"arquivos gerados em {pasta}: medianas_por_bloco.csv, analise_pares.csv")


if __name__ == "__main__":
    main()
