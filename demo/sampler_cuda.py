import time

from eacgm.bpf import BccBPF
from eacgm.sampler import eBPFSampler

text = """
// #include <cuda_runtime.h>
#include <uapi/linux/ptrace.h>

struct dim3 {
    unsigned int x, y, z;
};

int cudaMallocEntry(struct pt_regs *ctx){
    u64 malloc_ptr = PT_REGS_PARM1(ctx);
    u64 byte_length = PT_REGS_PARM2(ctx);
    u64 ts = bpf_ktime_get_ns();
    bpf_trace_printk("%ld start cudaMalloc %ld %ld\\n", ts, malloc_ptr, byte_length);
    return 0;
};

int cudaMallocExit(struct pt_regs *ctx){
    u64 ts = bpf_ktime_get_ns();
    bpf_trace_printk("%ld end cudaMalloc\\n", ts);
    return 0;
};

int cudaMemcpyEntry(struct pt_regs *ctx){
    u64 byte_length = PT_REGS_PARM3(ctx);
    u64 memcpy_kind = PT_REGS_PARM4(ctx);
    u64 ts = bpf_ktime_get_ns();
    bpf_trace_printk("%ld start cudaMemcpy %ld %ld\\n", ts, memcpy_kind);
    return 0;
};

int cudaMemcpyExit(struct pt_regs *ctx){
    u64 ts = bpf_ktime_get_ns();
    bpf_trace_printk("%ld end cudaMemcpy\\n", ts);
    return 0;
};

int cudaFreeEntry(struct pt_regs *ctx){
    u64 malloc_ptr = PT_REGS_PARM1(ctx);
    u64 ts = bpf_ktime_get_ns();
    bpf_trace_printk("%ld start cudaFree %ld\\n", malloc_ptr, ts);
    return 0;
};

int cudaFreeExit(struct pt_regs *ctx){
    u64 ts = bpf_ktime_get_ns();
    bpf_trace_printk("%ld end cudaFree\\n", ts);
    return 0;
};

int cudaLaunchKernelEntry(struct pt_regs *ctx){
    u64 ts = bpf_ktime_get_ns();
    struct dim3* gridDim = PT_REGS_PARM2(ctx);
    struct dim3* blockDim = PT_REGS_PARM3(ctx);
    u64 shared_mem = PT_REGS_PARM5(ctx);
    u64 stream_num = gridDim->x * gridDim->y * gridDim->z * blockDim->x * blockDim->y * blockDim->z;
    bpf_trace_printk("%ld start cudaLaunchKernel %ld %ld\\n", ts, stream_num, shared_mem);
    return 0;
};

int cudaLaunchKernelExit(struct pt_regs *ctx){
    u64 ts = bpf_ktime_get_ns();
    bpf_trace_printk("%ld end cudaLaunchKernel\\n", ts);
    return 0;
};
"""

bpf = BccBPF("CUDAeBPF", text, ["-w", "-I/usr/local/cuda/include"])

attach_config = [
    {
        "name": "CUDASampler",
        "exe_path": [
            "/home/msc-user/miniconda3/envs/py312-torch24-cu124/lib/python3.12/site-packages/nvidia/cuda_runtime/lib/libcudart.so.12",
        ],
        "exe_sym": [
            "cudaMalloc",
            "cudaMemcpy",
            "cudaFree",
            "cudaLaunchKernel",
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