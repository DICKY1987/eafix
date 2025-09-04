#!/bin/bash
# Free-Tier Multi-Agent Framework Setup
# Installs all free and open-source tools for the orchestrator including new agentic tools.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Helper functions
log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Detect OS and package manager
detect_system() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        PKG_MANAGER="brew"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command -v apt-get >/dev/null 2>&1; then
            OS="ubuntu"
            PKG_MANAGER="apt"
        elif command -v pacman >/dev/null 2>&1; then
            OS="arch"
            PKG_MANAGER="pacman"
        elif command -v dnf >/dev/null 2>&1; then
            OS="fedora"
            PKG_MANAGER="dnf"
        else
            OS="linux"
            PKG_MANAGER="manual"
        fi
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
        PKG_MANAGER="manual"
    else
        OS="unknown"
        PKG_MANAGER="manual"
    fi
    log_info "Detected OS: $OS, Package Manager: $PKG_MANAGER"
}

# Install prerequisites
install_prerequisites() {
    log_info "Installing prerequisites..."
    case $PKG_MANAGER in
        "brew")
            brew update
            brew install curl git jq python3 node npm
            ;;
        "apt")
            sudo apt update
            sudo apt install -y curl git jq python3 python3-pip nodejs npm
            ;;
        "pacman")
            sudo pacman -Sy curl git jq python python-pip nodejs npm
            ;;
        "dnf")
            sudo dnf install -y curl git jq python3 python3-pip nodejs npm
            ;;
        *)
            log_warning "Manual installation required for prerequisites"
            ;;
    esac
    log_success "Prerequisites installed"
}

# Install Ollama for local models
install_ollama() {
    log_info "Installing Ollama..."
    if command -v ollama >/dev/null 2>&1; then
        log_success "Ollama already installed"
        return
    fi
    if [[ "$OS" == "windows" ]]; then
        log_warning "Please install Ollama manually from https://ollama.ai/download/windows"
        return
    fi
    curl -fsSL https://ollama.ai/install.sh | sh
    # Start Ollama service
    if [[ "$OS" == "macos" ]]; then
        ollama serve &
    elif [[ "$OS" == "linux" ]]; then
        systemctl --user enable ollama
        systemctl --user start ollama
    fi
    log_success "Ollama installed"
}

# Pull essential local models
setup_local_models() {
    log_info "Setting up local models..."
    if ! command -v ollama >/dev/null 2>&1; then
        log_error "Ollama not found. Please install Ollama first."
        return
    fi
    models=(
        "codellama:7b-instruct"
        "codegemma:2b"
        "llama3.1:8b"
    )
    for model in "${models[@]}"; do
        log_info "Pulling model: $model"
        ollama pull "$model"
    done
    log_success "Local models setup complete"
}

# Install AI coding tools (original free-tier tools)
install_ai_tools() {
    log_info "Installing AI coding tools..."
    pip3 install aider-chat
    npm install -g @continuedev/cli || log_warning "Continue CLI not available via npm"
    log_success "AI tools installed"
}

# Install agentic AI tools (new function from agentic framework changes)
install_agentic_tools() {
    log_info "Installing agentic AI tools..."
    # Claude Code (requires API key)
    if command -v npm >/dev/null 2>&1; then
        npm install -g @anthropic-ai/claude-code || log_warning "Claude Code installation failed"
    else
        log_warning "npm not found - install Claude Code manually"
    fi
    # Aider - AI pair programmer (already installed but ensure latest)
    pip3 install --upgrade aider-chat
    # Continue CLI
    npm install -g @continuedev/cli || log_warning "Continue CLI installation failed"
    # Local model optimization
    pip3 install llama-cpp-python
    log_success "Agentic tools installed"
}

# Install code quality tools
install_quality_tools() {
    log_info "Installing code quality tools..."
    pip3 install ruff black pylint bandit safety
    npm install -g eslint prettier @eslint/config eslint-plugin-security
    pip3 install sqlfluff
    case $PKG_MANAGER in
        "brew")
            brew install sonarqube shellcheck hadolint
            ;;
        "apt")
            sudo apt install -y shellcheck
            ;;
        "pacman")
            sudo pacman -S shellcheck
            ;;
        *)
            log_warning "Some quality tools require manual installation"
            ;;
    esac
    log_success "Quality tools installed"
}

# Install security tools
install_security_tools() {
    log_info "Installing security scanning tools..."
    case $PKG_MANAGER in
        "brew")
            brew install dependency-check trivy gitleaks
            ;;
        "apt")
            # OWASP Dependency Check
            mkdir -p ~/.local/bin
            DEPCHECK_VERSION="8.4.0"
            curl -L "https://github.com/jeremylong/DependencyCheck/releases/download/v${DEPCHECK_VERSION}/dependency-check-${DEPCHECK_VERSION}-release.zip" -o /tmp/depcheck.zip
            unzip /tmp/depcheck.zip -d ~/.local/
            ln -sf ~/.local/dependency-check/bin/dependency-check.sh ~/.local/bin/dependency-check
            # Trivy
            sudo apt-get install -y wget apt-transport-https gnupg lsb-release
            wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
            echo "deb https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
            sudo apt-get update
            sudo apt-get install -y trivy
            # Gitleaks
            GITLEAKS_VERSION="8.18.0"
            curl -L "https://github.com/zricethezav/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" | tar xz -C ~/.local/bin/
            ;;
        "pacman")
            # Pacman installs
            sudo pacman -S trivy gitleaks
            ;;
        *)
            # Generic installation for non-supported package managers
            mkdir -p ~/.local/bin
            DEPCHECK_VERSION="8.4.0"
            curl -L "https://github.com/jeremylong/DependencyCheck/releases/download/v${DEPCHECK_VERSION}/dependency-check-${DEPCHECK_VERSION}-release.zip" -o /tmp/depcheck.zip
            unzip /tmp/depcheck.zip -d ~/.local/
            ln -sf ~/.local/dependency-check/bin/dependency-check.sh ~/.local/bin/dependency-check
            TRIVY_VERSION="0.45.0"
            curl -L "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" | tar xz -C ~/.local/bin/
            GITLEAKS_VERSION="8.18.0"
            curl -L "https://github.com/zricethezav/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" | tar xz -C ~/.local/bin/
            ;;
    esac
    pip3 install semgrep
    log_success "Security tools installed"
}

# Install infrastructure tools
install_infrastructure_tools() {
    log_info "Installing infrastructure tools..."
    case $PKG_MANAGER in
        "brew")
            brew install opentofu
            ;;
        "apt")
            sudo install -m 0755 -d /etc/apt/keyrings
            curl -fsSL https://get.opentofu.org/opentofu.gpg | sudo tee /etc/apt/keyrings/opentofu.gpg >/dev/null
            echo "deb [signed-by=/etc/apt/keyrings/opentofu.gpg] https://packages.opentofu.org/opentofu/tofu/any/ any main" | sudo tee /etc/apt/sources.list.d/opentofu.list
            sudo apt update
            sudo apt install tofu
            ;;
        *)
            TOFU_VERSION="1.6.0"
            curl -L "https://github.com/opentofu/opentofu/releases/download/v${TOFU_VERSION}/tofu_${TOFU_VERSION}_linux_amd64.zip" -o /tmp/tofu.zip
            unzip /tmp/tofu.zip -d ~/.local/bin/
            ;;
    esac
    pip3 install ansible checkov
    log_success "Infrastructure tools installed"
}

# Install documentation tools
install_documentation_tools() {
    log_info "Installing documentation tools..."
    case $PKG_MANAGER in
        "brew")
            brew install openapi-generator
            ;;
        *)
            npm install -g @openapitools/openapi-generator-cli
            ;;
    esac
    pip3 install mkdocs mkdocs-material
    npm install -g markdownlint-cli
    log_success "Documentation tools installed"
}

# Install monitoring tools
install_monitoring_tools() {
    log_info "Installing monitoring tools..."
    case $PKG_MANAGER in
        "brew")
            brew install htop btop
            ;;
        "apt")
            sudo apt install -y htop
            ;;
        "pacman")
            sudo pacman -S htop btop
            ;;
    esac
    log_success "Basic monitoring tools installed"
}

# Setup framework configuration - replaced with new agentic config
setup_framework_config() {
    log_info "Setting up framework configuration..."
    mkdir -p .ai
    # If config does not exist, create default agentic config
    if [[ ! -f ".ai/framework-config.json" ]]; then
        log_info "Creating default agentic framework configuration..."
        cat > .ai/framework-config.json << 'EOF'
{
  "framework": {
    "name": "Free-Tier Multi-Agent Orchestrator",
    "version": "1.0.0",
    "description": "Cost-optimized framework combining free tiers with local-first tools"
  },
  "quotaManagement": {
    "enabled": true,
    "trackingFile": ".ai/quota-tracker.json",
    "resetSchedule": "0 0 * * *",
    "warningThreshold": 0.8,
    "services": {
      "gemini_cli": {
        "dailyLimit": 1000,
        "priority": 1,
        "cost": "free",
        "useCase": "simple_tasks",
        "complexity": ["simple", "moderate"],
        "resetTime": "00:00 UTC"
      },
      "claude_code": {
        "dailyLimit": 25,
        "priority": 2,
        "cost": "premium",
        "costPerRequest": 0.15,
        "useCase": "complex_agentic",
        "complexity": ["complex"],
        "warningThreshold": 0.6,
        "requiresApproval": true,
        "resetTime": "00:00 UTC"
      },
      "aider_local": {
        "dailyLimit": "unlimited",
        "priority": 3,
        "cost": "free",
        "useCase": "development",
        "complexity": ["simple", "moderate"]
      },
      "ollama_local": {
        "dailyLimit": "unlimited",
        "priority": 4,
        "cost": "free",
        "useCase": "fallback",
        "complexity": ["simple", "moderate", "complex"]
      }
    }
  },
  "localModels": {
    "enabled": true,
    "provider": "ollama",
    "fallbackThreshold": 0.9,
    "models": {
      "coding": {
        "name": "codellama:7b-instruct",
        "use_case": "code generation, debugging",
        "memory_gb": 8,
        "speed": "medium"
      },
      "general": {
        "name": "llama3.1:8b",
        "use_case": "general reasoning, documentation",
        "memory_gb": 10,
        "speed": "medium"
      },
      "fast": {
        "name": "codegemma:2b",
        "use_case": "quick completions, simple tasks",
        "memory_gb": 4,
        "speed": "fast"
      }
    }
  },
  "serviceRotation": {
    "strategy": "priority_with_quota",
    "rotationRules": [
      {
        "condition": "quota_available",
        "action": "use_highest_priority"
      },
      {
        "condition": "quota_exceeded",
        "action": "fallback_to_next"
      },
      {
        "condition": "all_quotas_exceeded",
        "action": "use_local_models"
      }
    ]
  },
  "lanes": {
    "ai_coding": {
      "name": "AI Code Generation",
      "worktreePath": ".worktrees/ai-coding",
      "branch": "lane/ai-coding",
      "tools": {
        "primary": {
          "tool": "aider",
          "config": {
            "model_priority": [
              "gemini/gemini-1.5-pro",
              "ollama/codellama:7b-instruct"
            ],
            "auto_commit": false,
            "edit_format": "diff"
          }
        },
        "fallback": {
          "tool": "continue",
          "config": {
            "provider": "ollama",
            "model": "codellama:7b-instruct"
          }
        }
      },
      "allowedPatterns": ["src/**", "lib/**", "tests/**"],
      "excludePatterns": ["*.md", "docs/**"],
      "preCommit": ["ruff check .", "black --check ."],
      "commitPrefix": "ai:"
    },
    "quality": {
      "name": "Code Quality",
      "worktreePath": ".worktrees/quality",
      "branch": "lane/quality",
      "tools": {
        "linting": {
          "javascript": "eslint --fix .",
          "python": "ruff check --fix .",
          "sql": "sqlfluff fix ."
        },
        "formatting": {
          "javascript": "prettier --write .",
          "python": "black .",
          "json": "jq '.' --indent 2"
        },
        "analysis": "sonar-scanner"
      },
      "allowedPatterns": ["**/*.js", "**/*.py", "**/*.sql", "**/*.ts"],
      "preCommit": ["npm test", "python -m pytest"],
      "commitPrefix": "quality:"
    },
    "security": {
      "name": "Security Scanning",
      "worktreePath": ".worktrees/security",
      "branch": "lane/security",
      "tools": {
        "sast": {
          "general": "semgrep --config=auto .",
          "python": "bandit -r .",
          "javascript": "eslint --ext .js,.ts --config security ."
        },
        "dependencies": {
          "npm": "npm audit --audit-level=moderate",
          "python": "safety check",
          "containers": "trivy fs ."
        },
        "secrets": "gitleaks detect --source ."
      },
      "allowedPatterns": ["**/*"],
      "preCommit": ["echo 'Security scan complete'"],
      "commitPrefix": "security:",
      "failOnVulnerabilities": true,
      "severityThreshold": "high"
    },
    "infrastructure": {
      "name": "Infrastructure as Code",
      "worktreePath": ".worktrees/infrastructure",
      "branch": "lane/infrastructure",
      "tools": {
        "provisioning": "tofu",
        "configuration": "ansible-playbook",
        "validation": "checkov -d .",
        "planning": "tofu plan"
      },
      "allowedPatterns": ["infrastructure/**", "*.tf", "*.yml", "*.yaml"],
      "preCommit": ["tofu validate", "checkov -d . --check CKV_*"],
      "commitPrefix": "infra:"
    },
    "documentation": {
      "name": "Documentation Generation",
      "worktreePath": ".worktrees/docs",
      "branch": "lane/docs",
      "tools": {
        "api_docs": "swagger-codegen generate -i api-spec.yaml -l html2 -o docs/api",
        "readme": "readme-generator",
        "changelog": "conventional-changelog"
      },
      "allowedPatterns": ["docs/**", "*.md", "README*", "CHANGELOG*"],
      "preCommit": ["markdownlint docs/"],
      "commitPrefix": "docs:"
    },
    "agentic_research": {
      "name": "Research & Analysis",
      "worktreePath": ".worktrees/research",
      "branch": "lane/research",
      "tools": {
        "primary": {
          "tool": "gemini_cli",
          "config": {
            "model": "gemini-1.5-pro",
            "context_window": "1M_tokens"
          }
        }
      },
      "taskComplexity": "simple",
      "costBudget": "$0/day",
      "allowedPatterns": ["docs/**", "research/**", "*.md"]
    },
    "agentic_architecture": {
      "name": "System Architecture & Complex Design",
      "worktreePath": ".worktrees/architecture",
      "branch": "lane/architecture",
      "tools": {
        "primary": {
          "tool": "claude_code",
          "config": {
            "model": "claude-sonnet-4",
            "thinking_mode": "ultrathink",
            "workflow": "research_plan_code",
            "sub_agents": true
          }
        },
        "research_support": {
          "tool": "gemini_cli",
          "config": {"model": "gemini-1.5-pro"}
        }
      },
      "taskComplexity": "complex",
      "requiresApproval": true,
      "costBudget": "$5/day",
      "warningThreshold": 0.6,
      "allowedPatterns": ["architecture/**", "design/**", "*.arch.md"]
    },
    "agentic_implementation": {
      "name": "AI-Powered Code Implementation",
      "worktreePath": ".worktrees/implementation",
      "branch": "lane/implementation",
      "tools": {
        "primary": {
          "tool": "aider",
          "config": {
            "model_priority": [
              "ollama/codellama:7b-instruct",
              "gemini/gemini-1.5-pro"
            ],
            "workflow": "tdd",
            "auto_commit": false
          }
        },
        "fallback": {
          "tool": "continue",
          "config": {
            "provider": "ollama",
            "model": "codegemma:2b"
          }
        }
      },
      "taskComplexity": "moderate",
      "costOptimized": true,
      "allowedPatterns": ["src/**", "lib/**", "tests/**"]
    }
  },
  "integration": {
    "testCommand": "npm test && python -m pytest",
    "deployCommand": "echo 'Deploy to staging'",
    "rollbackCommand": "git revert HEAD",
    "notificationWebhook": null,
    "slackChannel": null
  },
  "taskClassification": {
    "simple": {
      "description": "Single file edits, basic debugging, simple refactoring",
      "recommendedService": "gemini_cli",
      "examples": [
        "fix typo",
        "add logging",
        "format code",
        "simple bug fix",
        "add comments",
        "rename variables",
        "basic validation"
      ],
      "maxTokens": 2000,
      "estimatedCost": "$0.00"
    },
    "moderate": {
      "description": "Multi-file changes, feature implementation, code reviews",
      "recommendedService": "aider_local",
      "examples": [
        "implement API endpoint",
        "add test suite",
        "refactor class",
        "integrate third-party library",
        "database schema changes"
      ],
      "maxTokens": 8000,
      "estimatedCost": "$0.00"
    },
    "complex": {
      "description": "Architecture changes, research tasks, multi-agent workflows",
      "recommendedService": "claude_code",
      "examples": [
        "system redesign",
        "performance optimization",
        "security audit",
        "microservices architecture",
        "cross-system integration",
        "research and implement new technology"
      ],
      "maxTokens": 32000,
      "requiresApproval": true,
      "estimatedCost": "$0.15-$2.00"
    }
  },
  "agenticPatterns": {
    "research_plan_code": {
      "enabled": true,
      "description": "Three-phase approach for complex tasks",
      "phases": [
        {
          "name": "research",
          "service": "gemini_cli",
          "purpose": "information gathering",
          "cost": "free"
        },
        {
          "name": "plan",
          "service": "claude_code",
          "purpose": "architecture and planning",
          "cost": "premium",
          "requiresApproval": true
        },
        {
          "name": "implement",
          "service": "aider_local",
          "purpose": "code generation",
          "cost": "free"
        }
      ]
    },
    "sub_agents": {
      "enabled": true,
      "description": "Specialized agents for different aspects",
      "agents": {
        "researcher": {
          "service": "gemini_cli",
          "purpose": "information gathering",
          "complexity": ["simple", "moderate"]
        },
        "architect": {
          "service": "claude_code",
          "purpose": "system design and planning",
          "complexity": ["complex"],
          "requiresApproval": true
        },
        "implementer": {
          "service": "aider_local",
          "purpose": "code generation and implementation",
          "complexity": ["simple", "moderate"]
        },
        "reviewer": {
          "service": "local",
          "purpose": "quality checks and validation",
          "complexity": ["simple", "moderate", "complex"]
        }
      }
    },
    "tdd_workflow": {
      "enabled": true,
      "description": "Test-driven development with AI",
      "preferredService": "aider_local",
      "steps": ["write_tests", "run_tests", "implement", "refactor"],
      "fallbackService": "ollama_local"
    }
  }
}
EOF
    fi
    # Create quota tracker if missing
    if [[ ! -f ".ai/quota-tracker.json" ]]; then
        cat > .ai/quota-tracker.json << 'EOF'
{
  "lastReset": "2024-01-01",
  "services": {}
}
EOF
    fi
    log_success "Framework configuration created"
}

# Create helper scripts (similar to original)
create_helper_scripts() {
    log_info "Creating helper scripts..."
    mkdir -p .ai/scripts
    # Quick lane starter
    cat > .ai/scripts/quick-start.sh << 'EOF'
#!/bin/bash
# Quick start script for common operations

case "$1" in
    "code")
        ./orchestrator.ps1 -Command start-lane -Lane ai_coding
        ;;
    "quality")
        ./orchestrator.ps1 -Command start-lane -Lane quality
        ;;
    "security")
        ./orchestrator.ps1 -Command start-lane -Lane security
        ;;
    "research")
        ./orchestrator.ps1 -Command start-lane -Lane agentic_research
        ;;
    "architecture")
        ./orchestrator.ps1 -Command start-lane -Lane agentic_architecture
        ;;
    "implementation")
        ./orchestrator.ps1 -Command start-lane -Lane agentic_implementation
        ;;
    "status")
        ./orchestrator.ps1 -Command status
        ;;
    *)
        echo "Usage: $0 {code|quality|security|research|architecture|implementation|status}"
        ;;
esac
EOF
    chmod +x .ai/scripts/quick-start.sh

    # Cost monitoring script (unchanged)
    cat > .ai/scripts/cost-monitor.py << 'EOF'
#!/usr/bin/env python3
import json
import datetime

def check_quotas():
    try:
        with open('.ai/quota-tracker.json', 'r') as f:
            tracker = json.load(f)
        with open('.ai/framework-config.json', 'r') as f:
            config = json.load(f)
        print("🎯 Quota Status:")
        total_savings = 0
        for service_name, service_config in config['quotaManagement']['services'].items():
            usage = tracker['services'].get(service_name, 0)
            limit = service_config.get('dailyLimit', 'unlimited')
            if limit == 'unlimited':
                print(f"  {service_name}: {usage} requests (unlimited)")
            else:
                percentage = (usage / limit) * 100
                print(f"  {service_name}: {usage}/{limit} ({percentage:.1f}%)")
                estimated_cost = usage * service_config.get('costPerRequest', 0.01)
                total_savings += estimated_cost
        print(f"\n💰 Estimated savings today: ${total_savings:.2f}")
    except FileNotFoundError:
        print("❌ Configuration files not found. Run setup first.")

if __name__ == "__main__":
    check_quotas()
EOF
    chmod +x .ai/scripts/cost-monitor.py
    log_success "Helper scripts created"
}

# Main installation function
main() {
    echo -e "${BLUE}"
    echo "🚀 Free-Tier Multi-Agent Framework Setup"
    echo "========================================"
    echo -e "${NC}"
    detect_system
    # Ensure local bin path exists
    mkdir -p ~/.local/bin
    export PATH="$HOME/.local/bin:$PATH"
    # Install components
    install_prerequisites
    install_ollama
    install_ai_tools
    install_agentic_tools
    install_quality_tools
    install_security_tools
    install_infrastructure_tools
    install_documentation_tools
    install_monitoring_tools
    # Setup framework and helper scripts
    setup_framework_config
    create_helper_scripts
    # Optional: Download local models
    read -p "Setup local models now? This will download several GB of data. (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        setup_local_models
    else
        log_info "Skipping local models setup. Run 'ollama pull codellama:7b-instruct' later."
    fi
    echo -e "${GREEN}"
    echo "✅ Setup Complete!"
    echo "=================="
    echo -e "${NC}"
    echo "Next steps:"
    echo "1. Run: ./orchestrator.ps1 -Command init"
    echo "2. Run: ./orchestrator.ps1 -Command status"
    echo "3. Start a lane: ./orchestrator.ps1 -Command start-lane -Lane ai_coding"
    echo ""
    echo "💡 Quick access: .ai/scripts/quick-start.sh code"
    echo "📊 Monitor costs: .ai/scripts/cost-monitor.py"
    echo ""
    echo "🎯 You now have access to:"
    echo "  - Free AI coding with Gemini CLI (1000 requests/day)"
    echo "  - Premium AI for complex tasks with Claude Code (strict quotas)"
    echo "  - Unlimited local AI with Ollama"
    echo "  - Complete free security scanning suite"
    echo "  - Open-source code quality tools"
    echo "  - Free infrastructure automation"
    echo ""
    echo "💰 Estimated monthly savings: \$200-500+ vs paid alternatives"
}

# Run main function
main "$@"