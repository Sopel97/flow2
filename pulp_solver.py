from pathlib import Path

import networkx as nx
from pulp import PULP_CBC_CMD

from src.core.addUserLocking import addPulpUserChosenQuantityFromFlow1Yaml
from src.core.connectGraph import produceConnectedGraphFromDisjoint
from src.core.flow1Compat import constructDisjointGraphFromFlow1Yaml
from src.core.graphToEquations import constructPuLPFromGraph
from src.core.postProcessing import pruneZeroEdges
from src.core.preProcessing import addExternalNodes, removeIgnorableIngredients
from src.data.basicTypes import ExternalNode, IngredientNode, MachineNode


if __name__ == '__main__':
    # flow_projects_path = Path('~/Dropbox/OrderedSetCode/game-optimization/minecraft/flow/projects').expanduser()
    # yaml_path = flow_projects_path / 'power/oil/light_fuel_hydrogen_loop.yaml'
    yaml_path = Path('temporaryFlowProjects/230_platline.yaml')

    G = constructDisjointGraphFromFlow1Yaml(yaml_path)
    G = produceConnectedGraphFromDisjoint(G)
    G = removeIgnorableIngredients(G) # eg water

    excluded_sources = set()

    excluded_sources.add('reprecipitated platinum dust')
    excluded_sources.add('ammonium chloride')
    excluded_sources.add('sludge dust residue dust')
    excluded_sources.add('acidic osmium solution')
    excluded_sources.add('leach residue dust')
    excluded_sources.add('platinum concentrate')
    excluded_sources.add('potassium disulfate dust')
    excluded_sources.add('PMP')
    excluded_sources.add('nitrogen dioxide')
    excluded_sources.add('platinum salt dust')
    excluded_sources.add('palladium enriched ammonia')
    excluded_sources.add('platinum dust')
    excluded_sources.add('sodium ruthenate dust')
    excluded_sources.add('calcium chloride dust')
    excluded_sources.add('refined platinum salt dust')
    excluded_sources.add('diluted sulfuric acid')
    excluded_sources.add('chlorine')
    excluded_sources.add('iridium chloride dust')
    excluded_sources.add('platinum residue dust')
    excluded_sources.add('rhodium sulfate')
    excluded_sources.add('molten potassium disulfate')
    excluded_sources.add('acidic iridium solution')
    excluded_sources.add('iridium dioxide dust')
    excluded_sources.add('iridium metal residue dust')
    excluded_sources.add('rarest metal residue dust')

    excluded_sinks = set()
    '''
    excluded_sinks.add('platinum residue dust')
    excluded_sinks.add('potassium disulfate dust')
    excluded_sinks.add('salt water')
    excluded_sinks.add('platinum concentrate')
    excluded_sinks.add('PMP')
    excluded_sinks.add('reprecipitated platinum dust')
    excluded_sinks.add('molten potassium disulfate')
    excluded_sinks.add('sulfur dust')
    excluded_sinks.add('potassium dust')
    excluded_sinks.add('rarest metal residue dust')
    excluded_sinks.add('ammonia')
    excluded_sinks.add('leach residue dust')
    excluded_sinks.add('iridium metal residue dust')
    excluded_sinks.add('iridium dioxide dust')
    excluded_sinks.add('refined platinum salt dust')
    excluded_sinks.add('platinum salt dust')
    excluded_sinks.add('saltpeter')
    excluded_sinks.add('hydrochloric acid')
    excluded_sinks.add('aqua regia')
    excluded_sinks.add('oxygen')
    excluded_sinks.add('acidic iridium solution')
    excluded_sinks.add('ammonium chloride')
    excluded_sinks.add('calcium dust')
    '''

    G = addExternalNodes(G, excluded_sources, excluded_sinks)
    for idx, node in G.nodes.items():
        print(idx, node)
    
    # Construct PuLP representation of graph
    system_of_equations, edge_to_variable = constructPuLPFromGraph(G)
    # for edge, variable in edge_to_variable.items():
    #     # Warm start all non-ExternalNode edges to 1
    #     if not isinstance(G.nodes[edge[0]]['object'], ExternalNode) and not isinstance(G.nodes[edge[1]]['object'], ExternalNode):
    #         variable.setInitialValue(1)

    # There isn't a chosen quantity yet, so add one
    # The YAML file has one since this is Flow1 compatible, so get it from there
    system_of_equations = addPulpUserChosenQuantityFromFlow1Yaml(G, edge_to_variable, system_of_equations, yaml_path)
    
    print(system_of_equations)

    seed = 1337 # Choose a seed for reproduceability
    status = system_of_equations.solve(PULP_CBC_CMD(msg=True, warmStart=True, options = [f'RandomS {seed}']))
    print(status)

    G = pruneZeroEdges(G, edge_to_variable)

    def find_coeff(vvar):
        return system_of_equations.objective[vvar]

    if status == 1:
        for variable in edge_to_variable.values():
            print(variable, variable.value(), find_coeff(variable))

    # Add label for ease of reading
    for idx, node in G.nodes.items():
        nobj = node['object']
        if isinstance(nobj, ExternalNode):
            node['label'] = nobj.machine
            node['color'] = 'purple'
        elif isinstance(nobj, MachineNode):
            node['label'] = nobj.machine
            if nobj.machine.startswith('[Source]') or nobj.machine.startswith('[Sink]'):
                node['color'] = 'purple'
            else:
                node['color'] = 'green'
        elif isinstance(nobj, IngredientNode):
            node['label'] = nobj.name
            node['color'] = 'red'
        node['shape'] = 'box'
        node['label'] = f"({idx}) {node['label']}"
        node['fontname'] = 'arial'
    
    for idx, edge in G.edges.items():
        index_idx = idx[:2]
        label_parts = [str(edge_to_variable[index_idx])]
        if status == 1:
            label_parts.append(f'{edge_to_variable[index_idx].value():.2f}')
        edge['label'] = '\n'.join(label_parts)
        edge['fontname'] = 'arial'

    ag = nx.nx_agraph.to_agraph(G)
    ag.draw('proto.png', prog='dot')