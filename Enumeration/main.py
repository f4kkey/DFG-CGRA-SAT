from pysat.formula import CNF
from pysat.solvers import Glucose3
from typing import List, Set, Dict, Tuple
import readCGRA
import readDFG
import time
var = 0
all_clauses = []

def atmost(k:int , nvar: list):
    global var, all_clauses
    
    # if(k==1):
    #     for i in range(len(nvar)):
    #         for j in range(i+1,len(nvar)):
    #             all_clauses.append([-nvar[i],-nvar[j]])
    #     return
    
    x = nvar.copy()
    x.insert(0,0)
    r = [[0 for _ in range(k+1)] for _ in range(len(nvar)+1)]
    for i in range(1,k+1):
        for j in range(1,i+1):
            var += 1
            r[i][j] = var
    for i in range(k+1,len(nvar)):
        for j in range(1,k+1):
            var += 1
            r[i][j] = var
            
    # 1
    for i in range (1,len(nvar)):
        all_clauses.append([-x[i],r[i][1]])
    
    # 2
    for i in range (2,len(nvar)):
        for j in range(1,min(i-1,k)+1):
            all_clauses.append([-r[i-1][j],r[i][j]])

    # 3
    for i in range(2,len(nvar)):
        for j in range(2,min(i,k)+1):
            all_clauses.append([-x[i],-r[i-1][j-1],r[i][j]])
    
    # 8
    for i in range(k+1,len(nvar)+1):
        all_clauses.append([-x[i],-r[i-1][k]])

def create_array(dim1: int, dim2: int, dim3: int):
    global var
    array = [[[0 for _ in range(dim3)] for _ in range(dim2)] for _ in range(dim1)]
    for i in range(dim1):
        for j in range(dim2):
            for k in range(dim3):
                var += 1
                array[i][j][k] = var
    return array

def create_extra_array(dim1: int, dim2: int, dim3: int, nodes: List):
    """Create 4D array where last dimension depends on number of operands for each node"""
    global var
    array = [[[[0 for _ in range(len(nodes[i].operands))] 
               for _ in range(dim3)]
              for _ in range(dim2)]
             for i in range(dim1)]
             
    for i in range(dim1):
        for j in range(dim2):
            for k in range(dim3):
                for z in range(len(nodes[i].operands)):
                    var += 1
                    array[i][j][k][z] = var
                    
    return array

def add_initial_conditions(X: List[List[List[int]]], nodes: List, components: List):
    # C1
    global all_clauses
    for i, node in enumerate(nodes):
        for j, comp_type in enumerate(components):
            if node.type == -1 and comp_type in [2, 3]: 
                all_clauses.append([X[i][j][0]]) 
            else:
                all_clauses.append([-X[i][j][0]])

def add_final_conditions(X: List[List[List[int]]], nodes: List, num_cycles: int):
    # C3
    global all_clauses
    extmem_id = 0
    for i, node in enumerate(nodes):
        if node.is_output:
            all_clauses.append([X[i][extmem_id][num_cycles-1]])

def get_incoming_paths(j: int, edges_cgra: List):
    return [h for h, edge in enumerate(edges_cgra) if edge.v == j]

def get_source_component(h: int, edges_cgra: List):
    return edges_cgra[h].u

def add_existence_constraints(X: List[List[List[int]]], Y: List[List[List[int]]], 
                            Z: List[List[List[int]]], nodes: List, components: List, 
                            edges_cgra: List):
    # C4
    global all_clauses
    for i in range(len(nodes)):
        for j in range(len(components)):
            for k in range(1, len(X[0][0])):
                H_j = get_incoming_paths(j, edges_cgra)
                
                clause = [-X[i][j][k], X[i][j][k-1]]
                for h in H_j:
                    clause.append(Y[i][h][k])
                if components[j] == 1 and nodes[i].type >= 0: 
                    clause.append(Z[i][j][k])
                all_clauses.append(clause)

def add_communication_constraints(X: List[List[List[int]]], Y: List[List[List[int]]], 
                                nodes: List, edges_cgra: List):
    # C5
    global all_clauses
    for i in range(len(nodes)):
        for h, edge in enumerate(edges_cgra):
            for k in range(1, len(X[0][0])):
                all_clauses.append([-Y[i][h][k], X[i][edge.u][k-1]])

def add_calculation_constraints(X: List[List[List[int]]], Y: List[List[List[int]]], 
                              Z: List[List[List[int]]], S: List[List[List[int]]], nodes: List, components: List, 
                              edges_cgra: List):
    # C6,7
    global all_clauses
    for i, node in enumerate(nodes):
        for j in range(len(components)):
            for k in range(1, len(X[0][0])):
                if node.type >= 0 and components[j] == 1:
                    for z in range(len(node.operands)):
                        H_j = get_incoming_paths(j, edges_cgra)
                        for operand in node.operands[z]:
                            clause = [-S[i][j][k][z], X[operand.id][j][k-1]]
                            for h in H_j:
                                clause.append(Y[operand.id][h][k])
                            all_clauses.append(clause)
                            
                    clause = [-Z[i][j][k]]
                    for z in range(len(node.operands)):
                        clause.append(S[i][j][k][z])
                    all_clauses.append(clause)
                    
                    # H_j = get_incoming_paths(j, edges_cgra)
                    # for operand in node.operands[0]:
                    #     clause = [-Z[i][j][k], X[operand.id][j][k-1]]
                    #     for h in H_j:
                    #         clause.append(Y[operand.id][h][k])
                    #     all_clauses.append(clause)
                else:
                    all_clauses.append([-Z[i][j][k]])

def add_capacity_constraints(X: List[List[List[int]]], Y: List[List[List[int]]], 
                           Z: List[List[List[int]]], nodes: List, components: List, 
                           edges_cgra: List):
    global all_clauses
    # C8,9,10

    for j, comp_type in enumerate(components):
        if comp_type == 1: 
            for k in range(len(X[0][0])):
                nvar = []
                for i in range(len(nodes)):
                    nvar.append(X[i][j][k])
                atmost(2, nvar) 

    for h, edge in enumerate(edges_cgra):
        for k in range(1, len(X[0][0])):
            if edge.w > 0:
                nvar = []
                for i in range(len(nodes)):
                    nvar.append(Y[i][h][k])
                atmost(edge.w, nvar) 

    for j, comp_type in enumerate(components):
        if comp_type == 1:  # PE
            for k in range(1, len(X[0][0])):
                nvar = []
                for i in range(len(nodes)):
                    nvar.append(Z[i][j][k])
                atmost(1, nvar)  

def solve_mapping(nodes: List, components: List, edges_cgra: List, num_cycles: int):
    """Main function to solve CGRA mapping"""
    global all_clauses, var
    all_clauses = []
    var = 0 
    
    start_time = time.time()  # Start timing
    
    X = create_array(len(nodes), len(components), num_cycles)
    Y = create_array(len(nodes), len(edges_cgra), num_cycles)
    Z = create_array(len(nodes), len(components), num_cycles)
    S = create_extra_array(len(nodes), len(components), num_cycles, nodes)
    # print(S)
    # print(len(nodes), len(components), len(edges_cgra), num_cycles, var)
    
    add_initial_conditions(X, nodes, components)
    add_final_conditions(X, nodes, num_cycles)
    add_existence_constraints(X, Y, Z, nodes, components, edges_cgra)
    add_communication_constraints(X, Y, nodes, edges_cgra)
    add_calculation_constraints(X, Y, Z, S, nodes, components, edges_cgra)
    add_capacity_constraints(X, Y, Z, nodes, components, edges_cgra)
    
    # print(all_clauses)
    
    setup_time = time.time() - start_time
    print(f"Setup time: {setup_time:.3f} seconds")
    print(f"Number of variables: {var}")
    print(f"Number of clauses: {len(all_clauses)}")
    
    cnf = CNF()
    for clause in all_clauses:
        cnf.append(clause)
    
    solver = Glucose3()
    solver.append_formula(cnf)
    
    solve_start = time.time()
    sat = solver.solve()
    solve_time = time.time() - solve_start
    print(f"Solving time: {solve_time:.3f} seconds")
    
    if sat:
        model = solver.get_model()
        return interpret_solution(model, X, Y, Z, num_cycles, edges_cgra)

def interpret_solution(model: List[int], X: List[List[List[int]]], Y: List[List[List[int]]], 
                      Z: List[List[List[int]]], num_cycle: int, edges_cgra: List):
    # read model
    result = [[] for _ in range(num_cycle)]
    model_set = set(abs(x) for x in model if x > 0)
    
    for k in range(num_cycle):
        for i in range(len(Y)):
            for h in range(len(Y[0])):
                if Y[i][h][k] in model_set:
                    result[k].append(f"node {i} is communicated in path {h} from component {edges_cgra[h].u} to component {edges_cgra[h].v} at cycle {k}")
        
        for i in range(len(Z)):
            for j in range(len(Z[0])):
                if Z[i][j][k] in model_set:
                    result[k].append(f"node {i} is calculated in component {j} at cycle {k}")
        
        for i in range(len(X)):
            for j in range(len(X[0])):
                if X[i][j][k] in model_set:
                    result[k].append(f"node {i} exists in component {j} at cycle {k}")
    
    return result

def main():
    # Read CGRA architecture
    readCGRA.read("input/e.txt")
    
    # Read DFG
    readDFG.read("input/f.txt")
    
    
    
    # Solve mapping problem - pass nodes list and operands are stored in nodes
    result = solve_mapping(readDFG.nodes, readCGRA.components, readCGRA.edges, num_cycles=9)
    
    if result:
        print("SAT")
        for k in range(len(result)):
            print(f"\nCycle {k}:")
            for line in result[k]:
                print(line)
    else:
        print("UNSAT")

if __name__ == "__main__":
    main()
