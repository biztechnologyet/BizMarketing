# Operations: Zero-Disruption Deployment Pipeline

## 1. The Core Constraint
The `ethiobiz.et` ERP system is in continuous live production carrying critical enterprise traffic. Standard Frappe deployment procedures such as `bench migrate`, `docker-compose down`, or editing files directly on the server are strictly prohibited as they will trigger system-wide locking or destructive DB restructuring.

## 2. Git-First Synchronization (The Blueprint)
All operations **must** conform to this exact deployment sequence:

1. **Local Development**: Write, debug, and securely build Python/JS inside the local clone (`bizmarketing/`).
2. **Version Control**: `git push origin main` everything securely.
3. **Container Injection**: 
   - SSH into the production server (`128.140.82.215`).
   - Execute a background `git pull` directly inside the Docker volume of the `backend` container specifically tracking the `bizmarketing` repo directory.
4. **Hitless Restart**:
   - `bench --site ethiobiz.et clear-cache`
   - `bench restart`
   - This reloads Frappe's Python memory context and JS routing without tearing down active HTTP connections or restructuring SQL databases.

## 3. Database Modifications
If a DocType schema must be modified (e.g. adding a custom field), do **not** click Export Customizations to deploy `.json` schema changes blindly, as the live server's `company_global_filter` requires careful manual instantiation. Build the Python logic separately.
