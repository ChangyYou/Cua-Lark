.PHONY: install dev test lint clean run help

# 安装依赖
install:
	pip install -r requirements.txt

# 安装开发依赖
dev:
	pip install -r requirements.txt
	pip install pytest black flake8 mypy

# 安装为 CLI 工具
install-cli:
	pip install -e .

# 运行测试
test:
	pytest tests/ -v

# 代码格式化
lint:
	black src/ tests/
	flake8 src/ tests/

# 类型检查
typecheck:
	mypy src/

# 清理缓存
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true

# 运行程序（使用 CLI）
run:
	cua-lark "帮我给游畅发送你好"

# 交互模式
interactive:
	cua-lark --interactive

# 帮助
help:
	@echo "CUA-Lark Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install       - Install dependencies"
	@echo "  install-cli   - Install as CLI tool (cua-lark command)"
	@echo "  dev           - Install development dependencies"
	@echo "  test          - Run tests"
	@echo "  lint          - Format code and run linter"
	@echo "  typecheck     - Run type checker"
	@echo "  clean         - Clean cache files"
	@echo "  run           - Run the application"
	@echo "  interactive   - Run in interactive mode"
	@echo ""
	@echo "Usage:"
	@echo "  cua-lark 帮我给游畅发送你好"
	@echo "  cua-lark 给王经理发消息说后端联调已经跑通了"
