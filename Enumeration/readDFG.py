from itertools import permutations
from itertools import combinations

nodes = []
ninputs = 0  # number of input nodes
ndata = 0    # total number of nodes (including inputs)
datanames = []  # names of data nodes
outputnames = []  # names of output nodes
name2oprs = {}
name2node = {}
operand2node = {}

class Operator:
    def __init__(self, symbol: str, num_operands: int, commutative: bool, associative: bool):
        self.symbol = symbol
        self.num_operands = num_operands
        self.commutative = commutative
        self.associative = associative

class Node:
    def __init__(self, type=-1, id=-1, Operator=None, child=[], operands=[]):
        self.type = type  # operator type or -1 for input
        self.id = id      # node id (input id for inputs, node index for operators)
        self.is_output = False
        self.Operator = Operator
        self.child = child
        self.operands = operands
         
def create_input(name: str):
    """Create input node"""
    global ninputs, ndata, nodes, name2node
    datanames.append(name)
    p = Node(type=-1, id=ninputs)  # Input nodes get sequential input IDs
    ninputs += 1
    ndata += 1
    nodes.append(p)
    name2node[name] = p
    return p

def reduce_node(node: Node):
    global ndata
    for child in node.child:
        if child.type == 1:
            if child.Operator == node.Operator:
                # Extend the operands list with operand's operands
                node.child.extend(child.child)
                # Remove the original operand since we've flattened its operands
                node.child.remove(child)
    for child in node.child:
        if child.type == 1:           
            reduce_node(child)
    # operand2node[tuple(node.child)] = node

def id_node(node: Node):
    global ndata
    for operand in node.operands:
        if operand.type == 1:
            id_node(operand)
    ndata += 1
    node.id = ndata-1
    nodes.append(node)

def create_node(parts: list, name2oprs: dict):
    global ndata, name2node
    q = []
    
    for i in range(len(parts)-1, 0, -1):
        if parts[i] in name2node:  # It's an operand
            q.append(name2node[parts[i]])  # Append node object instead of just ID
        else:  # It's an operator
            b = q.pop()  # Get right operand
            a = q.pop()  # Get left operand
            
            # Create new node with operator type
            operator = name2oprs.get(parts[i])
            if operator is None:
                raise ValueError(f"Operator {parts[i]} not found")
            
            # Create node with operator and operands
            # ndata += 1
            new_node = Node(type=1, Operator=operator, child=[a, b])  # Store Node objects
            q.append(new_node)
    
    if q:  # Store result for output node
        result_node = q[0]
        name2node[parts[0]] = result_node
        # reduce_node(result_node) 
        # id_node(result_node)

def gen_operands():
    global nodes, name2node, operand2node, ndata
    for i in outputnames:
        node = name2node[i]
        reduce_node(node)
    for i in outputnames:
        node = name2node[i]
        gen_node_operands(node)

def gen_node_operands(node: Node):
    global nodes, name2node, operand2node, ndata
    if node.type == -1:
        return
    
    for i in node.child:
        gen_node_operands(i)
    
    node.operands = []

    base_operands = node.child.copy()
    # node.operands.append(node.child.copy())
    n = len(base_operands)
    # Generate all possible subarrays (both contiguous and non-contiguous)
    for length in range(2, n):
        for indices in combinations(range(n), length):
            subarray = [base_operands[i] for i in indices]
            if operand2node.get(tuple(subarray)) is None:
                ndata += 1
                new_node = Node(type=1, id=ndata-1, Operator=node.Operator, child=subarray)
                nodes.append(new_node)
                operand2node[tuple(subarray)] = new_node
    ndata += 1
    node.id = ndata-1
    nodes.append(node)
    operand2node[tuple(base_operands)] = node
    
    for length in range(2, n+1):
        for indices in combinations(range(n), length):
            subarray = [base_operands[i] for i in indices]
            moperand = {}
            all_operands = []
            # for i in subarray:
            #     print(i.id, end=" ")
            # print("subarray")
            current_node = operand2node[tuple(subarray)]
            # print(current_node.id)
            # if current_node.id == 21:
            #     for i in subarray:
            #         print(i.id, end=" ")
            #     print("subarray")
            for bitmask in range(1,(1 << len(subarray)) -1):
                a = []
                b = []
                for i in range(len(subarray)):
                    if bitmask & (1 << i):
                        a.append(subarray[i])
                    else:
                        b.append(subarray[i])
                if len(a) == 1:
                    nodea = a[0]
                else:   
                    nodea = operand2node[tuple(a)]
                if len(b) == 1:
                    nodeb = b[0]
                else:
                    nodeb = operand2node[tuple(b)]
                
                # unique operands
                key_operands = []
                key_operands.extend([nodea, nodeb].copy())
                sorted_operands = sorted(key_operands, key=lambda x: x.id)
                
                if(moperand.get(tuple(sorted_operands)) == None):
                    moperand[tuple(sorted_operands)] = 1
                    all_operands.append(sorted_operands.copy())
                    # if(current_node.id == 78):
                    #     print_operands(current_node)
            
                # if(current_node.id == 79):
                #     for i in sorted_operands:
                #         print(i.id, end=" ")
                #     print("sorted_operands")
                    
                #     print(bitmask,current_node.id,"id")
                #     for i in subarray:
                #         print(i.id, end=" ")
                #     print("subarray")
                #     for i in a:
                #         print(i.id, end=" ")
                #     print("a")
                #     for i in b:
                #         print(i.id, end=" ")
                #     print("b")
            current_node.operands = all_operands.copy()
                # print(current_node.id)
                # print(nodea.id, nodeb.id)



def mac():
    global nodes, name2node, operand2node, ndata
    for node in nodes:
        if node.type == 1:
            add_operands = []
            for operand in node.operands:
                for member in operand:
                    if member.type == -1:
                        continue
                    all_inputs = True
                    for child in member.child:
                        if child.type != -1:  
                            all_inputs = False
                            break
                    if all_inputs:
                        tmp = operand.copy()
                        tmp.remove(member)
                        tmp.extend(member.child)
                        add_operands.append(tmp)     
            node.operands.extend(add_operands)

def print_operands(node: Node):
    # for i in node.child:
        # print(i.id, end=" ")
    # print()
    for i in node.operands:
        for j in i:
            print(j.id, end=" ")
        print()

def print_tree(node: Node, height: int):
    """Print tree with proper indentation"""
    indent = "\t" * height
    print(f"{indent}{node.id}", end="")
    
    if node.type == -1:  # Input node
        print(f" {datanames[node.id]}")
    else:  # Operator node
        print(f" {node.Operator.symbol}")
        for child in node.child:
            print_tree(child, height + 1)

def read(filename="f.txt"):
    """Read DFG from file"""
    global node, ninputs, ndata, datanames, outputnames, name2oprs, name2node
    
    # Reset all global variables
    node = []
    ninputs = 0
    ndata = 0
    datanames = []
    outputnames = []
    name2oprs = {}
    name2node = {}
    op_count = 0  # Counter for operator types
    
    try:
        with open(filename, 'r') as f:
            lines = [line.strip() for line in f.readlines()]
            
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
                
            parts = line.split()
            if not parts:
                i += 1
                continue
                
            if parts[0] == '.i':
                # Process input declarations
                for name in parts[1:]:
                    create_input(name)
                    
            elif parts[0] == '.o':
                # Process output declarations
                outputnames.extend(parts[1:])
                    
            elif parts[0] == '.f':
                # Process operator declarations
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    if not line or line.startswith('.'):
                        break
                        
                    parts = line.split()
                    if len(parts) < 2:
                        raise ValueError(f"Invalid operator declaration: {line}")
                        
                    symbol = parts[0]
                    try:
                        num_operands = int(parts[1])
                    except:
                        raise ValueError(f"Non-integer operands: {parts[1]}")
                        
                    if num_operands <= 0:
                        raise ValueError(f"Negative operands: {parts[1]}")
                        
                    commutative = 'c' in parts[2:]
                    associative = 'a' in parts[2:]
                    
                    # Create Operator object and store in dictionary
                    # print(symbol, num_operands, commutative, associative)
                    name2oprs[symbol] = Operator(symbol, num_operands, commutative, associative)
                    i += 1
                continue
                
            elif parts[0] == '.n':
                # Process node declarations
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    if not line or line.startswith('.'):
                        break
                        
                    parts = line.split()
                    if len(parts) < 2:
                        raise ValueError(f"Invalid node declaration: {line}")
                        
                    # Get node name
                    node_name = parts[0]
                    if node_name in name2node:
                        raise ValueError(f"Duplicated data: {node_name}")
                    
                    # Create node first
                    create_node(parts, name2oprs)
                    
                    # Now we can safely mark it as output since it exists in name2node
                    
                    if node_name in outputnames:
                        name2node[node_name].is_output = True
                    
                    i += 1
                continue
                
            elif parts[0] == '.p':
                # Process priority declarations
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    if not line or line.startswith('.'):
                        break
                        
                    parts = line.split()
                    if len(parts) < 3:
                        i += 1
                        continue
                    
                    # Process each priority relationship
                    p = name2node[parts[0]]
                    if not p:
                        raise ValueError(f"Unspecified data: {parts[0]}")
                    
                    for j in range(1, len(parts), 2):
                        if j+1 >= len(parts):
                            break
                            
                        q = name2node[parts[j+1]]
                        if not q:
                            raise ValueError(f"Unspecified data: {parts[j+1]}")
                        
                        # Update p for next iteration
                        p = q
                    
                    i += 1
                continue
                
            i += 1
        gen_operands()
        mac()
        return name2node
        
    except FileNotFoundError:
        print(f"Error: Cannot open file {filename}")
        return None, None

def main():
    name2node = read("MAC/f.txt")

    if name2node:
        print(ndata)
        print("\nNodes (Tree format):")
        for i in range(ndata):
            print(i,nodes[i].type, ":")
            print_operands(nodes[i])
        
        for i in outputnames:
            print_tree(name2node[i],0)

if __name__ == "__main__":
    main()

