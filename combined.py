import random
from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from enum import Enum
import math
from datetime import datetime, timedelta
import time
from colorama import init, Fore, Back, Style

class BiomeType(Enum):
    FOREST = "Forest"
    PLAINS = "Plains"
    MOUNTAIN = "Mountain"
    DESERT = "Desert"
    TUNDRA = "Tundra"

class ResourceType(Enum):
    WOOD = "Wood"
    STONE = "Stone"
    FOOD = "Food"
    WATER = "Water"

class ActivityType(Enum):
    IDLE = "Idle"
    GATHERING = "Gathering"
    BUILDING = "Building"
    EXPLORING = "Exploring"
    SOCIALIZING = "Socializing"
    SEEKING_SHELTER = "Seeking Shelter"

class Season(Enum):
    SPRING = "Spring"
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"

class WeatherType(Enum):
    CLEAR = "Clear"
    CLOUDY = "Cloudy"
    RAIN = "Rain"
    STORM = "Storm"
    SNOW = "Snow"
    HEATWAVE = "Heatwave"

@dataclass
@dataclass
class ShelterState:
    durability: float = 100.0  # Max durability of shelter
    quality: float = 1.0  # Multiplier for weather protection (0.5-2.0)
    last_repair: int = 0  # Day of last repair

@dataclass
class WeatherState:
    type: WeatherType
    temperature: float
    wind_speed: float
    precipitation: float
    
    @property
    def is_dangerous(self) -> bool:
        return (self.temperature < -10 or 
                self.temperature > 40 or 
                self.wind_speed > 20 or 
                self.type in {WeatherType.STORM, WeatherType.HEATWAVE})

class Climate:
    def __init__(self):
        self.day_of_year = 0
        self.current_season = Season.SPRING
        self.current_weather = WeatherState(
            WeatherType.CLEAR, 20.0, 5.0, 0.0
        )
        
    def update(self):
        """Update climate conditions"""
        self.day_of_year = (self.day_of_year + 1) % 360
        
        # Update season every 90 days
        season_day = self.day_of_year % 360
        if season_day < 90:
            self.current_season = Season.SPRING
        elif season_day < 180:
            self.current_season = Season.SUMMER
        elif season_day < 270:
            self.current_season = Season.AUTUMN
        else:
            self.current_season = Season.WINTER
            
        # Base temperature varies by season
        base_temp = {
            Season.SPRING: 20,
            Season.SUMMER: 30,
            Season.AUTUMN: 15,
            Season.WINTER: 0
        }[self.current_season]
        
        # Random weather changes
        if random.random() < 0.2:  # 20% chance of weather change
            weather_options = list(WeatherType)
            if self.current_season == Season.WINTER:
                weather_options.remove(WeatherType.HEATWAVE)
            elif self.current_season == Season.SUMMER:
                weather_options.remove(WeatherType.SNOW)
            
            self.current_weather.type = random.choice(weather_options)
            
        # Update weather parameters
        temp_variation = random.uniform(-5, 5)
        wind_variation = random.uniform(-2, 2)
        precip_variation = random.uniform(-0.1, 0.1)
        
        self.current_weather.temperature = base_temp + temp_variation
        self.current_weather.wind_speed = max(0, self.current_weather.wind_speed + wind_variation)
        self.current_weather.precipitation = max(0, min(1, self.current_weather.precipitation + precip_variation))

@dataclass
class Position:
    x: int
    y: int
    
    def distance_to(self, other: 'Position') -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

@dataclass
class Personality:
    caution: float = 0.5  # 0-1, higher means more cautious
    sociability: float = 0.5  # 0-1, higher means more social
    industriousness: float = 0.5  # 0-1, higher means more hardworking

class Entity:
    def __init__(self, name: str, position: Position):
        self.name = name
        self.position = position
        self.personality = Personality()
        self.energy = 100.0
        self.temperature = 20.0  # body temperature
        self.inventory: Dict[ResourceType, float] = {
            ResourceType.WOOD: 0.0,
            ResourceType.STONE: 0.0,
            ResourceType.FOOD: 0.0,
            ResourceType.WATER: 0.0
        }
        self.relationships: Dict[str, float] = {}  # name -> relationship value
        self.current_activity: Optional[ActivityType] = None
        self.shelter: Optional[ShelterState] = None
        
    def update(self, world: 'World'):
        """Update entity state based on world conditions"""
        # Update shelter conditions
        self.update_shelter(world)
        
        # Update body temperature based on weather
        weather = world.climate.current_weather
        temp_diff = weather.temperature - self.temperature
        shelter_protection = 0.5 if self.shelter else 1.0  # Shelter reduces temperature effects
        self.temperature += temp_diff * 0.1 * shelter_protection
        
        # Energy consumption
        self.energy -= 1.0  # Base energy loss
        if self.current_activity:
            self.energy -= 2.0  # Additional loss for activities
        
        # Temperature stress
        if abs(self.temperature - 20) > 10:
            self.energy -= 2.0
        
        # Decision making
        if self.energy < 20 or weather.is_dangerous:
            self.seek_shelter(world)
        elif random.random() < 0.2:  # 20% chance to change activity
            self.choose_activity(world)
            
    def seek_shelter(self, world: 'World'):
        """Try to find or build shelter"""
        if not self.shelter:
            self.current_activity = ActivityType.SEEKING_SHELTER
            if self.inventory[ResourceType.WOOD] >= 5 and self.inventory[ResourceType.STONE] >= 3:
                self.shelter = ShelterState()
                self.inventory[ResourceType.WOOD] -= 5
                self.inventory[ResourceType.STONE] -= 3
                print(f"{self.name} built a new shelter!")
        elif self.shelter.durability < 50 and self.inventory[ResourceType.WOOD] >= 2:
            # Repair shelter
            self.inventory[ResourceType.WOOD] -= 2
            self.shelter.durability = min(100, self.shelter.durability + 40)
            self.shelter.last_repair = world.climate.day_of_year
            print(f"{self.name} repaired their shelter!")
                
    def update_shelter(self, world: 'World'):
        """Update shelter condition based on weather"""
        if not self.shelter:
            return
            
        weather = world.climate.current_weather
        
        # Calculate decay based on weather conditions
        decay_rate = 0.1  # Base decay
        if weather.type in {WeatherType.STORM, WeatherType.SNOW}:
            decay_rate += 0.4
        elif weather.type in {WeatherType.RAIN}:
            decay_rate += 0.2
        
        # Wind damage
        decay_rate += weather.wind_speed * 0.02
        
        # Apply decay
        self.shelter.durability -= decay_rate
        
        # Destroy shelter if durability reaches 0
        if self.shelter.durability <= 0:
            print(f"{self.name}'s shelter has collapsed!")
            self.shelter = None

    def choose_activity(self, world: 'World'):
        """Choose a new activity based on personality and circumstances"""
        if world.climate.current_weather.is_dangerous and self.personality.caution > 0.3:
            self.seek_shelter(world)
            return
            
        options = [
            (ActivityType.GATHERING, 0.3),
            (ActivityType.BUILDING, 0.2),
            (ActivityType.EXPLORING, 0.2),
            (ActivityType.SOCIALIZING, 0.2),
            (ActivityType.IDLE, 0.1)
        ]
        
        # Adjust probabilities based on personality
        if self.personality.sociability > 0.7:
            options[3] = (ActivityType.SOCIALIZING, 0.4)
        if self.personality.industriousness > 0.7:
            options[0] = (ActivityType.GATHERING, 0.4)
            options[1] = (ActivityType.BUILDING, 0.3)
            
        # Choose activity
        total = sum(prob for _, prob in options)
        r = random.uniform(0, total)
        cumsum = 0
        for activity, prob in options:
            cumsum += prob
            if r <= cumsum:
                self.current_activity = activity
                break

@dataclass
class Tile:
    biome: BiomeType
    resources: Dict[ResourceType, float]
    entities: Set[Entity]

class World:
    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.climate = Climate()
        self.entities: List[Entity] = []
        self.tiles: List[List[Tile]] = []
        
        # Initialize tiles
        for x in range(width):
            row = []
            for y in range(height):
                biome = random.choice(list(BiomeType))
                resources = {
                    ResourceType.WOOD: random.uniform(0, 100),
                    ResourceType.STONE: random.uniform(0, 100),
                    ResourceType.FOOD: random.uniform(0, 100),
                    ResourceType.WATER: random.uniform(0, 100)
                }
                row.append(Tile(biome, resources, set()))
            self.tiles.append(row)
            
    def add_entity(self, entity: Entity):
        """Add an entity to the world"""
        self.entities.append(entity)
        self.tiles[entity.position.x][entity.position.y].entities.add(entity)
        
    def update(self):
        """Update world state"""
        self.climate.update()
        
        # Update all entities
        for entity in self.entities:
            # Remove from old position
            self.tiles[entity.position.x][entity.position.y].entities.remove(entity)
            
            # Update entity
            entity.update(self)
            
            # Maybe move
            if random.random() < 0.3:  # 30% chance to move
                new_x = max(0, min(self.width-1, entity.position.x + random.randint(-1, 1)))
                new_y = max(0, min(self.height-1, entity.position.y + random.randint(-1, 1)))
                entity.position = Position(new_x, new_y)
            
            # Add to new position
            self.tiles[entity.position.x][entity.position.y].entities.add(entity)
            
            # Resource gathering
            if entity.current_activity == ActivityType.GATHERING:
                tile = self.tiles[entity.position.x][entity.position.y]
                for resource_type in ResourceType:
                    if tile.resources[resource_type] > 0:
                        gathered = min(5.0, tile.resources[resource_type])
                        tile.resources[resource_type] -= gathered
                        entity.inventory[resource_type] += gathered
            
            # Social interactions
            if entity.current_activity == ActivityType.SOCIALIZING:
                tile = self.tiles[entity.position.x][entity.position.y]
                for other in tile.entities:
                    if other != entity:
                        # Update relationship
                        if other.name not in entity.relationships:
                            entity.relationships[other.name] = 0.0
                        entity.relationships[other.name] += random.uniform(0.1, 0.3)

class WorldDemo:
    def __init__(self, world_size: int = 8):
        self.world = World(world_size, world_size)
        self.initialize_entities()
        
    def initialize_entities(self):
        """Create initial entities with different personalities"""
        entities = [
            ("Alice", "Cautious gatherer", 0.8),  # High caution
            ("Bob", "Social butterfly", 0.3),      # Low caution
            ("Charlie", "Industrious builder", 0.6),# Medium caution
            ("Diana", "Explorer", 0.4),            # Low-medium caution
        ]
        
        for name, desc, caution in entities:
            entity = Entity(name, Position(
                random.randint(0, self.world.width-1),
                random.randint(0, self.world.height-1)
            ))
            entity.personality.caution = caution
            self.world.add_entity(entity)
            print(f"Created {name}: {desc} (Caution: {caution:.1f})")

    def get_weather_display(self) -> str:
        """Get colored string representation of current weather"""
        weather = self.world.climate.current_weather
        weather_colors = {
            WeatherType.CLEAR: Fore.YELLOW + "☀",
            WeatherType.CLOUDY: Fore.WHITE + "☁",
            WeatherType.RAIN: Fore.BLUE + "🌧",
            WeatherType.STORM: Fore.RED + "⛈",
            WeatherType.SNOW: Fore.CYAN + "❄",
            WeatherType.HEATWAVE: Fore.RED + "🌡"
        }
        return weather_colors.get(weather.type, "?") + Style.RESET_ALL

    def get_season_display(self) -> str:
        """Get colored string representation of current season"""
        season = self.world.climate.current_season
        season_colors = {
            Season.SPRING: Fore.GREEN + "🌱",
            Season.SUMMER: Fore.YELLOW + "☀",
            Season.AUTUMN: Fore.RED + "🍂",
            Season.WINTER: Fore.CYAN + "❄"
        }
        return season_colors.get(season, "?") + Style.RESET_ALL

    def display_world_state(self):
        """Display current world state with weather and entity information"""
        weather = self.world.climate.current_weather
        print("\n" + "="*50)
        print(f"Day: {self.world.climate.day_of_year}")
        print(f"Season: {self.get_season_display()} {self.world.climate.current_season.value}")
        print(f"Weather: {self.get_weather_display()} {weather.type.value}")
        print(f"Temperature: {weather.temperature:.1f}°C")
        print(f"Wind Speed: {weather.wind_speed:.1f} m/s")
        print(f"Precipitation: {weather.precipitation:.2f}")
        
        print("\nEntities:")
        for entity in self.world.entities:
            status = "🏠" if entity.shelter else "  "
            if entity.shelter:
                status += f"({entity.shelter.durability:.0f}%)"
            else:
                status += "      "
            activity = entity.current_activity.value if entity.current_activity else "idle"
            print(f"{status} {entity.name:8} | Energy: {entity.energy:5.1f} | "
                  f"Temp: {entity.temperature:4.1f}°C | "
                  f"Activity: {activity:12} | "
                  f"Pos: ({entity.position.x}, {entity.position.y})")
            
            if entity.inventory:
                resources = ", ".join(
                    f"{r.value}: {amt:.1f}"
                    for r, amt in entity.inventory.items()
                    if amt > 0
                )
                print(f"   Inventory: {resources}")
            
            if entity.relationships:
                relations = ", ".join(
                    f"{name}: {val:.2f}"
                    for name, val in entity.relationships.items()
                )
                print(f"   Relationships: {relations}")

    def run_simulation(self, days: int = 50, delay: float = 2.0):
        """Run simulation for specified number of days"""
        print("\nStarting simulation...")
        print("="*50)
        
        try:
            for day in range(days):
                self.world.update()
                self.display_world_state()
                
                # Log significant events
                weather = self.world.climate.current_weather
                if weather.is_dangerous:
                    print(f"\n⚠ Warning: Dangerous weather conditions detected!")
                    for entity in self.world.entities:
                        if entity.shelter:
                            print(f"  {entity.name} is safely in shelter")
                        else:
                            print(f"  {entity.name} is exposed to the elements!")
                
                # Show season changes
                if day > 0 and day % 90 == 0:
                    print(f"\n🌍 Season changing to {self.world.climate.current_season.value}")
                
                time.sleep(delay)
                
        except KeyboardInterrupt:
            print("\nSimulation interrupted by user")
            return

def main():
    # Initialize colorama for Windows compatibility
    init()
    
    # Create and run demo
    print("Initializing World Simulator Demo...")
    demo = WorldDemo(world_size=8)
    
    # Run simulation
    demo.run_simulation(days=50, delay=2.0)
    
    print("\nSimulation complete!")

if __name__ == "__main__":
    main()
