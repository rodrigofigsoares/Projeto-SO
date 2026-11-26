import copy
import random
from django.http import JsonResponse
from django.shortcuts import render

# Dados originais da coleta (Parte A) com a categoria adicionada para o filtro do menu
RAW_DATA = [
    {
        "benchmark": "alloc_malloc_free_64B",
        "category": "memoria",
        "metric": "time_per_op",
        "unit": "ns/op",
        "native": {"mean": 9.9451, "sd": 0.61444816253647, "lo": 9.505580801175602, "hi": 10.384619198824398, "vals": [9.728, 10.059, 9.232, 10.397, 10.421, 8.747, 9.625, 10.274, 10.191, 10.777], "cv": 6.178401047113353},
        "docker": {"mean": 8.7734, "sd": 1.1503738715932506, "lo": 7.950529279215356, "hi": 9.596270720784645, "vals": [8.932, 9.58, 9.13, 7.514, 7.67, 7.857, 8.827, 9.83, 10.927, 7.467], "cv": 13.112064554143782},
        "ratio": 0.8821831856894351,
        "diff": -11.78168143105649,
        "t": -2.841032475851661,
        "overlap": True,
    },
    {
        "benchmark": "alloc_mmap_munmap_4MiB",
        "category": "memoria",
        "metric": "time_per_op",
        "unit": "ns/op",
        "native": {"mean": 5406.8883, "sd": 21.645614136458402, "lo": 5391.405036214092, "hi": 5422.371563785907, "vals": [5416.761, 5416.423, 5371.306, 5380.587, 5402.591, 5425.433, 5400.471, 5447.492, 5404.454, 5403.365], "cv": 0.40033403568663334},
        "docker": {"mean": 4985.0137, "sd": 11.146752601841808, "lo": 4977.0403475322655, "hi": 4992.987052467735, "vals": [4988.318, 4995.256, 4996.185, 4982.465, 4991.687, 4964.737, 4970.037, 4993.137, 4976.293, 4992.022], "cv": 0.22360525512380852},
        "ratio": 0.9219746041359872,
        "diff": -7.802539586401281,
        "t": -54.794329417814076,
        "overlap": False,
    },
    {
        "benchmark": "alloc_mmap_touch_4MiB",
        "category": "memoria",
        "metric": "time_per_page",
        "unit": "ns/page",
        "native": {"mean": 223.241, "sd": 4.395742510910104, "lo": 220.0966937030162, "hi": 226.38530629698383, "vals": [229.037, 219.879, 220.162, 220.732, 220.74, 219.949, 219.378, 230.08, 229.109, 223.344], "cv": 1.969056988147385},
        "docker": {"mean": 220.2824, "sd": 1.3767958938540341, "lo": 219.29756797492982, "hi": 221.26723202507017, "vals": [223.567, 220.331, 221.528, 219.891, 219.544, 220.474, 219.854, 219.674, 219.12, 218.841], "cv": 0.6250140246583632},
        "ratio": 0.9867470581120851,
        "diff": -1.3252941887914926,
        "t": -2.031107037486469,
        "overlap": True,
    },
    {
        "benchmark": "disk_seq",
        "category": "disco",
        "metric": "read_throughput",
        "unit": "MiB/s",
        "native": {"mean": 1114.9211, "sd": 6.433246812026145, "lo": 1110.3193521926844, "hi": 1119.5228478073157, "vals": [1117.488, 1107.292, 1107.46, 1118.583, 1104.093, 1120.761, 1121.717, 1116.551, 1114.19, 1121.076], "cv": 0.5770136390840701},
        "docker": {"mean": 1107.6217, "sd": 21.6688207957373, "lo": 1092.1218363234661, "hi": 1123.1215636765337, "vals": [1065.211, 1083.95, 1124.645, 1090.095, 1121.91, 1129.235, 1102.238, 1125.736, 1110.263, 1122.934], "cv": 1.9563376914462132},
        "ratio": 0.9934529896330779,
        "diff": -0.6547010366922068,
        "t": -1.0211953209998288,
        "overlap": True,
    },
    {
        "benchmark": "disk_seq",
        "category": "disco",
        "metric": "write_throughput",
        "unit": "MiB/s",
        "native": {"mean": 1304.9276, "sd": 175.7441063852656, "lo": 1179.2165741622803, "hi": 1430.6386258377197, "vals": [1304.394, 1368.43, 1363.129, 1339.895, 1373.122, 1374.089, 1359.662, 1383.866, 1373.687, 809.002], "cv": 13.46772850733371},
        "docker": {"mean": 2556.6334, "sd": 139.5057761712954, "lo": 2456.843912924198, "hi": 2656.4228870758025, "vals": [2569.782, 2413.877, 2566.116, 2764.445, 2275.493, 2688.784, 2549.997, 2490.778, 2596.203, 2650.859], "cv": 5.456620263636366},
        "ratio": 1.9592147487722693,
        "diff": 95.92147487722693,
        "t": 17.640536491697745,
        "overlap": False,
    },
    {
        "benchmark": "fork_wait",
        "category": "cpu",
        "metric": "time_per_op",
        "unit": "ns/op",
        "native": {"mean": 141112.9787, "sd": 2280.166717697685, "lo": 139481.95901428477, "hi": 142743.99838571524, "vals": [143001.326, 143590.271, 143687.204, 142265.743, 142144.656, 140727.57, 141367.03, 138152.448, 138766.43, 137427.109], "cv": 1.6158447923810177},
        "docker": {"mean": 143970.4801, "sd": 2518.9580995693227, "lo": 142168.65121792693, "hi": 145772.30898207304, "vals": [143459.307, 142806.389, 147666.439, 149271.59, 144668.987, 142840.041, 142481.59, 142136.264, 142086.58, 142287.614], "cv": 1.749635132021292},
        "ratio": 1.0202497419183172,
        "diff": 2.024974191831719,
        "t": 2.659515087937098,
        "overlap": True,
    },
    {
        "benchmark": "pipe_pingpong",
        "category": "cpu",
        "metric": "time_per_roundtrip",
        "unit": "ns/roundtrip",
        "native": {"mean": 10475.6271, "sd": 38.78294877176479, "lo": 10447.885377245313, "hi": 10503.368822754686, "vals": [10496.911, 10488.14, 10437.875, 10426.626, 10491.754, 10501.544, 10480.352, 10404.056, 10515.35, 10513.663], "cv": 0.3702207839353578},
        "docker": {"mean": 10177.2103, "sd": 30.497376029386047, "lo": 10155.395307139823, "hi": 10199.025292860179, "vals": [10222.037, 10168.87, 10147.263, 10181.253, 10178.279, 10197.204, 10195.593, 10210.176, 10143.103, 10128.325], "cv": 0.2996634159106061},
        "ratio": 0.9715132280720455,
        "diff": -2.8486771927954457,
        "t": -19.126896603392623,
        "overlap": False,
    },
    {
        "benchmark": "syscall_getpid",
        "category": "cpu",
        "metric": "time_per_op",
        "unit": "ns/op",
        "native": {"mean": 649.9768, "sd": 3.06997176244704, "lo": 647.7808270738637, "hi": 652.1727729261363, "vals": [649.608, 646.832, 656.134, 652.814, 649.146, 647.456, 650.426, 647.745, 646.927, 652.68], "cv": 0.47232020626690674},
        "docker": {"mean": 901.2305, "sd": 143.32761303566036, "lo": 798.7072254721709, "hi": 1003.7537745278291, "vals": [1008.113, 1020.153, 1006.963, 1003.756, 999.822, 1000.876, 859.4, 706.017, 701.771, 705.434], "cv": 15.903546654896871},
        "ratio": 1.3865579509914816,
        "diff": 38.65579509914816,
        "t": 5.542210243759896,
        "overlap": False,
    },
]

ENV_DATA = {
    "native": {
        "env": "native",
        "data": "2026-11-11T18:46:05Z",
        "runs": "10   cpu_fixada: 2",
        "kernel": "Linux rodrigoleptop 7.3.0-4-cachyos #1 SMP PREEMPT_DYNAMIC Fri, 23 Oct 2026 15:03:58 +0000 x86_64 GNU/Linux",
        "cpu": "AMD Ryzen 7 5825U with Radeon Graphics",
        "nucleos_visiveis": "16",
        "thp": "[always] madvise never",
        "gcc": "gcc (GCC) 16.2.1 20260810",
        "disk_dir": "/home/rodrigo/bench_data",
        "filesystem_do_disk_dir": "/dev/nvme0n1p2 btrfs    499580928 99223188  398936284  20% /home",
    },
    "docker-bind": {
        "env": "docker-bind",
        "data": "2026-11-11T19:07:31Z",
        "runs": "10   cpu_fixada: nao",
        "kernel": "Linux 5b93d1ce4197 7.3.3-1-cachyos #1 SMP PREEMPT_DYNAMIC Sat, 07 Nov 2026 13:54:44 +0000 x86_64 GNU/Linux",
        "cpu": "AMD Ryzen 7 5825U with Radeon Graphics",
        "nucleos_visiveis": "1",
        "thp": "[always] madvise never",
        "disk_dir": "/data",
        "filesystem_do_disk_dir": "/dev/nvme0n1p2 btrfs 499580928 97816776 400247080  20% /data",
    },
}

# Mantém o estado atual em memória (sem precisar de banco de dados)
CURRENT_DATA = copy.deepcopy(RAW_DATA)


def index(request):
    """Renderiza o template principal do painel."""
    return render(request, "painel_benchmarks.html")


def api_benchmarks(request):
    """Endpoint JSON que responde às opções selecionadas no menu."""
    global CURRENT_DATA

    action = request.GET.get("action")

    if action == "reset":
        CURRENT_DATA = copy.deepcopy(RAW_DATA)
    elif action == "simulate":
        # Simula variação de nova rodada no Docker (substituível por leitura de CSV/subprocess)
        for item in CURRENT_DATA:
            fator = 1.0 + random.uniform(-0.04, 0.04)
            docker = item["docker"]
            docker["vals"] = [round(v * fator, 3) for v in docker["vals"]]
            docker["mean"] = sum(docker["vals"]) / len(docker["vals"])
            docker["lo"] *= fator
            docker["hi"] *= fator

            item["ratio"] = docker["mean"] / item["native"]["mean"]
            item["diff"] = (item["ratio"] - 1.0) * 100.0
            # Verifica sobreposição dos ICs 95%
            item["overlap"] = not (
                docker["lo"] > item["native"]["hi"] or item["native"]["lo"] > docker["hi"]
            )

    # Leitura dos parâmetros do menu
    category = request.GET.get("category", "all")
    sig = request.GET.get("sig", "all")
    sort_by = request.GET.get("sort", "default")

    filtered = list(CURRENT_DATA)

    if category != "all":
        filtered = [d for d in filtered if d["category"] == category]

    if sig == "sig":
        filtered = [d for d in filtered if not d["overlap"]]
    elif sig == "nonsig":
        filtered = [d for d in filtered if d["overlap"]]

    if sort_by == "diff_desc":
        filtered.sort(key=lambda d: abs(d["diff"]), reverse=True)
    elif sort_by == "t_desc":
        filtered.sort(key=lambda d: abs(d["t"]), reverse=True)

    return JsonResponse({
        "data": filtered,
        "all_data": CURRENT_DATA,
        "env": ENV_DATA,
    })