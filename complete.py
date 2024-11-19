import random
from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from enum import Enum
import math
from datetime import datetime, timedelta
import time
from colorama import init, Fore, Back, Style

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
    SEEKING_SHELTER = "seeking_shelter"

class Season(Enum):
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"

class WeatherType(Enum):
    CLEAR = "clear"
    CLOUDY = "cloudy"
    RAIN = "rain"
    STORM = "storm"
    SNOW = "snow"
    HEATWAVE = "heatwave"

@dataclass
class WeatherState:
    type: WeatherType
    temperature: float  # in Celsius
    humidity: float    # 0-1
    wind_speed: float  # in m/s
    precipitation: float  # 0-1
    duration: int      # how many ticks this weather will last
    
    @property
    def is_dangerous(self) -> bool:
        return (
            self.type in {WeatherType.STORM, WeatherType.HEATWAVE} or
            self.temperature < -10 or
            self.temperature > 40 or
            self.wind_speed > 20
        )

class Climate:
    def __init__(self, base_temperature: float = 15.0):
        self.base_temperature = base_temperature
        self.current_season = Season.SPRING
        self.day_of_year = 0
        self.current_weather = self._generate_weather()
        self.weather_duration = 0
        
    def _get_season_modifiers(self) -> Dict[str, float]:
        modifiers = {
            Season.SPRING: {
                "temperature": 5.0,
                "humidity": 0.6,
                "storm_chance": 0.1
            },
            Season.SUMMER: {
                "temperature": 15.0,
                "humidity": 0.4,
                "storm_chance": 0.15
            },
            Season.AUTUMN: {
                "temperature": 5.0,
                "humidity": 0.7,
                "storm_chance": 0.2
            },
            Season.WINTER: {
                "temperature": -5.0,
                "humidity": 0.5,
                "storm_chance": 0.1
            }
        }
        return modifiers[self.current_season]

    def _generate_weather(self) -> WeatherState:
        modifiers = self._get_season_modifiers()
        
        temperature = (
            self.base_temperature +
            modifiers["temperature"] +
            random.gauss(0, 3)
        )
        
        humidity = min(1.0, max(0.0, modifiers["humidity"] + random.gauss(0, 0.1)))
        
        weather_types = []
        if self.current_season == Season.WINTER and temperature < 0:
            weather_types.append((WeatherType.SNOW, 3))
        if humidity > 0.7:
            weather_types.append((WeatherType.RAIN, 2))
        if random.random() < modifiers["storm_chance"]:
            weather_types.append((WeatherType.STORM, 1))
        if temperature > 30:
            weather_types.append((WeatherType.HEATWAVE, 1))
        
        weather_types.extend([
            (WeatherType.CLEAR, 3),
            (WeatherType.CLOUDY, 2)
        ])
        
        weather_type = random.choices(
            [wt[0] for wt in weather_types],
            weights=[wt[1] for wt in weather_types]
        )[0]
        
        if weather_type == WeatherType.STORM:
            wind_speed = random.uniform(15, 25)
            precipitation = random.uniform(0.7, 1.0)
        elif weather_type in {WeatherType.RAIN, WeatherType.SNOW}:
            wind_speed = random.uniform(5, 15)
            precipitation = random.uniform(0.4, 0.8)
        else:
            wind_speed = random.uniform(0, 10)
            precipitation = random.uniform(0, 0.3)
        
        return WeatherState(
            type=weather_type,
            temperature=temperature,
            humidity=humidity,
            wind_speed=wind_speed,
            precipitation=precipitation,
            duration=random.randint(5, 15)
        )

    def update(self) -> None:
        self.day_of_year = (self.day_of_year + 1) % 360
        
        new_season = Season(list(Season)[self.day_of_year // 90])
        if new_season != self.current_season:
            self.current_season = new_season
        
        self.weather_duration += 1
        if self.weather_duration >= self.current_weather.duration:
            self.current_weather = self._generate_weather()
            self.weather_duration = 0

@dataclass
class Position:
    x: int
    y: int
    
    def distance_to(self, other: 'Position') -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

@dataclass
class Personality:
    sociability: float
    industriousness: float
    curiosity: float
    caution: float
    
    @classmethod
    def random(cls) -> 'Personality':
        return cls(
            sociability=random.random(),
            industriousness=random.random(),
            curiosity=random.random(),
            caution=random.random()
        )

class Entity:
    def __init__(self, name: str, position: Position):
        self.name = name
        self.position = position
        self.personality = Personality.random()
        self.energy = 100.0
        self.hunger = 0.0
        self.social_need = 0.0
        self.temperature = 37.0
        self.inventory: Dict[ResourceType, float] = {r: 0.0 for r in ResourceType}
        self.relationships: Dict[str, float] = {}
        self.current_activity: Optional[ActivityType] = None
        self.has_shelter = False

    def update(self, world: 'World') -> None:
        self._handle_weather_effects(world.climate.current_weather)
        
        self.energy -= 1.0
        self.hunger += 0.5
        self.social_need += self.personality.sociability * 0.5

        self._choose_activity(world)
        self._perform_activity(world)

    def _handle_weather_effects(self, weather: WeatherState) -> None:
        temp_difference = weather.temperature - 20
        self.temperature = 37.0 + (temp_difference * 0.1)
        
        if abs(temp_difference) > 10:
            self.energy -= abs(temp_difference) * 0.1
        
        if weather.type == WeatherType.STORM:
            self.energy -= 2.0
        elif weather.type == WeatherType.SNOW:
            self.energy -= 1.5
        elif weather.type == WeatherType.HEATWAVE:
            self.hunger += 1.0
            self.energy -= 1.5

    def _choose_activity(self, world: 'World') -> None:
        weather = world.climate.current_weather
        
        if weather.is_dangerous and random.random() < self.personality.caution:
            self.current_activity = ActivityType.SEEKING_SHELTER
            return
        
        if self.energy < 30:
            self.current_activity = ActivityType.RESTING
        elif self.hunger > 70:
            self.current_activity = ActivityType.GATHERING
        elif self.social_need > 80:
            self.current_activity = ActivityType.SOCIALIZING
        else:
            self.current_activity = (
                ActivityType.BUILDING 
                if random.random() < self.personality.industriousness 
                else ActivityType.GATHERING
            )

    def _perform_activity(self, world: 'World') -> None:
        weather = world.climate.current_weather
        weather_modifier = self._get_weather_modifier(weather)
        
        if self.current_activity == ActivityType.RESTING:
            if self.has_shelter:
                self.energy = min(100, self.energy + 10 * weather_modifier)
            else:
                self.energy = min(100, self.energy + 5 * weather_modifier)
        
        elif self.current_activity == ActivityType.GATHERING:
            tile = world.get_tile(self.position)
            gathered = tile.gather_resources(weather_modifier)
            for resource, amount in gathered.items():
                self.inventory[resource] = self.inventory.get(resource, 0) + amount
                if resource == ResourceType.FOOD:
                    self.hunger = max(0, self.hunger - amount * 10)
        
        elif self.current_activity == ActivityType.SOCIALIZING:
            if not weather.is_dangerous or self.has_shelter:
                nearby_entities = world.get_nearby_entities(self, radius=3)
                for other in nearby_entities:
                    compatibility = self._calculate_compatibility(other)
                    relationship_change = compatibility * 0.1 * weather_modifier
                    self.relationships[other.name] = self.relationships.get(other.name, 0) + relationship_change
                    self.social_need = max(0, self.social_need - 10)
        
        elif self.current_activity == ActivityType.SEEKING_SHELTER:
            if not self.has_shelter and self.inventory[ResourceType.WOOD] >= 10:
                self.has_shelter = True
                self.inventory[ResourceType.WOOD] -= 10

    def _get_weather_modifier(self, weather: WeatherState) -> float:
        if weather.is_dangerous:
            return 0.5
        elif weather.type in {WeatherType.RAIN, WeatherType.SNOW}:
            return 0.7
        elif weather.type == WeatherType.CLOUDY:
            return 0.9
        return 1.0

    def _calculate_compatibility(self, other: 'Entity') -> float:
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

    def gather_resources(self, weather_modifier: float = 1.0) -> Dict[ResourceType, float]:
        gathered = {}
        for resource_type, amount in self.resources.items():
            if amount > 0:
                gathered_amount = min(random.random() * 10 * weather_modifier, amount)
                self.resources[resource_type] -= gathered_amount
                gathered[resource_type] = gathered_amount
        return gathered

    def regenerate_resources(self, weather: WeatherState, season: Season) -> None:
        base_resources = self._initialize_resources()
        
        season_modifiers = {
            Season.SPRING: 1.2,
            Season.SUMMER: 1.0,
            Season.AUTUMN: 0.8,
            Season.WINTER: 0.5
        }
        
        weather_modifiers = {
            WeatherType.CLEAR: 1.0,
            WeatherType.CLOUDY: 0.9,
            WeatherType.RAIN: 1.2,
            WeatherType.STORM: 0.5,
            WeatherType.SNOW: 0.3,
            WeatherType.HEATWAVE: 0.7
        }
        
        modifier = season_modifiers[season] * weather_modifiers[weather.type]
        
        for resource_type, max_amount in base_resources.items():
            current = self.resources[resource_type]
            if current < max_amount:
                regen_amount = random.random() * 5 * modifier
                self.resources[resource_type] = min(max_amount, current + regen_amount)

class World:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.entities: List[Entity] = []
        self.grid: List[List[Tile]] = self._generate_world()
        self.time = 0
        self.climate = Climate()

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
        self.climate.update()
        
        for entity in self.entities:
            entity.update(self)
        
        if self.time % 10 == 0:
            for row in self.grid:
                for tile in row:
                    tile.regenerate_resources(self.climate.current_weather, self.climate.current_season)

class WorldDemo:
    def __init__(self, world_size: int = 8):
        self.world = World(world_size, world_size)
        self.initialize_entities()
        
    def initialize_entities(self):
        entities = [
            ("Alice", "Cautious gatherer", 0.8),
            ("Bob", "Social butterfly", 0.3),
            ("Charlie", "
