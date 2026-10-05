
#include <chrono>
#include <cstdint>
#include <ctime>
#include <fstream>
#include <iostream>
#include <vector>
#include <zlib.h>

template<bool Buffered, typename Writer>
void emit_phases(size_t neurons, size_t rows, const std::vector<double>& v,
                 const std::vector<double>& g, const std::vector<double>& last,
                 const std::vector<uint8_t>& mask, Writer& write) {
    std::vector<double> times(rows);
    std::vector<uint8_t> canonical(neurons);
    for(size_t row=0; row<rows; ++row) times[row]=row*0.0001;
    for(int phase=0; phase<3; ++phase) {
        write(times.data(), rows*sizeof(double));
        for(size_t row=0; row<rows; ++row) write(v.data(), neurons*sizeof(double));
        for(size_t row=0; row<rows; ++row) write(g.data(), neurons*sizeof(double));
        if(phase==2) for(size_t row=0; row<rows; ++row) write(last.data(), neurons*sizeof(double));
        for(size_t row=0; row<rows; ++row) {
            if constexpr(Buffered) {
                for(size_t neuron=0; neuron<neurons; ++neuron) canonical[neuron]=mask[neuron] ? 1 : 0;
                write(canonical.data(), neurons);
            } else {
                for(size_t neuron=0; neuron<neurons; ++neuron) {
                    const uint8_t value=mask[neuron] ? 1 : 0;
                    write(&value, 1);
                }
            }
        }
    }
}

int main(int argc, char** argv) {
    if(argc!=3) return 2;
    const int mode=std::atoi(argv[1]);
    std::ifstream input(argv[2], std::ios::binary);
    uint64_t neurons, rows;
    input.read(reinterpret_cast<char*>(&neurons), 8);
    input.read(reinterpret_cast<char*>(&rows), 8);
    std::vector<double> v(neurons), g(neurons), last(neurons);
    std::vector<uint8_t> mask(neurons);
    input.read(reinterpret_cast<char*>(v.data()), neurons*8);
    input.read(reinterpret_cast<char*>(g.data()), neurons*8);
    input.read(reinterpret_cast<char*>(last.data()), neurons*8);
    input.read(reinterpret_cast<char*>(mask.data()), neurons);
    if(!input) return 3;

static_assert(sizeof(double)==8 && sizeof(int32_t)==4 && sizeof(uint64_t)==8, "Observer scalar widths differ");
static uint32_t obs_crc = 0xffffffffu;
static uint32_t obs_table[256];
for(uint32_t i=0; i<256; ++i) {
    uint32_t value=i;
    for(int bit=0; bit<8; ++bit) value = (value>>1) ^ ((value&1) ? 0xedb88320u : 0u);
    obs_table[i]=value;
}
static auto obs_write = [](const void* pointer, size_t size) {
    if(size) {
        const auto* data = static_cast<const unsigned char*>(pointer);
        std::cout.write(reinterpret_cast<const char*>(data), size);
        for(size_t i=0; i<size; ++i) obs_crc = (obs_crc>>8) ^ obs_table[(obs_crc^data[i])&255u];
    }
};
static auto obs_q = [](uint64_t value) { obs_write(&value, sizeof(value)); };
static auto obs_i = [](int32_t value) { obs_write(&value, sizeof(value)); };
static auto obs_d = [](double value) { obs_write(&value, sizeof(value)); };
static auto obs_finish = []() {
    const uint32_t value = obs_crc ^ 0xffffffffu;
    std::cout.write(reinterpret_cast<const char*>(&value), sizeof(value));
    obs_crc = 0xffffffffu;
};
static uint64_t obs_step = 0;

    auto fast_write = [](const void* pointer, size_t size) {
    if(size) {
        const auto* data = static_cast<const unsigned char*>(pointer);
        std::cout.write(reinterpret_cast<const char*>(data), size);
        obs_crc = static_cast<uint32_t>(crc32_z(obs_crc ^ 0xffffffffu, data, size)) ^ 0xffffffffu;
    }
};
    const auto began=std::chrono::steady_clock::now();
    const auto cpu_began=std::clock();
    if(mode==0) emit_phases<false>(neurons, rows, v, g, last, mask, obs_write);
    else if(mode==1) emit_phases<true>(neurons, rows, v, g, last, mask, obs_write);
    else if(mode==2) emit_phases<true>(neurons, rows, v, g, last, mask, fast_write);
    else return 4;
    obs_finish();
    std::cout.flush();
    const double elapsed=std::chrono::duration<double>(std::chrono::steady_clock::now()-began).count();
    const double cpu=static_cast<double>(std::clock()-cpu_began)/CLOCKS_PER_SEC;
    std::cerr << "{\"producer_wall_s\":" << elapsed << ",\"producer_cpu_s\":" << cpu << "}";
    return std::cout ? 0 : 5;
}
