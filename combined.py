import random
from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from enum import Enum
import math
from datetime import datetime, timedelta
import time
from colorama import init, Fore, Back, Style

# All the original simulator classes and code first
#[Previous class definitions for BiomeType, ResourceType, ActivityType, Season, WeatherType, 
#WeatherState, Climate, Position, Personality, Entity, Tile, and World remain exactly the same]

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
            status = "🏠" if entity.has_shelter else "  "
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
                        if entity.has_shelter:
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
