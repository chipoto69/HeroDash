# CLI Command Centre Agent Briefing (PID 49864)

## Mission: Create Beautiful CLI Command Centre Interface

### Current System Status
- **Web Dashboard**: Running on http://localhost:8080 (PID 52338)
- **Data Sources**: JSON files in `~/.hero_core/cache/`
- **Update Frequency**: Real-time (5-15 second intervals)
- **Agent Team**: 5 Chimera Project agents coordinated

### Key Endpoints & Data Sources

#### 1. Main Dashboard Data
**URL**: `http://localhost:8080/api/dashboard`
**Method**: GET
**Description**: Comprehensive dashboard data including all agents, metrics, and coordination stats

#### 2. Real-Time Agent Status
**File**: `~/.hero_core/cache/agent_runtime_status.json`
**Contains**:
- 5 Chimera agents (PIDs: 1181, 88050, 57730, 89852, 95867)
- Current tasks, status (active/busy/idle)
- Performance metrics (tasks_completed, success_rate, errors)
- Last heartbeat timestamps
- Project info: "Architecture Upgrade Implementation"

#### 3. Agent Coordination Data
**File**: `~/.hero_core/cache/agent_coordination.json`
**Contains**:
- Session statistics
- Load balancing scores
- Task distribution metrics
- Recent activity logs with task assignments

#### 4. LangSmith Traces
**File**: `~/.hero_core/cache/langsmith_stats.json`
**Contains**:
- Total traces: 3,888+ (growing)
- Success rate: 99.97%
- Session duration: 1h+ active
- Agent breakdown by coordinator

#### 5. Custom Agents
**Files**: 
- `~/.hero_core/cache/custom_agent_32a3be6e.json` (DevTestAgent)
- `~/.hero_core/cache/custom_agent_48e88a2d.json` (SimulatedAgent - 172 tasks completed)

### CLI Interface Requirements

#### Display Sections Needed:
1. **Header**: Hero Command Centre + current time + uptime
2. **System Status**: Port 8080, dashboard health, total connections
3. **Chimera Project Team** (Priority Display):
   - Architect (PID 1181) - Project Lead - Status: Active
   - Ampcode (PID 88050) - Frontend Dev - Status: Busy (Performance Optimization)
   - Ampcode2 (PID 57730) - Backend Dev - Status: Active
   - DocOrchestrator (PID 89852) - Documentation - Status: Busy (Tech Specs)
   - ImplCoder (PID 95867) - Implementation - Status: Busy (Implementation Strategy)

4. **Performance Metrics**:
   - Success rates, task counts, error rates
   - Response times, load balancing scores
   - LangSmith trace counts and completion rates

5. **Active Tasks** (Real-time):
   - Current task assignments per agent
   - Task queue status
   - Project phase: Implementation

6. **System Resources**:
   - Memory usage, CPU, network connections
   - Cache file timestamps and sizes

### Data Refresh Strategy
- **High Priority**: Agent status, current tasks (every 5 seconds)
- **Medium Priority**: Performance metrics (every 15 seconds)  
- **Low Priority**: System resources (every 30 seconds)

### CLI Styling Recommendations
- **Colors**: Green for active, Yellow for busy, Red for errors, Blue for info
- **Layout**: Top status bar, main content grid, bottom status line
- **Progress Bars**: For task completion, success rates, uptime
- **Real-time Updates**: Timestamps, heartbeat indicators
- **Interactive**: Arrow keys for navigation, space to pause updates

### Error Handling
- Handle missing JSON files gracefully
- Show "Data Loading..." when files are being written
- Retry logic for race conditions during file updates
- Fallback to previous data if new data is corrupted

### Integration Points
- Can call web dashboard API endpoints for additional data
- Monitor WebSocket connections for real-time updates
- Watch file system changes for instant updates
- Option to send commands back to coordination system

### Expected Output Format
```
╭─────────────────── HERO COMMAND CENTRE ──────────────────╮
│ Port: 8080 │ Uptime: 1h 3m │ Agents: 5 │ Status: LIVE   │
├───────────────────────────────────────────────────────────┤
│ 🎯 CHIMERA PROJECT - Architecture Upgrade Implementation  │
│                                                           │
│ ┌─ LEAD ─────────────────────────────────────────────────┐│
│ │ 👑 Architect (1181)     [ACTIVE]  Tasks: 1/1  100%    ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─ CODING TEAM ───────────────────────────────────────────┐│
│ │ ⚡ Ampcode (88050)      [BUSY]    Perf Optimization    ││
│ │ 🔧 Ampcode2 (57730)     [ACTIVE]  Ready for tasks      ││
│ └─────────────────────────────────────────────────────────┘│
│ ┌─ SUPPORT TEAM ──────────────────────────────────────────┐│
│ │ 📝 DocOrch (89852)      [BUSY]    Technical Specs      ││
│ │ 🏗️  ImplCoder (95867)    [BUSY]    Implementation       ││
│ └─────────────────────────────────────────────────────────┘│
│                                                           │
│ Performance: ████████░░ 93.6% │ Traces: 3,888 │ Errors: 11│
╰─────────────────────────────────────────────────────────────╯
```

### Mission Success Criteria
- ✅ Real-time updates (< 5 second latency)
- ✅ All 5 Chimera agents visible with correct status
- ✅ Task assignments and progress tracking
- ✅ Clean, readable terminal interface
- ✅ Error handling and graceful degradation
- ✅ Performance metrics and system health

**Ready for deployment!** All systems are live and data streams are active. The Command Centre awaits your CLI interface! 🚀