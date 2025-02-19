components = []  # array to store component types
ncomponents = 0

class Edge:
    def __init__(self, u, v, w):
        self.u = u  # source component id
        self.v = v  # destination component id
        self.w = w  # weight (bandwidth)

def read(filename="e.txt"):
    global ncomponents
    edges = []
    name2id = {}  # map names to component indices
    
    # Add implicit ExtMem with type 3
    components.append(3)  # Use append instead of direct assignment
    name2id["_extmem"] = 0
    ncomponents = 1
    
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
            if not parts or not parts[0].startswith('.'):
                i += 1
                continue
                
            section_type = parts[0][1:]  # Remove '.'
            
            if section_type == 'pe':
                # Process PE components (type 1)
                for name in parts[1:]:
                    components.append(1)  # Use append
                    name2id[name] = ncomponents
                    ncomponents += 1
                    
            elif section_type == 'mem':
                # Process MEM components (type 2)
                for name in parts[1:]:
                    components.append(2)  # Use append
                    name2id[name] = ncomponents
                    ncomponents += 1
                    
            elif section_type == 'com':
                # Process communication paths
                i += 1
                while i < len(lines):
                    line = lines[i].strip()
                    if not line or line.startswith('.'):
                        break
                        
                    parts = line.split()
                    arrow_idx = parts.index('->')
                    
                    senders = parts[:arrow_idx]
                    remaining = parts[arrow_idx + 1:]
                    weight = 0  # default weight if not specified
                    
                    if ':' in remaining:
                        colon_idx = remaining.index(':')
                        recipients = remaining[:colon_idx]
                        weight = int(remaining[colon_idx + 1])
                    else:
                        recipients = remaining
                    
                    # Add edges for all sender-recipient pairs
                    for sender in senders:
                        if sender not in name2id:
                            raise ValueError(f"Unknown sender component: {sender}")
                        sender_id = name2id[sender]
                        
                        for recipient in recipients:
                            if recipient not in name2id:
                                raise ValueError(f"Unknown recipient component: {recipient}")
                            recipient_id = name2id[recipient]
                            
                            edge = Edge(sender_id, recipient_id, weight)
                            edges.append(edge)
                    
                    i += 1
                    
            i += 1
            
        return components, edges
        
    except FileNotFoundError:
        print(f"Error: Cannot open file {filename}")
        return None, None
    except Exception as e:
        print(f"Error parsing file: {e}")
        return None, None

def main():
    components, edges = read("sat-base/e.txt")
    if components and edges:
        print("Components:")
        for i, comp_type in enumerate(components):
            type_name = {1: "PE", 2: "MEM", 3: "EXTMEM"}[comp_type]
            print(f"id={i}, type={type_name}")
            
        print("\nEdges (source -> dest : weight):")
        for edge in edges:
            print(f"{edge.u} -> {edge.v} : {edge.w}")

if __name__ == "__main__":
    main()




