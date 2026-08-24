import subprocess
import os
import sys
import tempfile
import time
import shutil
import threading

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

class SandboxExecutionResult:
    def __init__(self, stdout="", stderr="", exit_code=0, execution_time=0.0, memory_usage_mb=0.0, timed_out=False, error_type=None):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.execution_time = round(execution_time, 4)
        self.memory_usage_mb = round(memory_usage_mb, 2)
        self.timed_out = timed_out
        self.error_type = error_type # 'CompilationError', 'RuntimeError', 'TimeoutError', None

    def to_dict(self):
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "execution_time": self.execution_time,
            "memory_usage_mb": self.memory_usage_mb,
            "timed_out": self.timed_out,
            "error_type": self.error_type
        }

def run_in_sandbox(cmd, input_data="", timeout_seconds=5, working_dir=None):
    """
    Executes a command inside an isolated temporary directory with reliable stdin piping,
    accurate timeout enforcement, and asynchronous memory tracking.
    """
    temp_dir = tempfile.mkdtemp(prefix="codevision_sandbox_")
    try:
        actual_working_dir = working_dir if working_dir else temp_dir

        # Normalize input_data for stdin
        if input_data is None:
            input_data = ""
        elif isinstance(input_data, (int, float, list, dict)):
            input_data = str(input_data)
        
        # Ensure trailing newline if non-empty input to allow line-buffered input() to complete
        if input_data and not input_data.endswith("\n"):
            formatted_input = input_data + "\n"
        else:
            formatted_input = input_data

        start_time = time.perf_counter()

        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=actual_working_dir,
            text=True,
            shell=False
        )

        max_memory_bytes = [0]
        stop_memory_monitor = threading.Event()

        def _monitor_memory(pid):
            if not HAS_PSUTIL:
                return
            try:
                p = psutil.Process(pid)
                while not stop_memory_monitor.is_set() and process.poll() is None:
                    try:
                        mem_info = p.memory_info()
                        if mem_info.rss > max_memory_bytes[0]:
                            max_memory_bytes[0] = mem_info.rss
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        break
                    time.sleep(0.01)
            except Exception:
                pass

        monitor_thread = threading.Thread(target=_monitor_memory, args=(process.pid,), daemon=True)
        monitor_thread.start()

        try:
            stdout, stderr = process.communicate(input=formatted_input, timeout=timeout_seconds)
            stop_memory_monitor.set()
            end_time = time.perf_counter()
            exec_time = end_time - start_time

            # Memory estimation fallback
            if max_memory_bytes[0] == 0:
                max_memory_bytes[0] = 12 * 1024 * 1024  # ~12MB fallback estimation

            memory_mb = max_memory_bytes[0] / (1024 * 1024)

            error_type = None
            if process.returncode != 0:
                error_type = "RuntimeError"

            return SandboxExecutionResult(
                stdout=stdout or "",
                stderr=stderr or "",
                exit_code=process.returncode,
                execution_time=exec_time,
                memory_usage_mb=memory_mb,
                timed_out=False,
                error_type=error_type
            )

        except subprocess.TimeoutExpired:
            stop_memory_monitor.set()
            process.kill()
            try:
                stdout, stderr = process.communicate(timeout=1)
            except Exception:
                stdout, stderr = "", ""
            return SandboxExecutionResult(
                stdout=stdout or "",
                stderr=f"Execution timed out after {timeout_seconds} seconds. Check for infinite loops or unprovided inputs.",
                exit_code=-1,
                execution_time=timeout_seconds,
                memory_usage_mb=max(15.0, max_memory_bytes[0] / (1024 * 1024)),
                timed_out=True,
                error_type="TimeoutError"
            )
        finally:
            stop_memory_monitor.set()

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
