CXX = g++
CXXFLAGS = -std=c++17 -Wall -Wextra -O2
SRC = src
SOLVER = solver

all: main

main: $(SRC)/main.cpp $(SRC)/parser.cpp $(SRC)/diagnostics.cpp $(SRC)/parser.h $(SRC)/diagnostics.h
	$(CXX) $(CXXFLAGS) -DPARSER_LIBRARY $(SRC)/main.cpp $(SRC)/parser.cpp $(SRC)/diagnostics.cpp -o main

parser: $(SRC)/parser.cpp $(SRC)/parser.h
	$(CXX) $(CXXFLAGS) $(SRC)/parser.cpp -o parser

install-deps:
	python -m pip install -r $(SOLVER)/requirements.txt

test: main
	python $(SOLVER)/milp_solver.py --input tests/case_bms.json --output results/bms_result.json
	python $(SOLVER)/milp_solver.py --input tests/case_trivial.json --output results/trivial_result.json
	python $(SOLVER)/milp_solver.py --input tests/case_infeasible.json --output results/infeasible_result.json
	python $(SOLVER)/milp_solver.py --input tests/case_3vars.json --output results/case3_result.json

clean:
	rm -f main.exe parser.exe results/spec.json results/result.json results/bms_result.json results/trivial_result.json results/infeasible_result.json results/case3_result.json

.PHONY: all install-deps clean
