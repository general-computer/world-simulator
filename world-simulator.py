import random
from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from enum import Enum
import math

class BiomeType(Enum):
    FOREST = "forest"
    PLAINS = "plains"
    MOUNTAIN = "mountain"
    DESERT = "desert"

class ResourceType(Enum):
    FOOD = "food"
    WOOD = "wood"
    STONE = "stone"
    WATER = "water"

class ActivityType(Enum):
    GATHERING = "gathering"
    RESTING = "resting"
    SOCIALIZING = "socializing"
    BUILDING = "building"

@dataclass
class Position:
    x: int
    y: int
    
    def distance_to(self, other: 'Position') -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

@dataclass
class Personality:
    sociability: float  # 0-1, how much they seek social interaction
    industriousness: float  # 0-1, how much they prefer working
    curiosity: float  # 0-1, how likely to explore
    
    @classmethod
    def random(cls) -> 'Personality':
        return cls(
            sociability=random.random(),
            industriousness=random.random(),
            curiosity=random.random()
        )

class Entity:
    def __init__(self, name: str, position: Position):
        self.name = name
        self.position = position
        self.personality = Personality.random()
        self.energy = 100.0
        self.hunger = 0.0
        self.social_need = 0.0
        self.inventory: Dict[ResourceType, float] = {r: 0.0 for r in ResourceType}
        self.relationships: Dict[str, float] = {}  # name -> relationship value
        self.current_activity: Optional[ActivityType] = None

    def update(self, world: 'World') -> None:
        # Basic needs decay
        self.energy -= 1.0
        self.hunger += 0.5
        self.social_need += self.personality.sociability * 0.5

        # Choose and perform activity based on needs
        self._choose_activity(world)
        self._perform_activity(world)

    def _choose_activity(self, world: 'World') -> None:
        if self.energy < 30:
            self.current_activity = ActivityType.RESTING
        elif self.hunger > 70:
            self.current_activity = ActivityType.GATHERING
        elif self.social_need > 80:
            self.current_activity = ActivityType.SOCIALIZING
        else:
            # Default to gathering or building based on personality
            self.current_activity = (
                ActivityType.BUILDING 
                if random.random() < self.personality.industriousness 
                else ActivityType.GATHERING
            )

    def _perform_activity(self, world: 'World') -> None:
        if self.current_activity == ActivityType.RESTING:
            self.energy = min(100, self.energy + 10)
        
        elif self.current_activity == ActivityType.GATHERING:
            tile = world.get_tile(self.position)
            for resource, amount in tile.gather_resources().items():
                self.inventory[resource] = self.inventory.get(resource, 0) + amount
                if resource == ResourceType.FOOD:
                    self.hunger = max(0, self.hunger - amount * 10)
        
        elif self.current_activity == ActivityType.SOCIALIZING:
            nearby_entities = world.get_nearby_entities(self, radius=3)
            for other in nearby_entities:
                compatibility = self._calculate_compatibility(other)
                relationship_change = compatibility * 0.1
                self.relationships[other.name] = self.relationships.get(other.name, 0) + relationship_change
                self.social_need = max(0, self.social_need - 10)

    def _calculate_compatibility(self, other: 'Entity') -> float:
        # Simple personality compatibility calculation
        personality_diff = abs(self.personality.sociability - other.personality.sociability)
        return 1.0 - personality_diff

class Tile:
    def __init__(self, biome: BiomeType):
        self.biome = biome
        self.resources: Dict[ResourceType, float] = self._initialize_resources()

    def _initialize_resources(self) -> Dict[ResourceType, float]:
        resources = {r: 0.0 for r in ResourceType}
        
        if self.biome == BiomeType.FOREST:
            resources[ResourceType.WOOD] = 100.0
            resources[ResourceType.FOOD] = 50.0
            resources[ResourceType.WATER] = 30.0
        elif self.biome == BiomeType.PLAINS:
            resources[ResourceType.FOOD] = 80.0
            resources[ResourceType.WATER] = 20.0
        elif self.biome == BiomeType.MOUNTAIN:
            resources[ResourceType.STONE] = 100.0
            resources[ResourceType.WATER] = 10.0
        elif self.biome == BiomeType.DESERT:
            resources[ResourceType.STONE] = 30.0
            
        return resources

    def gather_resources(self) -> Dict[ResourceType, float]:
        gathered = {}
        for resource_type, amount in self.resources.items():
            if amount > 0:
                gathered_amount = min(random.random() * 10, amount)
                self.resources[resource_type] -= gathered_amount
                gathered[resource_type] = gathered_amount
        return gathered

    def regenerate_resources(self) -> None:
        base_resources = self._initialize_resources()
        for resource_type, max_amount in base_resources.items():
            current = self.resources[resource_type]
            if current < max_amount:
                regen_amount = random.random() * 5
                self.resources[resource_type] = min(max_amount, current + regen_amount)

class World:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.entities: List[Entity] = []
        self.grid: List[List[Tile]] = self._generate_world()
        self.time = 0

    def _generate_world(self) -> List[List[Tile]]:
        return [[self._generate_tile() for _ in range(self.width)] for _ in range(self.height)]

    def _generate_tile(self) -> Tile:
        biome = random.choice(list(BiomeType))
        return Tile(biome)

    def add_entity(self, entity: Entity) -> None:
        self.entities.append(entity)

    def get_tile(self, position: Position) -> Tile:
        x = max(0, min(position.x, self.width - 1))
        y = max(0, min(position.y, self.height - 1))
        return self.grid[y][x]

    def get_nearby_entities(self, entity: Entity, radius: float) -> List[Entity]:
        return [
            other for other in self.entities
            if other != entity and entity.position.distance_to(other.position) <= radius
        ]

    def update(self) -> None:
        self.time += 1
        
        # Update all entities
        for entity in self.entities:
            entity.update(self)
        
        # Regenerate resources periodically
        if self.time % 10 == 0:
            for row in self.grid:
                for tile in row:
                    tile.regenerate_resources()

    def print_status(self) -> None:
        print(f"\nWorld Status - Time: {self.time}")
        for entity in self.entities:
            print(f"\n{entity.name}:")
            print(f"  Position: ({entity.position.x}, {entity.position.y})")
            print(f"  Activity: {entity.current_activity.value if entity.current_activity else 'none'}")
            print(f"  Energy: {entity.energy:.1f}")
            print(f"  Hunger: {entity.hunger:.1f}")
            print(f"  Social: {entity.social_need:.1f}")
            print("  Inventory:", {k.value: f"{v:.1f}" for k, v in entity.inventory.items() if v > 0})
            print("  Relationships:", {k: f"{v:.2f}" for k, v in entity.relationships.items()})

def main():
    # Create a small world
    world = World(10, 10)
    
    # Add some entities
    entities = [
        Entity("Alice", Position(random.randint(0, 9), random.randint(0, 9))),
        Entity("Bob", Position(random.randint(0, 9), random.randint(0, 9))),
        Entity("Charlie", Position(random.randint(0, 9), random.randint(0, 9)))
    ]
    
    for entity in entities:
        world.add_entity(entity)
    
    # Run simulation for 50 time steps
    for _ in range(50):
        world.update()
        if _ % 5 == 0:  # Print status every 5 steps
            world.print_status()

if __name__ == "__main__":
    main()
