import time

from eacgm.bpf import BccBPF
from eacgm.sampler import eBPFSampler

text = """
int ncclAllReduceEntry(struct pt_regs *ctx){
    u64 ts = bpf_ktime_get_ns();
    bpf_trace_printk("%ld start ncclAllReduce\\n", ts);
    return 0;
};

int ncclAllReduceExit(struct pt_regs *ctx){
    u64 ts = bpf_ktime_get_ns();
    bpf_trace_printk("%ld end ncclAllReduce\\n", ts);
    return 0;
};
"""

bpf = BccBPF("CUDAeBPF", text, ["-w"])

attach_config = [
    {
        "name": "CUDASampler",
        "exe_path": [
            "/home/msc-user/miniconda3/envs/py312-torch24-cu124/lib/python3.12/site-packages/nvidia/nccl/lib/libnccl.so.2",
        ],
        "exe_sym": [
            "ncclAllReduce",
        ]
    },
]

sampler = eBPFSampler(bpf)

sampler.run(attach_config)

while True:
    try:
        samples = sampler.sample(time_stamp=1)
        for sample in samples:
            print(sample)
        print("---")
    except KeyboardInterrupt:
        break

sampler.close()