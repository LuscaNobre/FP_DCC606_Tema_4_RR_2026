#include "parser.h"

#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <functional>
#include <cctype>
#include <iterator>

namespace fp_dcc606 {
namespace {

std::string json_escape(const std::string& value) {
    std::string out;
    out.reserve(value.size() + 8);
    for (char ch : value) {
        switch (ch) {
            case '\\': out += "\\\\"; break;
            case '"': out += "\\\""; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default: out += ch; break;
        }
    }
    return out;
}

std::string vector_to_json(const Vector& values) {
    std::ostringstream oss;
    oss << '[';
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i != 0) {
            oss << ',';
        }
        oss << values[i];
    }
    oss << ']';
    return oss.str();
}

std::string matrix_to_json(const Matrix& values) {
    std::ostringstream oss;
    oss << '[';
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i != 0) {
            oss << ',';
        }
        oss << vector_to_json(values[i]);
    }
    oss << ']';
    return oss.str();
}

ProgramSpec make_bms_spec() {
    ProgramSpec spec;
    spec.case_name = "bms";
    spec.n_vars = 2;
    spec.A_init = {{1, 0}, {-1, 0}, {0, 1}, {0, -1}};
    spec.b_init = {0, 0, 10, -10};
    spec.A_trans = {{-1, 0, 1, 0}, {1, 0, -1, 0}, {0, -1, 0, 1}, {0, 1, 0, -1}, {1, 0, 0, 0}};
    spec.b_trans = {1, -1, -1, 1, 10};
    spec.A_error = {{1, 1}, {-1, -1}};
    spec.b_error = {25, -25};
    spec.initial_state = {0, 10};
    spec.update_deltas = {1, -1};
    spec.guard_var_index = 0;
    spec.guard_upper = 10;
    spec.error_linear_form = {1, 1};
    spec.error_threshold = 25;
    return spec;
}

ProgramSpec make_trivial_spec() {
    ProgramSpec spec;
    spec.case_name = "trivial";
    spec.n_vars = 1;
    spec.A_init = {{1}, {-1}};
    spec.b_init = {0, 0};
    spec.A_trans = {{-1, 1}, {1, -1}, {1, 0}};
    spec.b_trans = {1, -1, 4};
    spec.A_error = {{1}, {-1}};
    spec.b_error = {10, -10};
    spec.initial_state = {0};
    spec.update_deltas = {1};
    spec.guard_var_index = 0;
    spec.guard_upper = 4;
    spec.error_linear_form = {1};
    spec.error_threshold = 10;
    return spec;
}

ProgramSpec make_infeasible_spec() {
    ProgramSpec spec;
    spec.case_name = "infeasible";
    spec.n_vars = 1;
    spec.A_init = {{1}, {-1}};
    spec.b_init = {0, 0};
    spec.A_trans = {{-1, 1}, {1, -1}, {1, 0}};
    spec.b_trans = {1, -1, 9};
    spec.A_error = {{1}, {-1}};
    spec.b_error = {11, -11};
    spec.initial_state = {0};
    spec.update_deltas = {1};
    spec.guard_var_index = 0;
    spec.guard_upper = 9;
    spec.error_linear_form = {1};
    spec.error_threshold = 11;
    spec.force_infeasible = true;
    return spec;
}

ProgramSpec make_three_vars_spec() {
    ProgramSpec spec;
    spec.case_name = "3vars";
    spec.n_vars = 3;
    spec.A_init = {{1, 0, 0}, {-1, 0, 0}, {0, 1, 0}, {0, -1, 0}, {0, 0, 1}, {0, 0, -1}};
    spec.b_init = {0, 0, 10, -10, 5, -5};
    spec.A_trans = {
        {-1, 0, 1, 0, 0, 0},
        {1, 0, -1, 0, 0, 0},
        {0, -1, 0, 1, 0, 0},
        {0, 1, 0, -1, 0, 0},
        {0, 0, -1, 0, 1, 0},
        {0, 0, 1, 0, -1, 0},
        {1, 0, 0, 0, 0, 0}
    };
    spec.b_trans = {1, -1, -1, 1, 2, -2, 5};
    spec.A_error = {{1, 1, 1}, {-1, -1, -1}};
    spec.b_error = {100, -100};
    spec.initial_state = {0, 10, 5};
    spec.update_deltas = {1, -1, 2};
    spec.guard_var_index = 0;
    spec.guard_upper = 5;
    spec.error_linear_form = {1, 1, 1};
    spec.error_threshold = 100;
    return spec;
}

std::string spec_to_json(const ProgramSpec& spec) {
    std::ostringstream oss;
    oss << "{\n";
    oss << "  \"case_name\": \"" << json_escape(spec.case_name) << "\",\n";
    oss << "  \"n_vars\": " << spec.n_vars << ",\n";
    oss << "  \"A_init\": " << matrix_to_json(spec.A_init) << ",\n";
    oss << "  \"b_init\": " << vector_to_json(spec.b_init) << ",\n";
    oss << "  \"A_trans\": " << matrix_to_json(spec.A_trans) << ",\n";
    oss << "  \"b_trans\": " << vector_to_json(spec.b_trans) << ",\n";
    oss << "  \"A_error\": " << matrix_to_json(spec.A_error) << ",\n";
    oss << "  \"b_error\": " << vector_to_json(spec.b_error) << ",\n";
    oss << "  \"initial_state\": " << vector_to_json(spec.initial_state) << ",\n";
    oss << "  \"update_deltas\": " << vector_to_json(spec.update_deltas) << ",\n";
    oss << "  \"guard_var_index\": " << spec.guard_var_index << ",\n";
    oss << "  \"guard_upper\": " << spec.guard_upper << ",\n";
    oss << "  \"error_linear_form\": " << vector_to_json(spec.error_linear_form) << ",\n";
    oss << "  \"error_threshold\": " << spec.error_threshold << ",\n";
    oss << "  \"force_infeasible\": " << (spec.force_infeasible ? "true" : "false") << "\n";
    oss << "}\n";
    return oss.str();
}

ProgramSpec spec_from_name(const std::string& case_name) {
    if (case_name == "bms") {
        return make_bms_spec();
    }
    if (case_name == "trivial") {
        return make_trivial_spec();
    }
    if (case_name == "infeasible") {
        return make_infeasible_spec();
    }
    if (case_name == "3vars" || case_name == "threevars" || case_name == "three-vars") {
        return make_three_vars_spec();
    }
    throw std::invalid_argument("unknown case: " + case_name);
}

} // namespace

ProgramSpec parse_bms() {
    return make_bms_spec();
}

ProgramSpec parse_case_trivial() {
    return make_trivial_spec();
}

ProgramSpec parse_case_infeasible() {
    return make_infeasible_spec();
}

ProgramSpec parse_case_3vars() {
    return make_three_vars_spec();
}

ProgramSpec parse_case(const std::string& case_name) {
    // If argument is a JSON file path, try to parse it
    std::ifstream f(case_name);
    if (f) {
        f.close();
        return parse_file(case_name);
    }
    return spec_from_name(case_name);
}

ProgramSpec parse_file(const std::string& filepath) {
    std::ifstream input(filepath);
    if (!input) {
        throw std::runtime_error("failed to open spec file: " + filepath);
    }
    std::string content((std::istreambuf_iterator<char>(input)), std::istreambuf_iterator<char>());

    auto skip_ws = [&](size_t &pos) {
        while (pos < content.size() && isspace((unsigned char)content[pos])) ++pos;
    };

    auto parse_number = [&](size_t &pos)->int {
        skip_ws(pos);
        size_t start = pos;
        if (pos < content.size() && (content[pos] == '-' || content[pos] == '+')) ++pos;
        while (pos < content.size() && (isdigit((unsigned char)content[pos]))) ++pos;
        std::string token = content.substr(start, pos - start);
        return std::stoi(token);
    };

    std::function<std::vector<int>(size_t&)> parse_vector = [&](size_t &pos)->std::vector<int> {
        std::vector<int> out;
        skip_ws(pos);
        if (pos >= content.size() || content[pos] != '[') throw std::runtime_error("expected [ for array");
        ++pos;
        skip_ws(pos);
        while (pos < content.size() && content[pos] != ']') {
            int v = parse_number(pos);
            out.push_back(v);
            skip_ws(pos);
            if (pos < content.size() && content[pos] == ',') { ++pos; skip_ws(pos); }
        }
        if (pos >= content.size() || content[pos] != ']') throw std::runtime_error("expected closing ] for array");
        ++pos;
        return out;
    };

    std::function<std::vector<std::vector<int>>(size_t&)> parse_matrix = [&](size_t &pos)->std::vector<std::vector<int>> {
        std::vector<std::vector<int>> out;
        skip_ws(pos);
        if (pos >= content.size() || content[pos] != '[') throw std::runtime_error("expected [ for matrix");
        ++pos;
        skip_ws(pos);
        while (pos < content.size() && content[pos] != ']') {
            skip_ws(pos);
            if (content[pos] == '[') {
                auto row = parse_vector(pos);
                out.push_back(row);
            } else {
                // empty or malformed
                throw std::runtime_error("expected matrix row");
            }
            skip_ws(pos);
            if (pos < content.size() && content[pos] == ',') { ++pos; skip_ws(pos); }
        }
        if (pos >= content.size() || content[pos] != ']') throw std::runtime_error("expected closing ] for matrix");
        ++pos;
        return out;
    };

    auto extract_field = [&](const std::string &key)->std::string {
        std::string needle = '"' + key + '"';
        size_t p = content.find(needle);
        if (p == std::string::npos) return std::string();
        size_t colon = content.find(':', p + needle.size());
        if (colon == std::string::npos) return std::string();
        size_t pos = colon + 1;
        skip_ws(pos);
        // return substring from pos for manual parsing
        return content.substr(pos);
    };

    ProgramSpec spec;
    // Parse simple fields by searching keys and using the above parsers
    auto parse_key_matrix = [&](const std::string &key, std::vector<std::vector<int>> &out) {
        std::string needle = '"' + key + '"';
        size_t p = content.find(needle);
        if (p == std::string::npos) return;
        size_t colon = content.find(':', p + needle.size());
        size_t pos = colon + 1;
        skip_ws(pos);
        out = parse_matrix(pos);
    };
    auto parse_key_vector = [&](const std::string &key, std::vector<int> &out) {
        std::string needle = '"' + key + '"';
        size_t p = content.find(needle);
        if (p == std::string::npos) return;
        size_t colon = content.find(':', p + needle.size());
        size_t pos = colon + 1;
        skip_ws(pos);
        out = parse_vector(pos);
    };
    auto parse_key_int = [&](const std::string &key, int &out) {
        std::string needle = '"' + key + '"';
        size_t p = content.find(needle);
        if (p == std::string::npos) return;
        size_t colon = content.find(':', p + needle.size());
        size_t pos = colon + 1;
        out = parse_number(pos);
    };
    auto parse_key_bool = [&](const std::string &key, bool &out) {
        std::string needle = '"' + key + '"';
        size_t p = content.find(needle);
        if (p == std::string::npos) return;
        size_t colon = content.find(':', p + needle.size());
        size_t pos = colon + 1;
        skip_ws(pos);
        if (content.compare(pos, 4, "true") == 0) { out = true; }
        else { out = false; }
    };

    // Fill fields
    std::vector<std::vector<int>> tmpm;
    std::vector<int> tmpv;
    parse_key_matrix("A_init", spec.A_init);
    parse_key_vector("b_init", spec.b_init);
    parse_key_matrix("A_trans", spec.A_trans);
    parse_key_vector("b_trans", spec.b_trans);
    parse_key_matrix("A_error", spec.A_error);
    parse_key_vector("b_error", spec.b_error);
    parse_key_vector("initial_state", spec.initial_state);
    parse_key_vector("update_deltas", spec.update_deltas);
    parse_key_vector("error_linear_form", spec.error_linear_form);
    parse_key_int("n_vars", spec.n_vars);
    parse_key_int("guard_var_index", spec.guard_var_index);
    parse_key_int("guard_upper", spec.guard_upper);
    parse_key_int("error_threshold", spec.error_threshold);
    parse_key_bool("force_infeasible", spec.force_infeasible);

    // Try to find case_name
    size_t pn = content.find("\"case_name\"");
    if (pn != std::string::npos) {
        size_t colon = content.find(':', pn + 12);
        size_t pos = colon + 1;
        skip_ws(pos);
        if (pos < content.size() && content[pos] == '"') {
            ++pos;
            size_t end = content.find('"', pos);
            if (end != std::string::npos) spec.case_name = content.substr(pos, end - pos);
        }
    } else {
        spec.case_name = filepath;
    }

    return spec;
}

void export_to_json(const ProgramSpec& spec, const std::string& filename) {
    std::ofstream output(filename, std::ios::binary);
    if (!output) {
        throw std::runtime_error("failed to open output file: " + filename);
    }
    output << spec_to_json(spec);
}

} // namespace fp_dcc606

#ifndef PARSER_LIBRARY
int main(int argc, char** argv) {
    using namespace fp_dcc606;
    std::string case_name = "bms";
    std::string output_file = "spec.json";
    bool print_stdout = false;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--case" && i + 1 < argc) {
            case_name = argv[++i];
        } else if (arg == "--output" && i + 1 < argc) {
            output_file = argv[++i];
        } else if (arg == "--stdout") {
            print_stdout = true;
        }
    }

    try {
        ProgramSpec spec = parse_case(case_name);
        export_to_json(spec, output_file);
        if (print_stdout) {
            std::cout << spec.case_name << "\n";
        }
        return 0;
    } catch (const std::exception& ex) {
        std::cerr << "parser error: " << ex.what() << '\n';
        return 1;
    }
}
#endif
