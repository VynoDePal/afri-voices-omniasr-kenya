# Environment

The notebooks target Google Colab with Python 3.12. The requirement file captures
the main Python surface, while individual setup cells pin binary or stage-specific
versions. CUDA-enabled PyTorch must match the selected Colab image; do not install
a CPU wheel over an existing GPU runtime.

KenLM is built from source in K3 at the revision recorded by that notebook. System
packages include a C++ toolchain, CMake, Boost, Eigen, `liblzma`, `zlib`, and
`libsndfile`.

Binary dependency realignment can require one Colab runtime restart. K4 and K6
print an explicit restart instruction when this happens.

