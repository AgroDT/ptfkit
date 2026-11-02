#include <array>
#include <cstdio>
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>
#include <cstring>
import ptfkit;
int main(int argc, char **argv) {
    if (argc >= 4 && std::strcmp(argv[1], "--collection") == 0) {
        try {
            auto model = ptfkit::Euptf2Model::load(argv[2], argv[3]);
            std::vector<double> probabilities;
            for (int i = 4; i < argc; ++i)
                probabilities.push_back(std::strtod(argv[i], nullptr));
            std::string line;
            while (std::getline(std::cin, line)) {
                std::istringstream row(line);
                std::string token;
                std::vector<double> inputs;
                while (row >> token) {
                    char *end;
                    double value = std::strtod(token.c_str(), &end);
                    if (*end)
                        break;
                    inputs.push_back(value);
                }
                try {
                    auto result = probabilities.empty() ? model.predict(inputs)
                                                        : model.predict(inputs, probabilities);
                    for (double v : result.mean)
                        std::printf("%.17g ", v);
                    for (const auto &q : result.quantiles)
                        for (double v : q)
                            std::printf("%.17g ", v);
                    std::putchar('\n');
                } catch (const ptfkit::ModelError &e) {
                    if (static_cast<int>(e.status) != 5)
                        throw;
                    std::puts("error15");
                }
            }
            return 0;
        } catch (const ptfkit::ModelError &e) {
            return 10 + static_cast<int>(e.status);
        }
    }
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
