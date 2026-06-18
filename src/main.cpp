#include "diagnostics.h"
#include "parser.h"

#include <cstdlib>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
    std::string case_name = "bms";
    std::string spec_path = "results/spec.json";
    std::string result_path = "results/result.json";

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--case" && i + 1 < argc) {
            case_name = argv[++i];
        } else if (arg == "--spec" && i + 1 < argc) {
            spec_path = argv[++i];
        } else if (arg == "--output" && i + 1 < argc) {
            result_path = argv[++i];
        }
    }

    try {
        fp_dcc606::ProgramSpec spec = fp_dcc606::parse_case(case_name);
        fp_dcc606::export_to_json(spec, spec_path);

        const std::string command_python3 = "python3 solver/milp_solver.py --input " + spec_path + " --output " + result_path;
        const std::string command_python = "python solver/milp_solver.py --input " + spec_path + " --output " + result_path;

        int status = std::system(command_python3.c_str());
        if (status != 0) {
            status = std::system(command_python.c_str());
        }
        if (status != 0) {
            std::cerr << "solver execution failed\n";
            return 1;
        }

        std::cout << fp_dcc606::format_result_from_json(result_path);
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "main error: " << ex.what() << '\n';
        return 1;
    }
}
