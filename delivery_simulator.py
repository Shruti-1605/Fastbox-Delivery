import json
import math
import os
import random
import csv

# -----------------------------
# CONFIG
# -----------------------------
DATA_FOLDER = "data"
JSON_OUTPUT_FILE = "report.json"
CSV_OUTPUT_FILE = "top_performers.csv"

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def euclidean_distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def print_route(agent_id, agent_loc, warehouse_id, wh_loc, destination):
    print(f"{agent_id} {agent_loc} --> {warehouse_id} {wh_loc} --> DEST {destination}")

# -----------------------------
# MAIN PROCESSING
# -----------------------------
final_report = {}
top_performers = []

# Iterate over all datasets
for file_name in sorted(os.listdir(DATA_FOLDER)):
    if not file_name.endswith(".json"):
        continue

    dataset_name = file_name.replace(".json", "")
    file_path = os.path.join(DATA_FOLDER, file_name)

    # ---------- FILE LOAD SAFE ----------
    try:
        with open(file_path) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f" File not found: {file_name}")
        continue
    except json.JSONDecodeError:
        print(f" Invalid JSON format in: {file_name}")
        continue

    # ---------- NORMALIZE DATA ----------
    try:
        warehouses = {w["id"]: w["location"] for w in data["warehouses"]} \
            if isinstance(data["warehouses"], list) else data["warehouses"]

        agents = {a["id"]: a["location"] for a in data["agents"]} \
            if isinstance(data["agents"], list) else data["agents"]

        packages = data["packages"]
    except KeyError as e:
        print(f" Missing key {e} in dataset {dataset_name}")
        continue

    report = {agent_id: {"packages_delivered": 0, "total_distance": 0.0} for agent_id in agents}

    print(f"\n===== Processing Dataset: {dataset_name} =====\n")

    # ---------------- DELIVERY SIMULATION ----------------
    for idx, pkg in enumerate(packages, 1):

        # ---------- WAREHOUSE SAFE ----------
        try:
            wh_id = pkg.get("warehouse") or pkg.get("warehouse_id")
            wh_loc = warehouses[wh_id]
        except Exception:
            print(f" Invalid warehouse data in package {idx}: {pkg}")
            continue

        # ---------- MID-DAY AGENT ----------
        if "new_agent" in pkg:
            try:
                new_id = pkg["new_agent"]["id"]
                new_loc = pkg["new_agent"]["location"]
                if new_id not in agents:
                    agents[new_id] = new_loc
                    report[new_id] = {"packages_delivered": 0, "total_distance": 0.0}
                    print(f"** New agent {new_id} joined mid-day at {new_loc}! **")
            except Exception:
                print(" Error while adding mid-day agent")
                continue

        # ---------- NEAREST AGENT ----------
        try:
            nearest_agent = min(
                agents,
                key=lambda a: euclidean_distance(agents[a], wh_loc)
            )
        except ValueError:
            print("No agents available")
            continue

        agent_loc = agents[nearest_agent]

        # ---------- DISTANCE SAFE ----------
        try:
            dist_to_wh = euclidean_distance(agent_loc, wh_loc)
            dist_to_dest = euclidean_distance(wh_loc, pkg["destination"])
            dist_to_dest *= random.uniform(1.0, 1.2)
        except Exception as e:
            print(f" Distance calculation error: {e}")
            continue

        # ---------- UPDATE STATS ----------
        report[nearest_agent]["total_distance"] += dist_to_wh + dist_to_dest
        report[nearest_agent]["packages_delivered"] += 1
        agents[nearest_agent] = pkg["destination"]

        # ---------- OUTPUT ----------
        print(f"Package {idx} from {wh_id} at {wh_loc} to {pkg['destination']}")
        print(f"Assigned Agent: {nearest_agent}")
        print(f"Distance to Warehouse: {dist_to_wh:.2f}")
        print(f"Distance to Destination (with delay): {dist_to_dest:.2f}")
        print(f"Total Distance by {nearest_agent}: {report[nearest_agent]['total_distance']:.2f}")
        print(f"Packages Delivered by {nearest_agent}: {report[nearest_agent]['packages_delivered']}")
        print_route(nearest_agent, agent_loc, wh_id, wh_loc, pkg["destination"])
        print("-" * 50)

    # ---------------- EFFICIENCY ----------------
    best_agent = None
    best_eff = float("inf")

    for agent_id, stats in report.items():
        if stats["packages_delivered"] > 0:
            stats["total_distance"] = round(stats["total_distance"], 2)
            stats["efficiency"] = round(stats["total_distance"] / stats["packages_delivered"], 2)
            if stats["efficiency"] < best_eff:
                best_eff = stats["efficiency"]
                best_agent = agent_id
        else:
            stats["efficiency"] = 0.0
            stats["total_distance"] = round(stats["total_distance"], 2)

    report["best_agent"] = best_agent
    final_report[dataset_name] = report

    print(f"\n--- Summary for Dataset {dataset_name} ---")
    for a, s in report.items():
        if a != "best_agent":
            print(f"Agent {a}: Packages={s['packages_delivered']}, Distance={s['total_distance']}, Efficiency={s['efficiency']}")
    print(f"Best Agent: {best_agent}")
    print("=" * 70)

    if best_agent:
        top_performers.append({
            "Dataset": dataset_name,
            "Best Agent": best_agent,
            "Packages Delivered": report[best_agent]["packages_delivered"],
            "Total Distance": report[best_agent]["total_distance"],
            "Efficiency": report[best_agent]["efficiency"]
        })

# ---------------- SAVE FILES SAFE ----------------
try:
    with open(JSON_OUTPUT_FILE, "w") as f:
        json.dump(final_report, f, indent=4)

    with open(CSV_OUTPUT_FILE, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile,
            fieldnames=["Dataset", "Best Agent", "Packages Delivered", "Total Distance", "Efficiency"])
        writer.writeheader()
        writer.writerows(top_performers)
        print(" SIMULATION COMPLETE!")
        print(f" Report saved: {JSON_OUTPUT_FILE}")
        print(f"Top performers: {CSV_OUTPUT_FILE}")
    print("\n All datasets processed successfully!")
    
except Exception as e:
    print(f" Error while saving output files: {e}")
 