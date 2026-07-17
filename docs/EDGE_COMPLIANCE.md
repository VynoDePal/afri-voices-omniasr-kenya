# Edge and parameter compliance

## Neural parameter accounting

| Component | Parameters | Resident in final runtime |
|---|---:|---|
| BF16 step-1250 acoustic base | 975,675,056 | Yes |
| Maasai LoRA step 1250 | 9,898,496 | Yes, selected route only |
| Kalenjin LoRA step 1250 | 9,898,496 | No |
| **Final active total** | **985,573,552** | **Yes** |

KenLM n-grams are external statistical language-model tables, not trainable neural
parameters. They still count toward disk and RAM measurements, so the largest
decoder was included in the memory audit.

The upstream catalog historically listed 975,065,300 parameters for the CTC 1B
model. The serialized checkpoint used here contains 975,675,056 parameters. All
contracts and compliance decisions use the measured checkpoint value.

## Why the clean-worker audit is authoritative

An early audit inspected the Python process's lifetime maximum RSS after training
and reported 35.24 GiB. This was not the inference peak: `ru_maxrss` cannot reset,
so it included memory from earlier objects. The replacement audit launches a
fresh subprocess, samples the complete process tree externally, and terminates it
after the real probe. It therefore measures only the deployable runtime.

## K5 procedure

The CPU worker performed the following operations:

1. load the BF16 base exactly once;
2. load and validate the selected Maasai adapter;
3. construct and destroy all 12 language/domain decoders one at a time;
4. process two real development audios;
5. record process-tree RSS on an external interval;
6. verify that no more than one decoder was resident;
7. add a 15% safety margin to the observed peak.

| Measurement | Result |
|---|---:|
| Raw peak process-tree RSS | 5.586 GiB |
| Peak with 15% safety margin | 6.424 GiB |
| Allowed limit | 8.000 GiB |
| Margin to limit | 1.576 GiB |
| Worker timed out | No |
| Worker return code | 0 |

## Runtime controls

- one acoustic model;
- BF16 weight storage;
- only the selected LoRA resident;
- one lazy KenLM decoder at a time;
- explicit deletion and garbage collection on route change;
- batch size 1;
- segmented long audio rather than unbounded waveform tensors;
- shard caches stored outside the resident inference process.

This audit demonstrates the tested package under the recorded software and CPU
environment. It is not a universal guarantee for every Python allocator or edge
device; the 15% margin is intended to absorb reasonable variation.

