# 论文构建。latexmk 优先（自动处理多遍与 biber），未安装则回退手动链。
# 用法： make | make clean
MAIN := main

all: build

build:
	@if command -v latexmk >/dev/null 2>&1; then \
		echo "[latexmk] building $(MAIN).tex"; \
		latexmk -xelatex -interaction=nonstopmode -halt-on-error $(MAIN).tex; \
	else \
		echo "[manual] building $(MAIN).tex (latexmk not installed; 推荐: sudo pacman -S latexmk)"; \
		xelatex -interaction=nonstopmode -halt-on-error $(MAIN).tex; \
		biber $(MAIN) || true; \
		xelatex -interaction=nonstopmode -halt-on-error $(MAIN).tex; \
		xelatex -interaction=nonstopmode -halt-on-error $(MAIN).tex; \
	fi

clean:
	rm -f $(MAIN).aux $(MAIN).bbl $(MAIN).bcf $(MAIN).blg $(MAIN).log \
	      $(MAIN).out $(MAIN).toc $(MAIN).run.xml $(MAIN).synctex.gz \
	      $(MAIN).fdb_latexmk $(MAIN).fls

.PHONY: all build clean
