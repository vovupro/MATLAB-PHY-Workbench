from __future__ import annotations

import json
from pathlib import Path

import pythoncom
import win32com.client
from PySide6.QtCore import QObject, Signal, Slot


def _matlab_quote(value: str | Path) -> str:
    return str(value).replace("'", "''")


class MatlabWorker(QObject):
    """Tiến trình nền kết nối và thực thi các phép tính trong MATLAB."""
    ready = Signal(dict)
    run_complete = Signal(dict)
    native_figure_opened = Signal(str)
    failed = Signal(str)

    def __init__(self, matlab_dir: Path, runtime_dir: Path):
        super().__init__()
        self.matlab_dir = matlab_dir
        self.runtime_dir = runtime_dir
        self.matlab = None
        self.current_trace: Path | None = None

    @Slot()
    def initialize(self):
        """Khởi động và kết nối tới MATLAB Desktop."""
        try:
            pythoncom.CoInitialize()
            self.matlab = win32com.client.Dispatch("Matlab.Desktop.Application")
            self.matlab.Visible = 1
            self.matlab.Execute(f"addpath('{_matlab_quote(self.matlab_dir)}')")
            
            environment_file = self.runtime_dir / "environment.json"
            self.matlab.Execute(f"phy_check_environment('{_matlab_quote(environment_file)}')")
            environment = json.loads(environment_file.read_text(encoding="utf-8"))
            self.ready.emit(environment)
        except Exception as exc:
            self.failed.emit(f"Không thể khởi động MATLAB: {exc}")

    @Slot(str, str)
    def run_level0(self, config_path: str, output_dir: str):
        """Thực thi chuỗi xử lý tín hiệu tầng vật lý Level 0 trong MATLAB."""
        try:
            if self.matlab is None:
                raise RuntimeError("MATLAB chưa sẵn sàng.")
            
            command = f"phy_level0_run('{_matlab_quote(config_path)}','{_matlab_quote(output_dir)}')"
            transcript = self.matlab.Execute(command)
            
            summary_path = Path(output_dir) / "summary.json"
            if not summary_path.exists():
                raise RuntimeError(transcript or "MATLAB không tạo được file kết quả summary.json.")
            
            self.current_trace = Path(output_dir) / "trace.mat"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.run_complete.emit(summary)
        except Exception as exc:
            self.failed.emit(f"Mô phỏng MATLAB thất bại: {exc}")

    @Slot(str)
    def open_native_figure(self, node_id: str):
        """Mở cửa sổ đồ thị trực tiếp của MATLAB cho khối được chọn."""
        try:
            if self.matlab is None or self.current_trace is None:
                raise RuntimeError("Vui lòng chạy mô phỏng trước khi xem đồ thị.")
            
            self.matlab.Visible = 1
            self.matlab.Execute(
                f"phy_render_trace('{_matlab_quote(self.current_trace)}','{_matlab_quote(node_id)}','',true)"
            )
            self.native_figure_opened.emit(node_id)
        except Exception as exc:
            self.failed.emit(f"Không thể mở đồ thị MATLAB: {exc}")

    @Slot()
    def shutdown(self):
        """Giải phóng kết nối COM khi tắt ứng dụng."""
        try:
            self.matlab = None
        except Exception:
            pass
        finally:
            pythoncom.CoUninitialize()
