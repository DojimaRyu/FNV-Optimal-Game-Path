from __future__ import annotations

from typing import Any, Union

import networkx as nx

class _Vertex:
    item: Any
    kind: str
    neighbours: set['_Vertex']
    effective_ranges: list[str]  # Change to list of strings
    skill: str

    def __init__(self, item: Any, kind: str, skill: str, effective_ranges: list[str] = None) -> None:
        self.item = item
        self.kind = kind
        self.neighbours = set()
        self.effective_ranges = effective_ranges if effective_ranges is not None else []
        self.skill = skill

    def degree(self) -> int:
        return len(self.neighbours)

class Graph:
    vertices: dict[Any, _Vertex]

    def __init__(self) -> None:
        self.vertices = {}

    def add_vertex(self, item: Any, kind: str, ranges: list[str], skill: str) -> None:
        if item not in self.vertices:
            self.vertices[item] = _Vertex(item, kind, skill, ranges)

    def add_edge(self, item1: Any, item2: Any) -> None:
        if item1 in self.vertices and item2 in self.vertices:
            v1 = self.vertices[item1]
            v2 = self.vertices[item2]

            v1.neighbours.add(v2)
            v2.neighbours.add(v1)
        else:
            raise ValueError

    def to_networkx(self, maxvertices: int = 5000) -> nx.Graph:
        graph_nx = nx.Graph()
        for v in self.vertices.values():
            graph_nx.add_node(v.item, kind=v.kind, effective_ranges=v.effective_ranges, skill=v.skill)

            for u in v.neighbours:
                if graph_nx.number_of_nodes() < maxvertices:
                    graph_nx.add_node(u.item, kind=u.kind, effective_ranges=u.effective_ranges, skill = v.skill)

                if u.item in graph_nx.nodes:
                    graph_nx.add_edge(v.item, u.item)

            if graph_nx.number_of_nodes() >= maxvertices:
                break

        return graph_nx
