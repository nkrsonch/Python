from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import date, datetime


EventDate = date | datetime | str


def configure_stdout() -> None:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')


class Calendar:
    def __init__(self, events: dict[str, EventDate]) -> None:
        self.events = events

    @staticmethod
    def _to_date(value: EventDate) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return datetime.fromisoformat(value).date()

    def get_time_before_actual_events(
        self,
        current_date: date | None = None,
    ) -> dict[str, int]:
        today = current_date or date.today()
        actual_events = {}

        for event_name, event_date in self.events.items():
            days_before_event = (self._to_date(event_date) - today).days
            if days_before_event >= 0:
                actual_events[event_name] = days_before_event

        return actual_events

    def print_time_before_actual_events(self) -> None:
        for event_name, days_before_event in self.get_time_before_actual_events().items():
            print(f'{event_name}: {days_before_event}')


@dataclass(frozen=True)
class MenuItem:
    name: str
    price: float

    def __str__(self) -> str:
        return f'{self.name} - {self.price}\u20bd'


@dataclass
class OrderItem:
    menu_item: MenuItem
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise ValueError('quantity must be positive')

    def get_total(self) -> float:
        return self.menu_item.price * self.quantity


class Order:
    def __init__(self) -> None:
        self.order_items: list[OrderItem] = []

    def add_item(self, menu_item: MenuItem, quantity: int) -> None:
        self.order_items.append(OrderItem(menu_item, quantity))

    def get_total(self) -> float:
        return sum(order_item.get_total() for order_item in self.order_items)

    def summary(self) -> str:
        lines = []

        for order_item in self.order_items:
            lines.append(
                f'{order_item.menu_item.name} x {order_item.quantity} = '
                f'{order_item.get_total()}\u20bd'
            )

        lines.append(f'Итого: {self.get_total()}\u20bd')
        return '\n'.join(lines)


@dataclass
class Node:
    value: str
    neigbs: list[int] = field(default_factory=list)

    @property
    def neighbors(self) -> list[int]:
        return self.neigbs


class Graph:
    def __init__(self, nodes: list[Node]) -> None:
        self.nodes = nodes
        self.adjacency_matrix = self._build_adjacency_matrix()

    def _build_adjacency_matrix(self) -> list[list[int]]:
        nodes_count = len(self.nodes)
        matrix = [[0 for _ in range(nodes_count)] for _ in range(nodes_count)]

        for node_id, node in enumerate(self.nodes):
            matrix[node_id][node_id] = 1

            for neighbor_id in node.neigbs:
                self._validate_node_id(neighbor_id)
                matrix[node_id][neighbor_id] = 1

        return matrix

    def _validate_node_id(self, node_id: int) -> None:
        if node_id < 0 or node_id >= len(self.nodes):
            raise IndexError('node id is out of graph range')

    def _get_node_id(self, node: Node) -> int:
        for node_id, graph_node in enumerate(self.nodes):
            if graph_node is node:
                return node_id

        return self.nodes.index(node)

    def get_node(self, node_id: int) -> Node:
        self._validate_node_id(node_id)
        return self.nodes[node_id]

    def print_adjacency_matrix(self) -> None:
        for row in self.adjacency_matrix:
            print(*row)

    def is_connected(self, first_node: Node, second_node: Node) -> bool:
        first_node_id = self._get_node_id(first_node)
        second_node_id = self._get_node_id(second_node)
        return self.is_connected_by_id(first_node_id, second_node_id)

    def is_connected_by_id(self, first_node_id: int, second_node_id: int) -> bool:
        self._validate_node_id(first_node_id)
        self._validate_node_id(second_node_id)
        return bool(self.adjacency_matrix[first_node_id][second_node_id])


if __name__ == '__main__':
    configure_stdout()

    cappuccino = MenuItem('Капучино', 250.0)
    croissant = MenuItem('Круассан', 150.0)

    order = Order()
    order.add_item(cappuccino, 2)
    order.add_item(croissant, 1)

    print(order.summary())
    print('Итого к оплате:', order.get_total())

    nodes = [
        Node(value='123', neigbs=[1, 2]),
        Node(value='13', neigbs=[0]),
        Node(value='321', neigbs=[0]),
    ]
    graph = Graph(nodes)
    graph.print_adjacency_matrix()
