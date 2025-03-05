node = []
ninputs = 0  # number of input nodes
ndata = 0    # total number of nodes (including inputs)
datanames = []  # names of data nodes
outputnames = []  # names of output nodes
name2oprs = {}

class Operator:
    def __init__(self, symbol: str, num_operands: int, commutative: bool, associative: bool):
        self.symbol = symbol
        self.num_operands = num_operands
        self.commutative = commutative
        self.associative = associative

class Node:
    def __init__(self, type=-1, id=-1, Operator=None, operands=[]):
        self.type = type  # operator type or -1 for input
        self.id = id      # node id (input id for inputs, node index for operators)
        self.is_output = False
        self.Operator = Operator
        self.operands = operands
         
def create_input(name: str, name2node: dict):
    """Create input node"""
    global ninputs, ndata, node
    datanames.append(name)
    p = Node(type=-1, id=ninputs)  # Input nodes get sequential input IDs
    ninputs += 1
    ndata += 1
    name2node[name] = p
    node.append(p)
    return p

def create_node(parts: list, name2oprs: dict, name2node: dict):
    """Create nodes from Polish notation"""
    global ndata
    q = []
    
    for i in range(len(parts)-1, 0, -1):
        if parts[i] in name2node:  # It's an operand
            q.append(name2node[parts[i]])  # Append node object instead of just ID
        else:  # It's an operator
            try:
                b = q.pop()  # Get right operand
                a = q.pop()  # Get left operand
                
                # Create new node with operator type
                ndata += 1
                operator = name2oprs.get(parts[i])
                if operator is None:
                    raise ValueError(f"Operator {parts[i]} not found")
                
                # Create node with operator and operands
                new_node = Node(type=1, id=ndata-1, Operator=operator, operands=[a.id, b.id])
                node.append(new_node)
                q.append(new_node)
                
            except IndexError:
                raise ValueError(f"Not enough operands for operator {parts[i]}")
    
    if q:  # Store result for output node
        name2node[parts[0]] = q[0]

def print_node_info(name: str, n: Node, name2oprs: dict):
    """Print detailed node information"""
    if n.type >= 0:
        print(f"{name}: id={n.id}, type={n.Operator.symbol}, operands={n.operands}, output={n.is_output}")
    else:
        print(f"{name}: input node (id={n.id})")

def print_tree(node_id: int, height: int):
    """Print tree with proper indentation"""
    n = node[node_id]
    indent = "\t" * height
    print(f"{indent}{node_id}", end="")
    
    if n.type == -1:  # Input node
        print(f" {datanames[n.id]}")
    else:  # Operator node
        print(f" {n.Operator.symbol}")
        for operand_id in n.operands:
            print_tree(operand_id, height + 1)

def read(filename="f.txt"):
    """Read DFG from file"""
    global node, ninputs, ndata, datanames, outputnames, oprs
    
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
                    create_input(name, name2node)
                    
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
                    create_node(parts, name2oprs, name2node)
                    
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
            
        return name2node
        
    except FileNotFoundError:
        print(f"Error: Cannot open file {filename}")
        return None, None

def main():
    name2node = read("input/f.txt")
    if name2node:
            
        print("\nNodes (Detailed format):")
        for name, n in name2node.items():
            print_node_info(name, n, name2oprs)
        
        for i in outputnames:
            print_tree(name2node[i].id,0)

if __name__ == "__main__":
    main()

