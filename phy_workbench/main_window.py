from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from PySide6.QtCore import QSettings, QTimer, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from .diagram import DiagramScene, DiagramView
from .matlab_bridge import MatlabWorker
from .model import IMPLEMENTED_NODES, LEVEL0_GRAPH, NODE_THEORY_NOTES
from .style import APP_STYLE


class MainWindow(QMainWindow):
    # Các tín hiệu giao tiếp với luồng chạy MATLAB
    initialize_matlab = Signal()
    run_requested = Signal(str, str)
    native_figure_requested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MATLAB PHY Workbench · Level 0")
        self.resize(1560, 940)
        self.setMinimumSize(1100, 720)
        self.setStyleSheet(APP_STYLE)
        self.setStatusBar(None)  # Bỏ hoàn toàn thanh status bar

        # Thư mục tạm lưu cấu hình và kết quả mô phỏng
        self.runtime_dir = Path(tempfile.mkdtemp(prefix="matlab_phy_workbench_"))
        self.current_node = ""
        self.has_run = False
        self.settings = QSettings("Adaptive PHY Lab", "MATLAB PHY Workbench")

        # Lưu tiêu đề và công thức của từng khối
        self.formulas = {
            child.node_id: (child.title, child.formula)
            for group in LEVEL0_GRAPH for child in group.children
        }

        # 1. Bố cục giao diện
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(18, 14, 18, 10)
        root_layout.setSpacing(12)

        # Thanh tiêu đề phía trên
        root_layout.addLayout(self._create_header())

        # Chia 2 phần: Bảng cấu hình (Trái) và Sơ đồ khối (Phải)
        self.splitter = QSplitter()
        self.splitter.setChildrenCollapsible(False)
        self.control_panel = self._create_control_panel()
        self.workspace_panel = self._create_workspace()
        self.splitter.addWidget(self.control_panel)
        self.splitter.addWidget(self.workspace_panel)
        self.splitter.setSizes([270, 1260])
        root_layout.addWidget(self.splitter, 1)

        # 2. Khởi tạo luồng MATLAB chạy nền
        matlab_dir = Path(__file__).resolve().parent.parent / "matlab"
        self.worker_thread = QThread(self)
        self.worker = MatlabWorker(matlab_dir, self.runtime_dir)
        self.worker.moveToThread(self.worker_thread)

        self.initialize_matlab.connect(self.worker.initialize)
        self.run_requested.connect(self.worker.run_level0)
        self.native_figure_requested.connect(self.worker.open_native_figure)

        self.worker.ready.connect(self._on_matlab_ready)
        self.worker.run_complete.connect(self._on_run_complete)
        self.worker.failed.connect(self._on_matlab_failed)

        self.worker_thread.start()
        self.initialize_matlab.emit()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self.view.fit_graph)

    def _create_header(self):
        """Thanh tiêu đề kèm nút ẩn/hiện bảng cấu hình."""
        header_layout = QHBoxLayout()
        title_label = QLabel("PHY Workbench")
        title_label.setObjectName("title")
        header_layout.addWidget(title_label)

        self.toggle_panel_button = QPushButton("⚙ Cấu hình")
        self.toggle_panel_button.clicked.connect(self.toggle_control_panel)
        header_layout.addWidget(self.toggle_panel_button)
        header_layout.addStretch()
        return header_layout

    def _create_control_panel(self):
        """Bảng điều khiển các thông số mô phỏng viễn thông."""
        panel = QFrame()
        panel.setObjectName("panel")
        panel.setMinimumWidth(250)
        panel.setMaximumWidth(320)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)

        section_title = QLabel("Cấu hình mô phỏng")
        section_title.setObjectName("section")
        layout.addWidget(section_title)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)

        # 1. Nguồn phát: Random bits hoặc Văn bản UTF-8
        self.source_mode = QComboBox()
        self.source_mode.addItems(["Random bits", "Text (UTF-8)"])
        self.source_mode.currentTextChanged.connect(self._on_source_mode_changed)

        self.text_input = QLineEdit("Hello PHY")
        self.text_input.setEnabled(False)

        # 2. Số lượng bit mô phỏng
        self.num_bits = QSpinBox()
        self.num_bits.setRange(100, 2_000_000)
        self.num_bits.setValue(20_000)
        self.num_bits.setSingleStep(10_000)

        # 3. Chuẩn điều chế: BPSK, QPSK, 16-QAM
        self.modulation = QComboBox()
        self.modulation.addItems(["BPSK", "QPSK", "16-QAM"])
        self.modulation.setCurrentText("QPSK")

        # 4. Tỉ số Eb/N0 trên kênh truyền AWGN (dB)
        self.ebno = QDoubleSpinBox()
        self.ebno.setRange(-10, 30)
        self.ebno.setValue(8.0)
        self.ebno.setSingleStep(0.5)
        self.ebno.setSuffix(" dB")

        # 5. Hạt giống ngẫu nhiên (Random Seed)
        self.seed = QSpinBox()
        self.seed.setRange(0, 2_147_483_647)
        self.seed.setValue(42)

        form_layout.addRow("Nguồn dữ liệu", self.source_mode)
        form_layout.addRow("Chuỗi ký tự", self.text_input)
        form_layout.addRow("Số bit phát", self.num_bits)
        form_layout.addRow("Điều chế", self.modulation)
        form_layout.addRow("Eb/N0", self.ebno)
        form_layout.addRow("Seed", self.seed)
        layout.addLayout(form_layout)

        # Nút bấm chạy mô phỏng
        self.run_button = QPushButton("Chạy trong MATLAB")
        self.run_button.setObjectName("primary")
        self.run_button.setEnabled(False)
        self.run_button.clicked.connect(self.run_simulation)
        layout.addWidget(self.run_button)

        guide_label = QLabel("Cuộn chuột: Phóng to / Thu nhỏ\nKéo chuột: Di chuyển sơ đồ\nClick khối: Mở / Đóng chi tiết")
        guide_label.setObjectName("muted")
        layout.addWidget(guide_label)
        layout.addStretch()
        return panel

    def _create_workspace(self):
        """Khu vực sơ đồ Diagram và bảng chi tiết công thức, ghi chú."""
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Khung vẽ sơ đồ khối
        self.scene = DiagramScene()
        self.scene.node_selected.connect(self.inspect_node)
        self.view = DiagramView(self.scene)
        layout.addWidget(self.view, 1)

        # Bảng thông tin chi tiết khối bên dưới
        info_panel = QFrame()
        info_panel.setObjectName("panel")
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(12, 9, 12, 9)
        info_layout.setSpacing(8)

        # Hàng hiển thị tên khối, công thức và các nút hành động
        top_row = QHBoxLayout()
        self.inspect_title = QLabel("Chọn một khối tính toán để xem chi tiết")
        self.inspect_title.setObjectName("section")

        self.formula_label = QLabel("Công thức toán học sẽ hiển thị tại đây.")
        self.formula_label.setObjectName("formula")

        self.plot_button = QPushButton("Vẽ đồ thị trong MATLAB")
        self.plot_button.setEnabled(False)
        self.plot_button.clicked.connect(self.plot_current_node)

        # Nút bấm thu gọn/mở rộng ô ghi chú
        self.toggle_notes_button = QPushButton("▼ Ghi chú & Hệ quy chiếu")
        self.toggle_notes_button.clicked.connect(self.toggle_notes_panel)

        top_row.addWidget(self.inspect_title)
        top_row.addWidget(self.formula_label, 1)
        top_row.addWidget(self.plot_button)
        top_row.addWidget(self.toggle_notes_button)
        info_layout.addLayout(top_row)

        # Khung nhập ghi chú & hệ quy chiếu
        self.note_container = QWidget()
        note_row = QHBoxLayout(self.note_container)
        note_row.setContentsMargins(0, 0, 0, 0)

        note_tag = QLabel("HỆ QUY CHIẾU\n& GHI CHÚ")
        note_tag.setObjectName("metricKey")

        self.note_editor = QPlainTextEdit()
        self.note_editor.setPlaceholderText("Hệ quy chiếu lý thuyết và ghi chú phục vụ phản biện, debug…")
        self.note_editor.setMinimumHeight(96)
        self.note_editor.setMaximumHeight(130)
        self.note_editor.setEnabled(False)

        self.save_note_button = QPushButton("Lưu ghi chú")
        self.save_note_button.setEnabled(False)
        self.save_note_button.clicked.connect(self.save_current_note)

        note_row.addWidget(note_tag)
        note_row.addWidget(self.note_editor, 1)
        note_row.addWidget(self.save_note_button)
        info_layout.addWidget(self.note_container)

        layout.addWidget(info_panel)
        return workspace

    def toggle_control_panel(self):
        """Thu gọn hoặc mở lại bảng cấu hình."""
        is_visible = self.control_panel.isVisible()
        self.control_panel.setVisible(not is_visible)
        self.toggle_panel_button.setText("⚙ Ẩn cấu hình" if not is_visible else "⚙ Cấu hình")
        QTimer.singleShot(10, self.view.fit_graph)

    def toggle_notes_panel(self):
        """Thu gọn hoặc mở rộng ô nhập ghi chú."""
        is_visible = self.note_container.isVisible()
        self.note_container.setVisible(not is_visible)
        self.toggle_notes_button.setText("▲ Ghi chú" if is_visible else "▼ Ghi chú & Hệ quy chiếu")

    def _on_source_mode_changed(self, mode: str):
        """Bật/tắt ô nhập văn bản khi đổi chế độ nguồn phát."""
        is_text = (mode == "Text (UTF-8)")
        self.text_input.setEnabled(is_text)
        self.num_bits.setEnabled(not is_text)

    def get_simulation_config(self) -> dict:
        """Lấy toàn bộ thông số mô phỏng hiện tại."""
        return {
            "sourceMode": self.source_mode.currentText(),
            "text": self.text_input.text(),
            "numBits": self.num_bits.value(),
            "modulation": self.modulation.currentText(),
            "ebnoDb": self.ebno.value(),
            "seed": self.seed.value(),
        }

    @Slot(dict)
    def _on_matlab_ready(self, environment: dict):
        """Khi MATLAB khởi động thành công."""
        self.run_button.setEnabled(True)
        self.run_simulation()

    def run_simulation(self):
        """Thực thi mô phỏng trong MATLAB."""
        config = self.get_simulation_config()

        # Lưu file config.json cho script MATLAB đọc
        config_path = self.runtime_dir / "config.json"
        config_path.write_text(json.dumps(config, ensure_ascii=False), encoding="utf-8")

        # Tự động ẩn bảng cấu hình để mở rộng Diagram
        if self.control_panel.isVisible():
            self.control_panel.hide()
            self.toggle_panel_button.setText("⚙ Cấu hình")

        # Cập nhật thông số lên các khối trên sơ đồ
        self.scene.update_config(config)

        self.current_node = ""
        self.has_run = False
        self.plot_button.setEnabled(False)
        self.run_button.setEnabled(False)
        self.run_button.setText("MATLAB đang tính toán…")

        # Gửi tín hiệu chạy mô phỏng
        self.run_requested.emit(str(config_path), str(self.runtime_dir))
        QTimer.singleShot(20, self.view.fit_graph)

    @Slot(dict)
    def _on_run_complete(self, summary: dict):
        """Khi MATLAB hoàn thành mô phỏng và trả về kết quả."""
        self.has_run = True
        ber_value = summary["ber"]
        bit_errors = summary["bitErrors"]

        # Cập nhật kết quả tỉ lệ lỗi bit lên khối Metrics
        ber_text = f"BER: {ber_value:.2e} ({bit_errors} lỗi)"
        self.scene.update_config(self.get_simulation_config(), ber_text)

        self.plot_button.setEnabled(self.current_node in IMPLEMENTED_NODES)
        self.run_button.setEnabled(True)
        self.run_button.setText("Chạy trong MATLAB")

    @Slot(str)
    def inspect_node(self, node_id: str):
        """Xem công thức và hệ quy chiếu lý thuyết/ghi chú của khối được chọn."""
        self.current_node = node_id
        title, formula = self.formulas[node_id]

        # Chỉ hiển thị duy nhất tên của khối nhỏ
        self.inspect_title.setText(title)
        self.formula_label.setText(formula)

        # Đọc ghi chú lý thuyết & hệ quy chiếu chuẩn của khối
        default_theory_note = NODE_THEORY_NOTES.get(
            node_id,
            f"[HỆ QUY CHIẾU LÝ THUYẾT & CHỈ DẪN DEBUG]\n• Khối: {title}\n• Công thức: {formula}"
        )
        saved_note = self.settings.value(f"notes/{node_id}", default_theory_note, type=str)
        self.note_editor.setPlainText(saved_note)
        self.note_editor.setEnabled(True)
        self.save_note_button.setEnabled(True)
        self.plot_button.setEnabled(self.has_run and node_id in IMPLEMENTED_NODES)

    def save_current_note(self):
        """Lưu ghi chú của người dùng vào bộ nhớ."""
        if not self.current_node:
            return
        note_content = self.note_editor.toPlainText()
        self.settings.setValue(f"notes/{self.current_node}", note_content)
        self.settings.sync()

    def plot_current_node(self):
        """Mở cửa sổ đồ thị MATLAB trực tiếp cho khối đang chọn."""
        if not self.current_node or not self.has_run or self.current_node not in IMPLEMENTED_NODES:
            return
        self.native_figure_requested.emit(self.current_node)

    @Slot(str)
    def _on_matlab_failed(self, error_message: str):
        """Báo lỗi khi MATLAB gặp sự cố."""
        self.run_button.setEnabled(True)
        self.run_button.setText("Chạy trong MATLAB")
        QMessageBox.critical(self, "Lỗi MATLAB", error_message)

    def closeEvent(self, event):
        """Đóng ứng dụng."""
        event.accept()
        os._exit(0)
