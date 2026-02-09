"""
Advanced Airport Surveillance Scenario Generator (FYP Final Version - Complete)
-----------------------------------------------------------------------------
Features:
- Topology: Star Topology (Edges -> Core Gateway -> Cloud)
- Physics: Wireless Perimeter (Rain Fade), Wired Interior (Stable), WAN Congestion
- Bottleneck: Shared WAN Link at the Core Gateway (1 Gbps)
- Chaos: Node Shutdowns, Link Degradations, Double Failures
- Context: Peak/Off-Peak traffic, Bursty Background Noise
- Scale: Generates 1000 unique scenarios for GNN training

Usage: python generate_dataset.py
"""

import json
import random
import os
from enum import Enum
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

# ------------------ ENUMS ------------------

class PolicyZone(Enum):
    PZ1_CRITICAL_SECURITY = 1
    PZ2_BOARDING_GATES = 2
    PZ3_PUBLIC_AREA = 3
    PZ4_VIP_RESTRICTED = 4
    PZ5_ARRIVAL_BAGGAGE = 5

class IntentCategory(Enum):
    SAFETY_CRITICAL = "safety_critical"
    CROWD_MONITORING = "crowd_monitoring"
    COST_OPTIMIZATION = "cost_optimization"
    NETWORK_QOS = "network_qos"
    CONTEXT_AWARE = "context_aware"
    FAULT_TOLERANCE = "fault_tolerance"
    MULTI_OBJECTIVE = "multi_objective"

# ------------------ DATACLASSES ------------------

@dataclass
class Camera:
    id: str
    zone: PolicyZone
    location: str
    priority: int
    resolution: str
    fps: int
    bitrate_mbps: float

@dataclass
class EdgeServer:
    id: str
    location: str
    cpu_cores: int
    memory_gb: int
    network_bandwidth_gbps: float

@dataclass
class NetworkLink:
    src: str
    dst: str
    capacity_mbps: float
    latency_ms: float
    packet_loss_rate: float
    stochastic: bool = False
    link_type: str = "wired"  # wired, wireless, wan

@dataclass
class VideoFlow:
    id: str
    camera_id: str
    zone: PolicyZone
    source: str
    destination: str
    backup_destination: str
    bitrate_mbps: float
    priority: int
    analytics_type: str
    compute_intensity: float
    processing_delay_ms: float

@dataclass
class Intent:
    id: str
    category: IntentCategory
    description: str
    target_zones: List[PolicyZone]
    constraints: Dict[str, Any]
    priority: int

@dataclass
class FailureEvent:
    target: str
    failure_type: str  # "shutdown", "link_degradation"
    start_time_s: int
    duration_s: int
    severity: float = 1.0

@dataclass
class BackgroundTraffic:
    id: str
    src: str
    dst: str
    start_time_s: float
    duration_s: float
    bitrate_mbps: float
    flow_type: str

# ------------------ SCENARIO GENERATOR ------------------

class ScenarioGenerator:
    def __init__(self, seed=42):
        random.seed(seed)
        self.cameras: List[Camera] = []
        self.edge_servers: List[EdgeServer] = []
        self.cloud_endpoints: List[Dict] = []
        self.network_links: List[NetworkLink] = []
        self.flows: List[VideoFlow] = []
        self.intents: List[Intent] = []
        self.background_traffic: List[BackgroundTraffic] = []
        self.failures: List[FailureEvent] = []

    # ---------- TOPOLOGY ----------
    def generate_topology(self):
        # 1. Define Cameras with Bitrate Logic
        self._add_terminal_cameras("TerminalA", "CheckIn", PolicyZone.PZ3_PUBLIC_AREA, 8)
        self._add_terminal_cameras("TerminalA", "Gates_A", PolicyZone.PZ2_BOARDING_GATES, 10)
        self._add_terminal_cameras("TerminalA", "VIP", PolicyZone.PZ4_VIP_RESTRICTED, 3)
        self._add_terminal_cameras("TerminalB", "CheckIn", PolicyZone.PZ3_PUBLIC_AREA, 8)
        self._add_terminal_cameras("TerminalB", "Gates_B", PolicyZone.PZ2_BOARDING_GATES, 12)
        self._add_terminal_cameras("TerminalB", "VIP", PolicyZone.PZ4_VIP_RESTRICTED, 3)
        self._add_terminal_cameras("TerminalC", "Gates_C", PolicyZone.PZ2_BOARDING_GATES, 8)
        self._add_terminal_cameras("TerminalC", "Baggage", PolicyZone.PZ5_ARRIVAL_BAGGAGE, 6)
        self._add_terminal_cameras("TerminalC", "Arrival", PolicyZone.PZ5_ARRIVAL_BAGGAGE, 4)
        self._add_terminal_cameras("Security", "Screening", PolicyZone.PZ1_CRITICAL_SECURITY, 15)
        self._add_terminal_cameras("Perimeter", "Fence", PolicyZone.PZ1_CRITICAL_SECURITY, 20) # Only these are Wireless
        self._add_terminal_cameras("Perimeter", "Apron", PolicyZone.PZ1_CRITICAL_SECURITY, 12) # Only these are Wireless
        self._add_terminal_cameras("Staff", "Corridors", PolicyZone.PZ1_CRITICAL_SECURITY, 8)
        self._add_terminal_cameras("Retail", "Shops", PolicyZone.PZ3_PUBLIC_AREA, 10)

        # 2. Infrastructure: Edges + Core Gateway
        self.edge_servers = [
            EdgeServer("edge_termA", "Terminal A", 16, 64, 10.0),
            EdgeServer("edge_termB", "Terminal B", 16, 64, 10.0),
            EdgeServer("edge_termC", "Terminal C", 16, 64, 10.0),
            EdgeServer("edge_security", "Security Hub", 32, 128, 25.0),
            EdgeServer("edge_perimeter", "Perimeter Control", 16, 64, 10.0),
            # THE CORE GATEWAY: Aggregates traffic, does NOT process CV
            EdgeServer("core_gateway", "Server Room", 64, 128, 100.0)
        ]
        
        # 3. Cloud Endpoints
        self.cloud_endpoints = [
            {"id": "cloud_primary", "location": "Region-1", "bandwidth_gbps": 100},
            {"id": "cloud_backup", "location": "Region-2", "bandwidth_gbps": 100},
        ]

        self._create_network_links()

    def _add_terminal_cameras(self, terminal: str, area: str, zone: PolicyZone, count: int):
        priority_map = {
            PolicyZone.PZ1_CRITICAL_SECURITY: 1, PolicyZone.PZ2_BOARDING_GATES: 2,
            PolicyZone.PZ3_PUBLIC_AREA: 3, PolicyZone.PZ4_VIP_RESTRICTED: 2,
            PolicyZone.PZ5_ARRIVAL_BAGGAGE: 3,
        }
        for i in range(count):
            if zone == PolicyZone.PZ1_CRITICAL_SECURITY:
                res, fps, bitrate = "4K", 30, 25.0
            elif zone in [PolicyZone.PZ2_BOARDING_GATES, PolicyZone.PZ4_VIP_RESTRICTED]:
                res, fps, bitrate = "1080p", 30, 8.0
            else:
                res, fps, bitrate = "1080p", 25, 6.0
            
            self.cameras.append(Camera(
                id=f"cam_{terminal}_{area}_{i:02d}", zone=zone, location=f"{terminal}/{area}",
                priority=priority_map[zone], resolution=res, fps=fps, bitrate_mbps=bitrate
            ))

    def _create_network_links(self):
        # 1. Edge -> Core Gateway (Internal High-Speed LAN)
        # 10 Gbps, Stable. Represents fiber within the airport.
        for edge in self.edge_servers:
            if edge.id == "core_gateway": continue
            self.network_links.append(NetworkLink(edge.id, "core_gateway", 10000, 1.0, 0.0, stochastic=False, link_type="wired"))

        # 2. Core Gateway -> Cloud (Shared WAN Uplink)
        # 1 Gbps (The Bottleneck), Stochastic (Internet Congestion).
        self.network_links.append(NetworkLink("core_gateway", "cloud_primary", 1000, 15.0, 0.001, stochastic=True, link_type="wan"))
        self.network_links.append(NetworkLink("core_gateway", "cloud_backup", 1000, 25.0, 0.001, stochastic=True, link_type="wan"))

        # 3. Camera -> Edge
        camera_to_edge_map = {
            "TerminalA": "edge_termA", "TerminalB": "edge_termB", "TerminalC": "edge_termC",
            "Security": "edge_security", "Perimeter": "edge_perimeter", "Staff": "edge_security",
            "Retail": "edge_termA"
        }
        
        for cam in self.cameras:
            terminal = cam.location.split('/')[0]
            edge = camera_to_edge_map.get(terminal, "edge_termA")
            
            # Logic: Only "Perimeter" is Wireless/Outdoor
            is_outdoor = (terminal == "Perimeter")
            is_wired = not is_outdoor
            
            capacity = 1000.0 if is_wired else 300.0
            latency = 1.0 if is_wired else 8.0
            loss = 0.0001 if is_wired else 0.005
            l_type = "wired" if is_wired else "wireless"
            
            self.network_links.append(NetworkLink(cam.id, edge, capacity, latency, loss, stochastic=is_outdoor, link_type=l_type))

    # ---------- PHYSICS ----------
    def apply_weather_physics(self, weather_condition: str):
        if weather_condition == "clear": return

        print(f"Applying weather physics: {weather_condition}")
        for link in self.network_links:
            if link.stochastic:
                # CASE A: Wireless (Physics - Rain Fade)
                if link.link_type == "wireless":
                    if weather_condition == "rain":
                        link.packet_loss_rate = 0.05
                        link.capacity_mbps *= 0.8
                    elif weather_condition == "storm":
                        link.packet_loss_rate = 0.15
                        link.capacity_mbps *= 0.6
                
                # CASE B: WAN (Congestion - Traffic Jams)
                elif link.link_type == "wan":
                    if weather_condition == "storm":
                        link.capacity_mbps *= 0.7  # Capacity drops to 700 Mbps
                        link.latency_ms *= 1.5

    # ---------- INTENTS ----------
    def generate_intents(self, time_context: str = "peak"):
        self.intents = []
        # RESTORED: Full list of intents
        self.intents.append(Intent("SC1", IntentCategory.SAFETY_CRITICAL, "Sub-200ms latency for security", 
                                   [PolicyZone.PZ1_CRITICAL_SECURITY], {"max_latency": 200}, 1))
        self.intents.append(Intent("SC2", IntentCategory.SAFETY_CRITICAL, "Prioritize intrusion detection", 
                                   [PolicyZone.PZ1_CRITICAL_SECURITY], {"priority_boost": True}, 1))
        self.intents.append(Intent("CM1", IntentCategory.CROWD_MONITORING, "Optimize check-in density monitoring", 
                                   [PolicyZone.PZ3_PUBLIC_AREA], {"min_fps": 15}, 2))
        self.intents.append(Intent("CO1", IntentCategory.COST_OPTIMIZATION, "Minimize cloud egress cost", 
                                   list(PolicyZone), {"max_cloud_ratio": 0.3}, 3))
        self.intents.append(Intent("NQ1", IntentCategory.NETWORK_QOS, "Limit packet loss < 1%", 
                                   list(PolicyZone), {"max_loss": 0.01}, 2))
        self.intents.append(Intent("FT1", IntentCategory.FAULT_TOLERANCE, "Failover to nearest edge", 
                                   list(PolicyZone), {"failover_enabled": True}, 1))
        
        if time_context == "peak":
            self.intents.append(Intent("CA1", IntentCategory.CONTEXT_AWARE, "Peak hour security boost", 
                                       [PolicyZone.PZ1_CRITICAL_SECURITY], {"bw_reservation": "50%"}, 1))
        elif time_context == "emergency":
             self.intents.append(Intent("CA2", IntentCategory.CONTEXT_AWARE, "EMERGENCY: Max reliability", 
                                       list(PolicyZone), {"override_cost": True}, 1))

    # ---------- FLOWS ----------
    def generate_flows(self, placement_strategy: str = "random"):
        self.flows = []
        
        analytics_map = {
            PolicyZone.PZ1_CRITICAL_SECURITY: "intrusion",
            PolicyZone.PZ2_BOARDING_GATES: "passenger_flow",
            PolicyZone.PZ3_PUBLIC_AREA: "crowd_analytics",
            PolicyZone.PZ4_VIP_RESTRICTED: "occupancy",
            PolicyZone.PZ5_ARRIVAL_BAGGAGE: "baggage_tracking",
        }
        
        analytics_profile = {
            "intrusion": {"intensity": 0.8, "delay": 150.0},
            "crowd_analytics": {"intensity": 0.4, "delay": 60.0},
            "passenger_flow": {"intensity": 0.5, "delay": 80.0},
            "occupancy": {"intensity": 0.1, "delay": 20.0},
            "baggage_tracking": {"intensity": 0.6, "delay": 90.0},
        }

        camera_to_edge_map = {
            "TerminalA": "edge_termA", "TerminalB": "edge_termB", "TerminalC": "edge_termC",
            "Security": "edge_security", "Perimeter": "edge_perimeter", "Staff": "edge_security",
            "Retail": "edge_termA"
        }

        for cam in self.cameras:
            local_edge = camera_to_edge_map.get(cam.location.split('/')[0], "edge_termA")
            
            # Destination Strategy (Excluding Core Gateway)
            if placement_strategy == "all_edge": dest = local_edge
            elif placement_strategy == "all_cloud": dest = "cloud_primary"
            elif placement_strategy == "critical_edge":
                dest = local_edge if cam.zone == PolicyZone.PZ1_CRITICAL_SECURITY else "cloud_primary"
            else: 
                # Random choice between Local Edge and Cloud (Never Core Gateway)
                dest = random.choice([e.id for e in self.edge_servers if e.id != "core_gateway"] + ["cloud_primary"])

            # Backup Strategy
            backup = "cloud_primary" if dest != "cloud_primary" else "edge_security"

            task = analytics_map[cam.zone]
            base_profile = analytics_profile.get(task, {"intensity": 0.5, "delay": 50.0})

            # RESTORED: Compute Jitter (+/- 10%)
            jitter = random.uniform(0.9, 1.1)
            final_intensity = min(1.0, base_profile["intensity"] * jitter)
            
            self.flows.append(VideoFlow(
                id=f"flow_{cam.id}", camera_id=cam.id, zone=cam.zone, source=cam.id, destination=dest,
                backup_destination=backup, bitrate_mbps=cam.bitrate_mbps, priority=cam.priority, 
                analytics_type=task, compute_intensity=final_intensity, processing_delay_ms=base_profile["delay"]
            ))

    # ---------- BACKGROUND TRAFFIC ----------
    def generate_background_traffic(self, num_flows: int = 50):
        self.background_traffic = []
        terminals = ["edge_termA", "edge_termB", "edge_termC"] # Traffic starts at Edge
        for i in range(num_flows):
            src = random.choice(terminals)
            # Destination is Cloud (Passing through Core Gateway)
            self.background_traffic.append(BackgroundTraffic(
                id=f"bg_{i}", src=src, dst="cloud_primary",
                start_time_s=random.randint(0, 600), duration_s=random.randint(30, 300),
                bitrate_mbps=random.uniform(5.0, 20.0), flow_type="TCP"
            ))

    # ---------- FAILURES ----------
    def generate_failures(self):
        self.failures = []
        scenario_roll = random.random()
        
        # RESTORED: Complex Failure Logic
        if scenario_roll > 0.85:
            # Case A: Edge Shutdown (Severe)
            # Pick an edge server (excluding Core Gateway)
            targets = [e.id for e in self.edge_servers if e.id != "core_gateway"]
            if targets:
                edge = random.choice(targets)
                start = random.randint(100, 400)
                self.failures.append(FailureEvent(edge, "shutdown", start, 120, severity=1.0))
                print(f"Generated EVENT: {edge} shutdown")
            
        elif scenario_roll > 0.70:
            # Case B: Link Degradation (Latency Spike on WAN)
            link_target = "core_gateway_cloud_primary" # The bottleneck link
            start = random.randint(50, 300)
            self.failures.append(FailureEvent(link_target, "link_degradation", start, 200, severity=0.2)) 
            print(f"Generated EVENT: {link_target} degraded")
            
        elif scenario_roll > 0.65:
            # Case C: Double Failure (Rare)
            targets = [e.id for e in self.edge_servers if e.id != "core_gateway"]
            if len(targets) >= 2:
                e1 = targets[0]
                e2 = targets[-1]
                self.failures.append(FailureEvent(e1, "shutdown", 100, 60, severity=1.0))
                self.failures.append(FailureEvent(e2, "shutdown", 120, 60, severity=1.0))
                print(f"Generated EVENT: Double Shutdown ({e1}, {e2})")

    # ---------- EXPORT ----------
    def export_scenario(self, filename: str, scenario_id: int, weather_context: str):
        scenario = {
            "scenario_id": scenario_id,
            "context": {
                "weather": weather_context,
                "time_of_day": "peak" if len(self.background_traffic) > 50 else "off_peak"
            },
            "cameras": [asdict(c) for c in self.cameras],
            "edge_servers": [asdict(e) for e in self.edge_servers],
            "cloud_endpoints": self.cloud_endpoints,
            "network_links": [asdict(l) for l in self.network_links],
            "flows": [asdict(f) for f in self.flows],
            "background_traffic": [asdict(b) for b in self.background_traffic],
            "intents": [asdict(i) for i in self.intents],
            "failures": [asdict(f) for f in self.failures]
        }
        
        def custom_serializer(obj):
            if isinstance(obj, Enum): return obj.name
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(filename, 'w') as f:
            json.dump(scenario, f, default=custom_serializer, indent=2)

# ------------------ MAIN EXECUTION ------------------

def generate_dataset(num_scenarios: int = 1000, output_dir: str = "final_scenarios_core"):
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    time_contexts = ["peak", "off_peak", "emergency"]
    weather_conditions = ["clear", "rain", "storm"]
    placement_strategies = ["random", "all_edge", "critical_edge", "all_cloud"]

    for i in range(num_scenarios):
        gen = ScenarioGenerator(seed=42 + i)
        
        gen.generate_topology()
        
        weather = random.choice(weather_conditions)
        time_ctx = random.choice(time_contexts)
        
        # Apply physics BEFORE logic
        gen.apply_weather_physics(weather)
        
        gen.generate_intents(time_context=time_ctx)
        
        placement = random.choice(placement_strategies)
        gen.generate_flows(placement_strategy=placement)
        
        # Traffic scaling: Peak has more noise
        bg_load = random.randint(60, 100) if time_ctx == "peak" else random.randint(10, 30)
        gen.generate_background_traffic(num_flows=bg_load)
        
        gen.generate_failures()
        
        filename = f"{output_dir}/scenario_{i:04d}.json"
        gen.export_scenario(filename, i, weather_context=weather)

    print(f"\nSuccessfully generated {num_scenarios} scenarios in '{output_dir}/'")

if __name__ == "__main__":
    generate_dataset(1000, "final_scenarios_core")