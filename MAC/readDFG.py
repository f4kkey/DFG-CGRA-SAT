nodes = []
ninputs = 0  # number of input nodes
ndata = 0    # total number of nodes (including inputs)
datanames = []  # names of data nodes
outputnames = []  # names of output nodes
name2oprs = {}
name2node = {}

class Operator:
    def __init__(self, symbol: str, num_operands: int, commutative: bool, associative: bool):
        self.symbol = symbol
        self.num_operands = num_operands
        self.commutative = commutative
        self.associative = associative
        self.next_operator = []
        

class Node:
    def __init__(self, type, id, operator, child, operands):
        self.type = type  # operator type or -1 for input
        self.id = id   
        self.is_output = False
        self.operator = operator
        self.child = child
        self.operands = operands
         
def create_input(name: str):
    """Create input node"""
    global ninputs, ndata, nodes, name2node
    datanames.append(name)
    p = Node(type=-1, id=ninputs,operator=None,child=[],operands=[]) 
    ninputs += 1
    ndata += 1
    nodes.append(p)
    name2node[name] = p
    return p

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
            ndata += 1
            new_node = Node(type=1, id=ndata-1, operator=operator, child=[a, b],operands=[]) 
            q.append(new_node)
            nodes.append(new_node)
    
    if q:  # Store result for output node
        result_node = q[0]
        name2node[parts[0]] = result_node

def gen_operands():
    global nodes, name2node
    
    for i in outputnames:
        node = name2node[i]
        gen_node_operands(node)

def gen_node_operands(node: Node):
    if node.type == -1:  # Input node
        return
        
    # First clear any existing operands
    node.operands = []
    
    # Add current children as first operand set
    tmp = node.child.copy()
    node.operands.append(tmp)
    
    for child in node.child:
        if(child.type == -1):
            continue
        gen_node_operands(child)
        
def mac():
    global nodes, name2node, operand2node, ndata
    for node in nodes:
        if node.type == 1:
            for child in node.child:
                if(child.type == -1):
                    continue
                # print(child.operator.symbol, node.operator.symbol, "arr")
                # for oprs in node.operator.next_operator:
                #     print (oprs.symbol)
                if child.operator in node.operator.next_operator:
                    # print(node.id, node.operator.symbol, child.id, child.operator.symbol)
                    # for operator in node.operator.next_operator:
                    #     print(operator.symbol)
                    tmp = node.child.copy()
                    tmp.remove(child)
                    tmp.extend(child.child)
                    node.operands.append(tmp)

def print_operands(node: Node):
    # for i in node.child:
        # print(i.id, end=" ")
    # print()
    for i in node.operands:
        for j in i:
            print('\t',j.id, end=" ")
        print()

def print_tree(node: Node, height: int):
    """Print tree with proper indentation"""
    indent = "\t" * height
    print(f"{indent}{node.id}", end="")
    
    if node.type == -1:  # Input node
        print(f" {datanames[node.id]}")
    else:  # Operator node
        print(f" {node.operator.symbol}")
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
            elif parts[0] == '.m':
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    if not line or line.startswith('.'):
                        break
                    parts = line.split()
                    st = []
                    for j in range(len(parts)-1, -1, -1):
                        if(name2oprs.get(parts[j]) != None):
                            oprs = name2oprs.get(parts[j])
                            # print(oprs.symbol)
                            for k in range(oprs.num_operands):
                                if st[len(st)-1] != None:
                                    oprs2 = st.pop()
                                    oprs.next_operator.append(oprs2)                                        
                                else:
                                    st.pop()
                            st.append(oprs)
                        else:
                            st.append(None)
                        # oprs1 = name2oprs.get('*')
                        # print(j,'\t',oprs1.symbol)
                        # for oprs2 in oprs1.next_operator:
                        #     print('\t',oprs2.symbol)
                    # print(parts)
                    i+=1
                continue
            i += 1
        
        gen_operands()
        mac()
        return name2node
        
    except FileNotFoundError:
        print(f"Error: Cannot open file {filename}")
        return None, None

def main():
    name2node = read("input/f.txt")

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

