#include <array>
#include <cstdio>
#include <cstdlib>
import ptfkit;
int main(int argc, char **argv) {
    if (argc != 6)
        return 2;
    try {
        auto model = ptfkit::Euptf2Ths::load(argv[1]);
        std::array<double, 4> inputs;
        for (size_t i = 0; i < 4; ++i)
            inputs[i] = std::strtod(argv[i + 2], nullptr);
        for (double value : model.predict(inputs))
            std::printf("%.17g\n", value);
        return 0;
    } catch (const ptfkit::ModelError &error) {
        return 10 + static_cast<int>(error.status);
    }
}
