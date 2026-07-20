#!/usr/bin/env python3
"""
Fix scheduler container entrypoint.
The current command runs pip install loop (15 apps) BEFORE bench schedule,
blocking the scheduler for minutes at startup.

Fix: Start bench schedule immediately, run pip install in background.

Run on the server: python3 fix_scheduler_entrypoint.py
Or forward via: plink ... "python3 -c $(cat fix_scheduler_entrypoint.py)"
"""
import subprocess, json

CONTAINER = "bismallah_ethiobiz_inshaallah-scheduler-1"
COMPOSE_DIR = "/root/bizhealth_src"

def get_container_info():
    r = subprocess.run(["docker", "inspect", CONTAINER, "--format", "{{json .Config.Cmd}}"],
        capture_output=True, text=True)
    if r.returncode != 0:
        print(f"ERROR: Container {CONTAINER} not found")
        return None
    return json.loads(r.stdout)

def fix_via_compose():
    """Fix by updating docker-compose.yml command"""
    import glob, yaml
    compose_files = glob.glob(f"{COMPOSE_DIR}/**/docker-compose*.yml", recursive=True)
    if not compose_files:
        compose_files = glob.glob(f"{COMPOSE_DIR}/docker-compose*.yml", recursive=True)
    print(f"Found compose files: {compose_files}")
    
    for cf in compose_files:
        with open(cf) as f:
            orig = f.read()
        data = yaml.safe_load(orig)
        changed = False
        for svc_name, svc in data.get("services", {}).items():
            if svc_name == "scheduler" or "scheduler" in str(svc.get("command", "")):
                old_cmd = svc.get("command", "")
                if isinstance(old_cmd, str) and "pip install" in old_cmd:
                    # Put pip install in background with &
                    new_cmd = old_cmd.replace(
                        "&& bench schedule",
                        "& bench schedule"
                    )
                    if "& bench schedule" not in new_cmd:
                        new_cmd = old_cmd.replace(
                            "; done && bench schedule",
                            "; done) & bench schedule"
                        )
                    if new_cmd != old_cmd:
                        svc["command"] = new_cmd
                        changed = True
                        print(f"  {cf} / {svc_name}: FIXED")
                        print(f"    OLD: {old_cmd[:80]}...")
                        print(f"    NEW: {new_cmd[:80]}...")
        if changed:
            with open(cf, "w") as f:
                yaml.dump(data, f, default_flow_style=False)
            print(f"  Updated {cf}")
    return changed

def fix_via_docker_update():
    """Fix by updating running container config (limited)"""
    # Stop old container
    print("Stopping old scheduler container...")
    subprocess.run(["docker", "stop", CONTAINER], check=False)
    subprocess.run(["docker", "rm", CONTAINER], check=False)
    
    # Get the original container config
    r = subprocess.run(["docker", "inspect", CONTAINER, "--format", "{{json .Config}}"],
        capture_output=True, text=True)
    config = json.loads(r.stdout)
    
    # Fix the command
    old_cmd = " ".join(config.get("Cmd", []))
    new_cmd = old_cmd.replace(
        "done && bench schedule",
        "done) & bench schedule"
    ).replace(
        "done& bench schedule",
        "done) & bench schedule"
    )
    
    print(f"Old Cmd: {old_cmd[:100]}...")
    print(f"New Cmd: {new_cmd[:100]}...")
    
    # Recreate container with same config but fixed command
    # Get mounts, env, network, etc.
    r2 = subprocess.run(["docker", "inspect", CONTAINER, "--format", "{{json .Mounts}}"],
        capture_output=True, text=True)
    mounts = json.loads(r2.stdout)
    
    r3 = subprocess.run(["docker", "inspect", CONTAINER, "--format", "{{json .NetworkSettings.Networks}}"],
        capture_output=True, text=True)
    networks = json.loads(r3.stdout)
    
    # Build docker run command
    cmd_parts = ["docker", "run", "-d", "--name", CONTAINER, "--restart", "unless-stopped"]
    for m in mounts:
        if m["Type"] == "bind":
            cmd_parts.extend(["-v", f"{m['Source']}:{m['Destination']}"])
        elif m["Type"] == "volume":
            cmd_parts.extend(["-v", f"{m['Name']}:{m['Destination']}"])
        elif m["Type"] == "tmpfs":
            cmd_parts.extend(["--tmpfs", m["Destination"]])
    
    for net, net_config in networks.items():
        cmd_parts.extend(["--network", net])
    
    cmd_parts.append(config["Image"])
    cmd_parts.extend(["bash", "-c", new_cmd])
    
    print(f"Running: {' '.join(cmd_parts[:5])} ...")
    subprocess.run(cmd_parts, check=True)
    print(f"Container {CONTAINER} recreated successfully!")

if __name__ == "__main__":
    import sys
    info = get_container_info()
    if not info:
        sys.exit(1)
    
    print(f"Current command: {info}")
    
    # Try compose fix first
    try:
        if fix_via_compose():
            print("\nCompose file fixed. Run 'docker-compose up -d scheduler' to apply.")
        else:
            print("\nNo compose file found or no change needed. Direct fix...")
            fix_via_docker_update()
    except ImportError:
        print("yaml not available. Using direct fix...")
        fix_via_docker_update()
