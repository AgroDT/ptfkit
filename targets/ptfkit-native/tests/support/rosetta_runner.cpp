#include <cstdio>
#include <cstdlib>
#include <vector>
#include <array>
#include <cstring>
import ptfkit;
int main(int argc, char **argv) {
    if (argc < 7 || argc > 10)
        return 2;
    try {
        auto model = std::strcmp(argv[1], "--builtin") == 0 ? ptfkit::Rosetta3::builtin()
                                                            : ptfkit::Rosetta3::load(argv[1]);
        unsigned level = (unsigned)std::strtoul(argv[2], nullptr, 10),
                 mode = (unsigned)std::strtoul(argv[3], nullptr, 10);
        std::vector<double> x;
        for (int i = 4; i < argc; ++i)
            x.push_back(std::strtod(argv[i], nullptr));
        if (mode > 2)
            return 15;
        auto result = model.predict(level, static_cast<ptfkit::Estimate>(mode), x);
        if (mode == 0) {
            auto named =
                level == 2   ? ptfkit::calc_ptf_zhang2017_mod2(model, x[0], x[1], x[2])
                : level == 3 ? ptfkit::calc_ptf_zhang2017_mod3(model, x[0], x[1], x[2], x[3])
                : level == 4
                    ? ptfkit::calc_ptf_zhang2017_mod4(model, x[0], x[1], x[2], x[3], x[4])
                    : ptfkit::calc_ptf_zhang2017_mod5(model, x[0], x[1], x[2], x[3], x[4], x[5]);
            if (named.mean() != result.mean() || named.stddev() != result.stddev())
                return 30;
        }
        for (double v : result.mean())
            std::printf("%.17g\n", v);
        for (double v : result.stddev())
            std::printf("%.17g\n", v);
        return 0;
    } catch (const ptfkit::ModelError &error) {
        return 10 + static_cast<int>(error.status);
    }
}
