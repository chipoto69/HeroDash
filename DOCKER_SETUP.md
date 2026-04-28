# Docker Setup Guide

This guide explains how to use Docker Compose to run all required services for Hero Dashboard.

## Quick Start

### 1. Start Core Services (Neo4j + Redis)

```bash
docker-compose up -d
```

This starts:
- **Neo4j** (ports 7474, 7687) - Graph database for Graphiti knowledge base
- **Redis** (port 6379) - In-memory cache for short-term memory

### 2. Start All Services (including NATS)

```bash
docker-compose --profile full up -d
```

This additionally starts:
- **NATS** (ports 4222, 8222, 6222) - Message broker for inter-agent communication

### 3. Configure Environment

Copy the example environment file and update it:

```bash
cp .env.example .env
```

Update the following in `.env`:

```bash
# Neo4j configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=hero_password_change_me  # Change this in production!
```

**Important**: For production use, change the Neo4j password in both `docker-compose.yml` and `.env`.

### 4. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

Expected output:
```
NAME                IMAGE                     STATUS
hero-neo4j          neo4j:5.18-community      Up (healthy)
hero-redis          redis:7-alpine            Up (healthy)
```

## Service Details

### Neo4j

**Purpose**: Graph database for Graphiti temporal knowledge graphs

**Access**:
- Browser UI: http://localhost:7474
- Bolt protocol: bolt://localhost:7687

**Default credentials**:
- Username: `neo4j`
- Password: `hero_password_change_me` (change this!)

**Data persistence**: Stored in Docker volume `neo4j_data`

### Redis

**Purpose**: In-memory key-value store for caching and short-term memory

**Access**:
- Redis CLI: `docker exec -it hero-redis redis-cli`
- Connection: `localhost:6379`

**Data persistence**: Stored in Docker volume `redis_data` with AOF (append-only file)

### NATS (Optional)

**Purpose**: Message broker for distributed agent communication

**Access**:
- Client connections: `nats://localhost:4222`
- Monitoring UI: http://localhost:8222

**Note**: NATS is only required for legacy inter-agent communication features. The rebooted Hero dashboard does not require it.

## Common Operations

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f neo4j
docker-compose logs -f redis
```

### Stop Services

```bash
# Stop but keep data
docker-compose stop

# Stop and remove containers (data persists in volumes)
docker-compose down

# Stop and remove everything including data
docker-compose down -v
```

### Restart Services

```bash
docker-compose restart
```

### Check Service Health

```bash
# Neo4j
docker exec hero-neo4j cypher-shell -u neo4j -p hero_password_change_me "RETURN 1"

# Redis
docker exec hero-redis redis-cli ping
```

## Data Management

### Backup Neo4j Data

```bash
# Create backup directory
mkdir -p backups

# Dump Neo4j database
docker exec hero-neo4j neo4j-admin database dump neo4j \
  --to-path=/var/lib/neo4j/import/backup.dump

# Copy to host
docker cp hero-neo4j:/var/lib/neo4j/import/backup.dump ./backups/
```

### Backup Redis Data

```bash
# Trigger save
docker exec hero-redis redis-cli BGSAVE

# Copy RDB file
docker cp hero-redis:/data/dump.rdb ./backups/redis-backup.rdb
```

### Restore from Backup

```bash
# Stop services first
docker-compose down

# Remove old data
docker volume rm herodash_neo4j_data herodash_redis_data

# Restart and restore (implementation depends on backup format)
docker-compose up -d
```

## Troubleshooting

### Neo4j won't start

1. Check logs: `docker-compose logs neo4j`
2. Ensure port 7687 is not in use: `lsof -i :7687`
3. Check disk space: `df -h`

### Redis connection refused

1. Check if Redis is running: `docker-compose ps redis`
2. Check logs: `docker-compose logs redis`
3. Verify port availability: `lsof -i :6379`

### Port conflicts

If ports are already in use, you can change them in `docker-compose.yml`:

```yaml
services:
  neo4j:
    ports:
      - "17474:7474"  # Changed HTTP port
      - "17687:7687"  # Changed Bolt port
```

Don't forget to update your `.env` file accordingly.

## Production Considerations

### Security

1. **Change default passwords**: Update Neo4j password in `docker-compose.yml` and `.env`
2. **Use secrets**: Consider using Docker secrets for sensitive data
3. **Network isolation**: Use custom Docker networks to isolate services
4. **Enable authentication**: Configure NATS authentication if using it in production

### Performance

1. **Resource limits**: Add resource constraints in `docker-compose.yml`:
   ```yaml
   services:
     neo4j:
       deploy:
         resources:
           limits:
             memory: 2G
           reservations:
             memory: 1G
   ```

2. **Neo4j tuning**: Adjust heap sizes for production workloads:
   ```yaml
   environment:
     - NEO4J_dbms_memory_heap_initial__size=1G
     - NEO4J_dbms_memory_heap_max__size=2G
   ```

3. **Redis maxmemory**: Configure memory limits and eviction policies:
   ```yaml
   command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru --appendonly yes
   ```

### Monitoring

1. **Neo4j metrics**: Available at http://localhost:7474/metrics
2. **Redis INFO**: `docker exec hero-redis redis-cli INFO`
3. **NATS monitoring**: Available at http://localhost:8222/varz

## Integration with Hero Dashboard

Once services are running:

1. Update `.env` with correct connection details
2. Run the Hero dashboard:
   ```bash
   ./launch_web_dashboard.sh start
   ```

3. Access the dashboard at http://127.0.0.1:8080

The dashboard will automatically detect and connect to the Docker services.

## Migration from External Services

If you were previously running Neo4j and Redis natively:

1. Export data from existing services
2. Start Docker services: `docker-compose up -d`
3. Import data into Docker services
4. Update `.env` to point to `localhost` ports
5. Stop old native services

## Additional Resources

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Redis Documentation](https://redis.io/documentation)
- [NATS Documentation](https://docs.nats.io/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
