#include "npy.h"

import std;

import ptfkit.li2007;
import ptfkit.mayr1999;
import ptfkit.dharumarajan2019;

namespace {

namespace fs = std::filesystem;

struct FreeDeleter {
    void operator()(double *values) const { std::free(values); }
};

using NpyBuffer = std::unique_ptr<double[], FreeDeleter>;

void print_record(std::string_view name, std::size_t samples, auto elapsed) {
    auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(elapsed).count();
    std::println("{{\"target\":\"cpp\",\"case\":\"{}\",\"samples\":{},\"elapsed_ns\":{}}}", name,
                 samples, ns);
}

void observe(const std::vector<double> &values) {
    double total = 0.0;
    for (double value : values) {
        total += value;
    }
    volatile double observed = total;
    (void)observed;
}

} // namespace

int main(int argc, char *argv[]) {
    if (argc < 3 || argc > 4) {
        std::println(stderr, "usage: ptfkit-cpp-benchmarks DATASET WARMUPS [LIMIT]");
        return 2;
    }

    const fs::path dataset = argv[1];
    const auto warmups = static_cast<std::size_t>(std::stoull(argv[2]));

    std::size_t samples;
    const auto load_input = [&dataset, &samples](const char *name) {
        return NpyBuffer{load_npy_f64((dataset / name).c_str(), &samples)};
    };
    auto sand = load_input("sand.npy");
    auto silt = load_input("silt.npy");
    auto clay = load_input("clay.npy");
    auto bulk_density = load_input("bulk_density.npy");
    auto organic_carbon = load_input("organic_carbon.npy");
    const auto limit = argc == 4 ? static_cast<std::size_t>(std::stoull(argv[3])) : samples;

    std::vector<double> infiltration(limit);
    std::vector<double> mayr_a_hc(limit);
    std::vector<double> mayr_b_hc(limit);
    std::vector<double> mayr_theta_s(limit);
    std::vector<double> li_theta_s(limit);
    std::vector<double> li_a_vg(limit);
    std::vector<double> li_n_vg(limit);
    std::vector<double> li_k_sat(limit);

    for (std::size_t iteration = 0; iteration <= warmups; ++iteration) {
        const auto started = std::chrono::steady_clock::now();
        for (std::size_t index = 0; index < limit; ++index) {
            infiltration[index] = ptfkit::dharumarajan2019::calc_ptf_dharumarajan2019_infiltration(
                sand[index], silt[index], clay[index]);
        }
        const auto elapsed = std::chrono::steady_clock::now() - started;
        observe(infiltration);
        if (iteration == warmups) {
            print_record("dharumarajan2019_infiltration", limit, elapsed);
        }
    }
    for (std::size_t iteration = 0; iteration <= warmups; ++iteration) {
        const auto started = std::chrono::steady_clock::now();
        for (std::size_t index = 0; index < limit; ++index) {
            const auto result = ptfkit::mayr1999::calc_ptf_mayr1999(
                sand[index], silt[index], clay[index], bulk_density[index], organic_carbon[index]);
            mayr_a_hc[index] = result.a_hc;
            mayr_b_hc[index] = result.b_hc;
            mayr_theta_s[index] = result.theta_s;
        }
        const auto elapsed = std::chrono::steady_clock::now() - started;
        observe(mayr_a_hc);
        observe(mayr_b_hc);
        observe(mayr_theta_s);
        if (iteration == warmups) {
            print_record("mayr1999", limit, elapsed);
        }
    }
    for (std::size_t iteration = 0; iteration <= warmups; ++iteration) {
        const auto started = std::chrono::steady_clock::now();
        for (std::size_t index = 0; index < limit; ++index) {
            const auto result = ptfkit::li2007::calc_ptf_li2007(
                sand[index], silt[index], clay[index], bulk_density[index], organic_carbon[index]);
            li_theta_s[index] = result.theta_s;
            li_a_vg[index] = result.a_vg;
            li_n_vg[index] = result.n_vg;
            li_k_sat[index] = result.k_sat;
        }
        const auto elapsed = std::chrono::steady_clock::now() - started;
        observe(li_theta_s);
        observe(li_a_vg);
        observe(li_n_vg);
        observe(li_k_sat);
        if (iteration == warmups) {
            print_record("li2007", limit, elapsed);
        }
    }

    return 0;
}
