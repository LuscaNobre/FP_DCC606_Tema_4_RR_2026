#pragma once

#include <string>
#include <vector>

namespace fp_dcc606 {

using Matrix = std::vector<std::vector<int>>;
using Vector = std::vector<int>;

struct ProgramSpec {
    std::string case_name;
    int n_vars{};
    Matrix A_init;
    Vector b_init;
    Matrix A_trans;
    Vector b_trans;
    Matrix A_error;
    Vector b_error;
    Vector initial_state;
    Vector update_deltas;
    int guard_var_index{};
    int guard_upper{};
    Vector error_linear_form;
    int error_threshold{};
    bool force_infeasible{false};
};

ProgramSpec parse_bms();
ProgramSpec parse_case_trivial();
ProgramSpec parse_case_infeasible();
ProgramSpec parse_case_3vars();
ProgramSpec parse_case(const std::string& case_name);
ProgramSpec parse_file(const std::string& filepath);
void export_to_json(const ProgramSpec& spec, const std::string& filename);

} // namespace fp_dcc606
