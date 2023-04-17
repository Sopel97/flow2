from pathlib import Path

import networkx as nx

from src.core.connectGraph import produceConnectedGraphFromDisjoint
from src.core.flow1Compat import constructDisjointGraphFromFlow1Yaml
from src.core.graphToEquations import constructPuLPFromGraph
from src.data.basicTypes import IngredientNode, MachineNode


if __name__ == '__main__':
    # flow_projects_path = Path('~/Dropbox/OrderedSetCode/game-optimization/minecraft/flow/projects').expanduser()
    # yaml_path = flow_projects_path / 'power/oil/light_fuel_hydrogen_loop.yaml'
    yaml_path = Path('temporaryFlowProjects/testProjects/loopGraph.yaml')

    G = constructDisjointGraphFromFlow1Yaml(yaml_path)
    G = produceConnectedGraphFromDisjoint(G)
    for idx, node in G.nodes.items():
        print(idx, node)
    
    # Construct PuLP representation of graph
    problem, edge_to_variable = constructPuLPFromGraph(G)
    # There isn't a chosen quantity yet, so add one
    problem += edge_to_variable[(1, 7)] == 1000
    print(problem)

    status = problem.solve()
    print(status)

    if status == 1:
        for variable in edge_to_variable.values():
            print(variable, variable.value())

    # Add label for ease of reading
    for idx, node in G.nodes.items():
        nobj = node['object']
        if isinstance(nobj, MachineNode):
            node['label'] = nobj.machine
        elif isinstance(nobj, IngredientNode):
            node['label'] = nobj.name
        node['label'] = f"({idx}) {node['label']}"
        node['shape'] = 'box'
    
    for idx, edge in G.edges.items():
        edge['label'] = str(edge_to_variable[idx[:2]])

    ag = nx.nx_agraph.to_agraph(G)
    ag.draw('proto.pdf', prog='dot')