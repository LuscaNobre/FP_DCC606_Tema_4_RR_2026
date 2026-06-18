#include "diagnostics.h"

#include <fstream>
#include <iostream>
#include <iomanip>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>

namespace fp_dcc606 {
namespace {

std::string read_file(const std::string& path) {
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        throw std::runtime_error("failed to open json file: " + path);
    }
    std::ostringstream buffer;
    buffer << input.rdbuf();
    return buffer.str();
}

std::string extract_string(const std::string& json, const std::string& key) {
    std::regex pattern("\\\"" + key + "\\\"\\s*:\\s*\\\"([^\\\"]*)\\\"");
    std::smatch match;
    if (std::regex_search(json, match, pattern)) {
        return match[1].str();
    }
    return {};
}

int extract_int(const std::string& json, const std::string& key, int fallback = 0) {
    std::regex pattern("\\\"" + key + "\\\"\\s*:\\s*(-?[0-9]+)");
    std::smatch match;
    if (std::regex_search(json, match, pattern)) {
        return std::stoi(match[1].str());
    }
    return fallback;
}

double extract_double(const std::string& json, const std::string& key, double fallback = 0.0) {
    std::regex pattern("\\\"" + key + "\\\"\\s*:\\s*(-?[0-9]+(?:\\.[0-9]+)?)");
    std::smatch match;
    if (std::regex_search(json, match, pattern)) {
        return std::stod(match[1].str());
    }
    return fallback;
}

std::string pad_to_width(const std::string& text, std::size_t width) {
    // Count UTF-8 codepoints (approximate display width)
    std::size_t chars = 0;
    for (std::size_t i = 0; i < text.size();) {
        unsigned char c = static_cast<unsigned char>(text[i]);
        std::size_t step = 1;
        if ((c & 0x80) == 0x00) step = 1;
        else if ((c & 0xE0) == 0xC0) step = 2;
        else if ((c & 0xF0) == 0xE0) step = 3;
        else if ((c & 0xF8) == 0xF0) step = 4;
        else step = 1;
        i += step;
        ++chars;
    }
    if (chars >= width) return text;
    return text + std::string(width - chars, ' ');
}

std::string format_fixed(double value) {
    std::ostringstream stream;
    stream << std::fixed << std::setprecision(2) << value;
    return stream.str();
}

std::string box_line(const std::string& text) {
    constexpr std::size_t inner_width = 36;
    return "║ " + pad_to_width(text, inner_width - 2) + " ║\n";
}

} // namespace

std::string format_result_from_json(const std::string& json_path) {
    const std::string json = read_file(json_path);
    const std::string status = extract_string(json, "status");
    const std::string reachability = extract_string(json, "error_state");
    const std::string invariant = extract_string(json, "invariant_text");
    const int active = extract_int(json, "active_restrictions");
    const int total = extract_int(json, "total_restrictions");
    const double time_ms = extract_double(json, "time_ms");
    const double mip_gap = extract_double(json, "mip_gap") * 100.0;

    std::ostringstream out;
    out << "╔══════════════════════════════════════╗\n";
    out << box_line("RESULTADO DA VERIFICAÇÃO FORMAL");
    out << "╠══════════════════════════════════════╣\n";
    out << box_line("Status: " + status);
    out << box_line("Estado de erro: " + reachability);
    out << "╠══════════════════════════════════════╣\n";
    out << box_line("INVARIANTE INDUTIVO SINTETIZADO:");
    out << box_line("  " + invariant);
    out << box_line("  (restrições ativas: " + std::to_string(active) + " de " + std::to_string(total) + ")");
    out << "╠══════════════════════════════════════╣\n";
    out << box_line("Tempo Branch-and-Bound: " + format_fixed(time_ms) + " ms");
    out << box_line("MIP Gap final: " + format_fixed(mip_gap) + "%");
    out << "╚══════════════════════════════════════╝\n";
    return out.str();
}

void print_result_from_json(const std::string& json_path) {
    std::cout << format_result_from_json(json_path);
}

} // namespace fp_dcc606
