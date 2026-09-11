#!/bin/bash

# ============================================
# AI Customer Intelligence Engine - Quick Start
# ============================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Display banner
echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║   AI Customer Intelligence Engine - Docker Deployment       ║"
echo "║   Dashboard | Analytics | Model Metrics                     ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check if Docker is installed
echo -e "${CYAN}Checking Docker installation...${NC}"
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓ Docker found: $DOCKER_VERSION${NC}"
else
    echo -e "${RED}✗ Docker not found! Please install Docker.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
echo -e "${CYAN}Checking Docker Compose...${NC}"
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓ Docker Compose found: $COMPOSE_VERSION${NC}"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    echo -e "${GREEN}✓ Docker Compose (V2) found: $COMPOSE_VERSION${NC}"
else
    echo -e "${RED}✗ Docker Compose not found!${NC}"
    exit 1
fi

# Display menu
echo -e "\n${CYAN}Select operation:${NC}"
echo "1) Start all services (PostgreSQL, Backend, Frontend)"
echo "2) Stop all services"
echo "3) View logs"
echo "4) Restart services"
echo "5) Full reset (warning: deletes data)"
echo "6) Health check"
echo "7) Exit"

read -p "Enter option (1-7): " choice

case $choice in
    1)
        echo -e "\n${CYAN}Starting services...${NC}"
        docker-compose up -d
        
        echo -e "${GREEN}✓ Services starting...${NC}"
        echo -e "${CYAN}Waiting for services to be ready...${NC}"
        sleep 15
        
        echo -e "\n${GREEN}✓ Services are running at:${NC}"
        echo -e "  ${CYAN}📊 Frontend Dashboard: http://localhost${NC}"
        echo -e "  ${CYAN}🔧 Backend API: http://localhost:5000${NC}"
        echo -e "  ${CYAN}📁 Database: localhost:5432${NC}"
        echo -e "\n${CYAN}View logs with: docker-compose logs -f${NC}"
        ;;
    2)
        echo -e "\n${CYAN}Stopping services...${NC}"
        docker-compose down
        echo -e "${GREEN}✓ Services stopped${NC}"
        ;;
    3)
        echo -e "\n${CYAN}Showing logs (Ctrl+C to exit)...${NC}"
        docker-compose logs -f
        ;;
    4)
        echo -e "\n${CYAN}Restarting services...${NC}"
        docker-compose restart
        echo -e "${GREEN}✓ Services restarted${NC}"
        ;;
    5)
        echo -e "\n${YELLOW}⚠️  WARNING: This will delete all data!${NC}"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            echo -e "${YELLOW}Performing full reset...${NC}"
            docker-compose down -v
            echo -e "${GREEN}✓ Reset complete${NC}"
        else
            echo -e "${CYAN}Cancelled${NC}"
        fi
        ;;
    6)
        echo -e "\n${CYAN}Checking service health...${NC}"
        
        # Check Backend
        if curl -s http://localhost:5000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Backend: Healthy${NC}"
        else
            echo -e "${RED}✗ Backend: Unreachable${NC}"
        fi
        
        # Check Frontend
        if curl -s http://localhost > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Frontend: Healthy${NC}"
        else
            echo -e "${RED}✗ Frontend: Unreachable${NC}"
        fi
        
        # Check Database
        if docker exec ai-intelligence-db pg_isready -U postgres -d customer_intelligence > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Database: Healthy${NC}"
        else
            echo -e "${RED}✗ Database: Unreachable${NC}"
        fi
        ;;
    7)
        echo -e "${CYAN}Exiting...${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid option!${NC}"
        ;;
esac
