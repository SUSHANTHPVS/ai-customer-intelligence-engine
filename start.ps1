# ============================================
# AI Customer Intelligence Engine - Quick Start
# ============================================

# Colors for output
$colors = @{
    Success = 'Green'
    Error = 'Red'
    Info = 'Cyan'
    Warning = 'Yellow'
}

function Write-Color {
    param($Message, $Color = 'White')
    Write-Host $Message -ForegroundColor $Color
}

# Display banner
Write-Color "
╔══════════════════════════════════════════════════════════════╗
║   AI Customer Intelligence Engine - Docker Deployment       ║
║   Dashboard | Analytics | Model Metrics                     ║
╚══════════════════════════════════════════════════════════════╝
" -Color Cyan

# Check if Docker is installed
Write-Color "Checking Docker installation..." -Color Info
try {
    $dockerVersion = docker --version
    Write-Color "✓ Docker found: $dockerVersion" -Color Success
} catch {
    Write-Color "✗ Docker not found! Please install Docker Desktop." -Color Error
    exit 1
}

# Check if Docker Compose is installed
Write-Color "Checking Docker Compose..." -Color Info
try {
    $composeVersion = docker compose version
    Write-Color "✓ Docker Compose found: $composeVersion" -Color Success
} catch {
    Write-Color "✗ Docker Compose not found!" -Color Error
    exit 1
}

# Display menu
Write-Color "`nSelect operation:" -Color Info
Write-Color "1) Start all services (PostgreSQL, Backend, Frontend)" -Color Cyan
Write-Color "2) Stop all services" -Color Cyan
Write-Color "3) View logs" -Color Cyan
Write-Color "4) Restart services" -Color Cyan
Write-Color "5) Full reset (warning: deletes data)" -Color Cyan
Write-Color "6) Health check" -Color Cyan
Write-Color "7) Exit" -Color Cyan

$choice = Read-Host "Enter option (1-7)"

switch ($choice) {
    "1" {
        Write-Color "`nStarting services..." -Color Info
        docker compose up -d
        
        Write-Color "`n" -Color Success
        Write-Color "✓ Services starting..." -Color Success
        Write-Color "`nWaiting for services to be ready..." -Color Info
        Start-Sleep -Seconds 15
        
        Write-Color "`nServices are running at:" -Color Success
        Write-Color "  📊 Frontend Dashboard: http://localhost" -Color Cyan
        Write-Color "  🔧 Backend API: http://localhost:5000" -Color Cyan
        Write-Color "  📁 Database: localhost:5432" -Color Cyan
        Write-Color "`nView logs with: docker compose logs -f" -Color Info
    }
    "2" {
        Write-Color "`nStopping services..." -Color Info
        docker compose down
        Write-Color "✓ Services stopped" -Color Success
    }
    "3" {
        Write-Color "`nShowing logs (Ctrl+C to exit)..." -Color Info
        docker compose logs -f
    }
    "4" {
        Write-Color "`nRestarting services..." -Color Info
        docker compose restart
        Write-Color "✓ Services restarted" -Color Success
    }
    "5" {
        Write-Color "`n⚠️  WARNING: This will delete all data!" -Color Warning
        $confirm = Read-Host "Are you sure? (yes/no)"
        if ($confirm -eq "yes") {
            Write-Color "Performing full reset..." -Color Warning
            docker compose down -v
            Write-Color "✓ Reset complete" -Color Success
        } else {
            Write-Color "Cancelled" -Color Info
        }
    }
    "6" {
        Write-Color "`nChecking service health..." -Color Info
        
        # Check Backend
        try {
            $health = Invoke-WebRequest -Uri "http://localhost:5000/health" -ErrorAction Stop
            Write-Color "✓ Backend: Healthy" -Color Success
        } catch {
            Write-Color "✗ Backend: Unreachable" -Color Error
        }
        
        # Check Frontend
        try {
            $frontend = Invoke-WebRequest -Uri "http://localhost" -ErrorAction Stop
            Write-Color "✓ Frontend: Healthy" -Color Success
        } catch {
            Write-Color "✗ Frontend: Unreachable" -Color Error
        }
        
        # Check Database
        try {
            $dbCheck = docker exec ai-intelligence-db pg_isready -U postgres -d customer_intelligence
            Write-Color "✓ Database: Healthy" -Color Success
        } catch {
            Write-Color "✗ Database: Unreachable" -Color Error
        }
    }
    "7" {
        Write-Color "Exiting..." -Color Info
        exit 0
    }
    default {
        Write-Color "Invalid option!" -Color Error
    }
}
