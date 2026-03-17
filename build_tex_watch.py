import argparse
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Set


WATCH_EXTS: Set[str] = {
    ".tex", ".sty", ".cls", ".bib",
    ".png", ".jpg", ".jpeg", ".pdf", ".eps",
    ".bst", ".bbx", ".cbx"
}

DEFAULT_EXCLUDE_DIRS: Set[str] = {
    ".git", ".idea", ".vscode", "__pycache__",
    "out", "auxil", "build", ".venv", "venv"
}


def log(msg: str) -> None:
    now = time.strftime("%H:%M:%S")
    print(f"[{now}] {msg}")


def is_under(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def resolve_output_dir(base_dir: Path, value: str) -> Path:
    p = Path(value).expanduser()
    if p.is_absolute():
        return p.resolve()
    return (base_dir / p).resolve()


def build_engine_command(
    engine: str,
    tex_file: Path,
    out_dir: Path,
    aux_dir: Path,
) -> List[str]:
    engine = engine.lower()
    if engine not in {"xelatex", "pdflatex", "lualatex"}:
        raise ValueError(f"不支持的引擎：{engine}")

    return [
        engine,
        "-file-line-error",
        "-interaction=nonstopmode",
        "-synctex=1",
        f"-output-directory={out_dir}",
        f"-aux-directory={aux_dir}",
        tex_file.name,
    ]


def summarize_compiler_output(output: str, max_lines: int = 15) -> str:
    lines = [line.rstrip() for line in output.splitlines()]
    if not lines:
        return ""

    patterns = [
        re.compile(r"^\s*!"),
        re.compile(r".+:\d+:.+"),
        re.compile(r"\b(error|warning)\b", re.IGNORECASE),
        re.compile(r"Undefined control sequence", re.IGNORECASE),
        re.compile(r"Emergency stop", re.IGNORECASE),
        re.compile(r"Runaway argument", re.IGNORECASE),
        re.compile(r"Missing .* inserted", re.IGNORECASE),
    ]

    selected: List[str] = []
    seen: Set[str] = set()
    for line in lines:
        text = line.strip()
        if not text:
            continue
        if any(pattern.search(text) for pattern in patterns):
            if text not in seen:
                selected.append(text)
                seen.add(text)
        if len(selected) >= max_lines:
            break

    if selected:
        return "\n".join(selected)

    tail = [line.strip() for line in lines if line.strip()]
    return "\n".join(tail[-max_lines:])


def run_cmd(
    cmd: List[str],
    cwd: Path,
    quiet: bool = False,
    log_file: Optional[Path] = None,
) -> None:
    if quiet:
        result = subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace"
        )

        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.write_text(result.stdout, encoding="utf-8", errors="replace")

        if result.returncode != 0:
            summary = summarize_compiler_output(result.stdout)
            if summary:
                print(summary)
            if log_file is not None:
                print(f"[ERROR] 完整日志: {log_file}")
            raise subprocess.CalledProcessError(result.returncode, cmd)
    else:
        result = subprocess.run(cmd, cwd=str(cwd))
        if result.returncode != 0:
            raise subprocess.CalledProcessError(result.returncode, cmd)


def reset_log_files(aux_dir: Path, stem: str) -> None:
    for path in (aux_dir / f"{stem}.log", aux_dir / f"{stem}_build.log"):
        try:
            if path.exists():
                path.unlink()
        except OSError:
            pass


def compile_tex(
    tex_file: Path,
    engine: str,
    out_dir: Path,
    aux_dir: Path,
    passes: int = 2,
    quiet: bool = False,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    aux_dir.mkdir(parents=True, exist_ok=True)

    cmd = build_engine_command(engine, tex_file, out_dir, aux_dir)
    log_file = aux_dir / f"{tex_file.stem}_build.log"
    reset_log_files(aux_dir, tex_file.stem)

    total_passes = max(1, passes)
    for i in range(1, total_passes + 1):
        if not quiet:
            log(f"开始编译，第 {i}/{total_passes} 次")
        run_cmd(
            cmd,
            cwd=tex_file.parent,
            quiet=quiet,
            log_file=log_file
        )

    return out_dir / f"{tex_file.stem}.pdf"


def should_skip_dir(dirname: str, extra_excludes: Set[str]) -> bool:
    return dirname in DEFAULT_EXCLUDE_DIRS or dirname in extra_excludes


def collect_watch_files(
    project_dir: Path,
    out_dir: Path,
    aux_dir: Path,
    extra_excludes: Set[str],
) -> Dict[Path, float]:
    files: Dict[Path, float] = {}

    for root, dirs, filenames in os.walk(project_dir):
        root_path = Path(root)

        dirs[:] = [
            d for d in dirs
            if not should_skip_dir(d, extra_excludes)
            and not is_under(root_path / d, out_dir)
            and not is_under(root_path / d, aux_dir)
        ]

        for name in filenames:
            p = root_path / name
            if p.suffix.lower() not in WATCH_EXTS:
                continue
            try:
                files[p.resolve()] = p.stat().st_mtime
            except (FileNotFoundError, PermissionError, OSError):
                pass

    return files


def detect_changes(old_snapshot: Dict[Path, float], new_snapshot: Dict[Path, float]) -> List[Path]:
    changed: List[Path] = []
    old_keys = set(old_snapshot.keys())
    new_keys = set(new_snapshot.keys())

    for p in (old_keys ^ new_keys):
        changed.append(p)

    for p in (old_keys & new_keys):
        if old_snapshot[p] != new_snapshot[p]:
            changed.append(p)

    return sorted(changed, key=lambda x: str(x))


def clean_aux_files(aux_dir: Path, out_dir: Path, stem: str) -> None:
    exts_aux = [
        ".aux", ".log", ".out", ".toc", ".lof", ".lot",
        ".fls", ".fdb_latexmk", ".xdv", ".bcf", ".run.xml",
        ".bbl", ".blg", ".nav", ".snm", ".vrb"
    ]
    exts_out = [".synctex.gz"]

    removed = 0

    for ext in exts_aux:
        p = aux_dir / f"{stem}{ext}"
        if p.exists():
            try:
                p.unlink()
                removed += 1
            except Exception:
                pass

    for ext in exts_out:
        p = out_dir / f"{stem}{ext}"
        if p.exists():
            try:
                p.unlink()
                removed += 1
            except Exception:
                pass

    log(f"清理完成，删除 {removed} 个文件")


def watch_loop(
    tex_file: Path,
    engine: str,
    out_dir: Path,
    aux_dir: Path,
    passes: int,
    interval: float,
    debounce: float,
    cooldown: float,
    quiet: bool,
    extra_excludes: Set[str],
) -> None:
    project_dir = tex_file.parent.resolve()
    pdf_path = (out_dir / f"{tex_file.stem}.pdf").resolve()
    build_log_path = (aux_dir / f"{tex_file.stem}_build.log").resolve()

    if quiet:
        log(f"监听已启动: {tex_file.name} -> {pdf_path}")
        log(f"完整编译日志: {build_log_path}")
    else:
        log("启动监听模式")
        log(f"主文件: {tex_file}")
        log(f"监听目录: {project_dir}")
        log(f"输出目录: {out_dir}")
        log(f"辅助目录: {aux_dir}")
        log(f"输出 PDF: {pdf_path}")
    log("按 Ctrl+C 停止")

    try:
        pdf = compile_tex(tex_file, engine, out_dir, aux_dir, passes=passes, quiet=quiet)
        if pdf.exists():
            log(f"初次编译成功: {pdf}")
        else:
            log(f"编译结束，但未找到 PDF: {pdf}")
    except Exception as e:
        log(f"初次编译失败: {e}")

    snapshot = collect_watch_files(project_dir, out_dir, aux_dir, extra_excludes)

    pending_since: Optional[float] = None
    last_change_time: Optional[float] = None
    pending_changes: List[Path] = []
    last_compile_end = 0.0

    while True:
        try:
            time.sleep(interval)
            new_snapshot = collect_watch_files(project_dir, out_dir, aux_dir, extra_excludes)
            changes = detect_changes(snapshot, new_snapshot)
            now = time.time()

            if changes:
                snapshot = new_snapshot
                pending_changes = changes
                if pending_since is None:
                    pending_since = now
                last_change_time = now

            if pending_since is None or last_change_time is None:
                continue

            if now - last_compile_end < cooldown:
                continue

            if now - last_change_time < debounce:
                continue

            if not quiet:
                shown = pending_changes[:5]
                short_names = ", ".join(p.name for p in shown)
                if len(pending_changes) > 5:
                    short_names += f" ... 共 {len(pending_changes)} 个"
                log(f"检测到变化: {short_names}")

            try:
                pdf = compile_tex(tex_file, engine, out_dir, aux_dir, passes=passes, quiet=quiet)
                last_compile_end = time.time()
                if pdf.exists():
                    log(f"编译成功: {pdf.name}")
                else:
                    log("编译结束，但未找到 PDF")
            except subprocess.CalledProcessError as e:
                last_compile_end = time.time()
                log(f"LaTeX 编译失败，退出码: {e.returncode}")
            except Exception as e:
                last_compile_end = time.time()
                log(f"编译异常: {e}")

            pending_since = None
            last_change_time = None
            pending_changes = []

        except KeyboardInterrupt:
            log("已停止监听")
            break


def main() -> None:
    parser = argparse.ArgumentParser(
        description="更省资源、适合长期后台运行的 LaTeX 自动监听编译脚本"
    )
    parser.add_argument("tex", help="主 tex 文件路径，例如 D:\\paper\\main.tex")
    parser.add_argument(
        "--engine",
        choices=["xelatex", "pdflatex", "lualatex"],
        default="xelatex",
        help="编译引擎（默认 xelatex）"
    )
    parser.add_argument(
        "--outdir",
        default="out",
        help="PDF 输出目录；相对路径默认相对于 tex 所在目录"
    )
    parser.add_argument(
        "--auxdir",
        default="auxil",
        help="辅助文件目录；相对路径默认相对于 tex 所在目录"
    )
    parser.add_argument("--passes", type=int, default=2, help="每次编译次数，默认 2")
    parser.add_argument("--interval", type=float, default=1.0, help="轮询间隔秒数，默认 1.0")
    parser.add_argument("--debounce", type=float, default=1.2, help="变化防抖秒数，默认 1.2")
    parser.add_argument("--cooldown", type=float, default=1.5, help="编译后冷却秒数，默认 1.5")
    parser.add_argument("--once", action="store_true", help="只编译一次，不进入监听")
    parser.add_argument("--clean", action="store_true", help="只清理辅助文件，不编译")
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument("--quiet", dest="quiet", action="store_true", help="精简终端输出（默认开启）")
    verbosity_group.add_argument("--verbose", dest="quiet", action="store_false", help="显示完整编译日志")
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="额外排除目录名，可重复传入，例如 --exclude-dir figures_cache"
    )
    parser.set_defaults(quiet=True)

    args = parser.parse_args()

    tex_file = Path(args.tex).expanduser().resolve()
    if not tex_file.exists():
        print(f"[ERROR] 找不到 tex 文件: {tex_file}")
        sys.exit(1)
    if tex_file.suffix.lower() != ".tex":
        print(f"[ERROR] 不是 .tex 文件: {tex_file}")
        sys.exit(1)

    workdir = tex_file.parent.resolve()
    out_dir = resolve_output_dir(workdir, args.outdir)
    aux_dir = resolve_output_dir(workdir, args.auxdir)
    extra_excludes = set(args.exclude_dir or [])

    try:
        if args.clean:
            clean_aux_files(aux_dir, out_dir, tex_file.stem)
            return

        if args.once:
            pdf = compile_tex(
                tex_file=tex_file,
                engine=args.engine,
                out_dir=out_dir,
                aux_dir=aux_dir,
                passes=max(1, args.passes),
                quiet=args.quiet,
            )
            if pdf.exists():
                log(f"编译成功: {pdf}")
            else:
                log(f"编译结束，但未找到 PDF: {pdf}")
                sys.exit(2)
        else:
            watch_loop(
                tex_file=tex_file,
                engine=args.engine,
                out_dir=out_dir,
                aux_dir=aux_dir,
                passes=max(1, args.passes),
                interval=max(0.3, args.interval),
                debounce=max(0.2, args.debounce),
                cooldown=max(0.0, args.cooldown),
                quiet=args.quiet,
                extra_excludes=extra_excludes,
            )

    except FileNotFoundError as e:
        print(f"[ERROR] 命令不存在: {e}")
        print("[提示] 请确认 MiKTeX 已安装且 xelatex/pdflatex/lualatex 已加入 PATH。")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] LaTeX 编译失败，退出码: {e.returncode}")
        sys.exit(e.returncode)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
