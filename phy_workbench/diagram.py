from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF, QWheelEvent
from PySide6.QtWidgets import (
    QGraphicsObject,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsView,
)

from .model import LEVEL0_GRAPH, ChildNode, GroupNode


class ChildItem(QGraphicsObject):
    """Khối con thể hiện một bước xử lý tín hiệu cụ thể trong hệ thống."""
    selected = Signal(str)

    def __init__(self, model: ChildNode, color: str, parent=None):
        super().__init__(parent)
        self.model = model
        self.subtitle = model.subtitle
        self.formula = model.formula
        self.hovered = False
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def boundingRect(self):
        return QRectF(0, 0, 208, 72)

    def paint(self, painter: QPainter, option, widget=None):
        rect = self.boundingRect()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Màu nền khối (đổi màu nhẹ khi rê chuột qua)
        if self.hovered:
            painter.setBrush(QColor("#dbeaf5"))
            painter.setPen(QPen(QColor("#356f9b"), 1.5))
        else:
            painter.setBrush(QColor("#ffffff"))
            painter.setPen(QPen(QColor("#2b2b2b"), 1.5))
        painter.drawRect(rect)

        # Tiêu đề khối
        painter.setPen(QColor("#222222"))
        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.drawText(QRectF(12, 10, 184, 18), self.model.title)

        # Dòng thông số / mô tả (in đậm màu xanh nếu có thông số cấu hình)
        if self.subtitle != self.model.subtitle:
            painter.setPen(QColor("#005fb8"))
            painter.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        else:
            painter.setPen(QColor("#555555"))
            painter.setFont(QFont("Arial", 8))
        painter.drawText(QRectF(12, 32, 184, 15), self.subtitle)

        # Công thức toán học
        painter.setPen(QColor("#333333"))
        painter.setFont(QFont("Consolas", 7))
        painter.drawText(QRectF(12, 51, 184, 13), self.formula)

    def hoverEnterEvent(self, event):
        self.hovered = True
        self.update()

    def hoverLeaveEvent(self, event):
        self.hovered = False
        self.update()

    def mousePressEvent(self, event):
        self.selected.emit(self.model.node_id)
        event.accept()


class GroupItem(QGraphicsObject):
    """Khối lớn đại diện cho một tầng chức năng (Nguồn, Phát, Kênh truyền, Thu,...)."""
    geometry_changed = Signal()
    child_selected = Signal(str)

    def __init__(self, model: GroupNode):
        super().__init__()
        self.model = model
        self.expanded = False
        self.children: list[ChildItem] = []

        for child_model in model.children:
            child = ChildItem(child_model, model.color, self)
            child.selected.connect(self.child_selected)
            child.setVisible(False)
            self.children.append(child)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    @property
    def width(self):
        return 236.0

    @property
    def height(self):
        if self.expanded:
            return 76.0 + 86.0 * len(self.children)
        return 76.0

    def boundingRect(self):
        return QRectF(0, 0, self.width, self.height)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.boundingRect()

        # Vẽ khung hộp của nhóm
        painter.setBrush(QColor("#f7f7f7"))
        painter.setPen(QPen(QColor("#252525"), 2))
        painter.drawRect(rect)
        painter.fillRect(QRectF(0, 0, 5, rect.height()), QColor("#6b6b6b"))

        # Tên nhóm chức năng
        painter.setPen(QColor("#151515"))
        painter.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        painter.drawText(QRectF(18, 22, 170, 28), Qt.AlignmentFlag.AlignVCenter, self.model.title)

        # Nút tròn mở rộng (+) hoặc thu gọn (−)
        circle_rect = QRectF(194, 20, 26, 26)
        painter.setBrush(QColor("#e2e2e2"))
        painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawRect(circle_rect)
        painter.setPen(QColor("#111111"))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        symbol = "−" if self.expanded else "+"
        painter.drawText(circle_rect, Qt.AlignmentFlag.AlignCenter, symbol)

        # Vẽ liên kết giữa các khối con khi mở rộng nhóm
        if self.expanded and len(self.children) > 1:
            center_x = self.width / 2

            for i in range(len(self.children) - 1):
                first_bottom = 68 + i * 86 + 72
                next_top = 68 + (i + 1) * 86
                mid_y = (first_bottom + next_top) / 2

                if self.model.group_id == "channel":
                    # Khối Channel: Các tác động kênh truyền (nhiễu AWGN, fading, suy hao)
                    # mang tính chất cộng/chồng chập (+), vẽ biểu tượng bộ cộng '+' hình tròn
                    painter.setBrush(QColor("#ffffff"))
                    painter.setPen(QPen(QColor("#252525"), 1.4))
                    painter.drawEllipse(QPointF(center_x, mid_y), 7.5, 7.5)
                    painter.setFont(QFont("Arial", 11, QFont.Weight.Bold))
                    painter.setPen(QColor("#111111"))
                    painter.drawText(QRectF(center_x - 8, mid_y - 8, 16, 16), Qt.AlignmentFlag.AlignCenter, "+")
                else:
                    # Các nhóm phát/thu: Quy trình xử lý tuần tự, vẽ đường nối kèm mũi tên hướng xuống
                    painter.setBrush(QColor("#333333"))
                    painter.setPen(QPen(QColor("#333333"), 1.4))
                    painter.drawLine(QPointF(center_x, first_bottom + 1), QPointF(center_x, next_top - 5))
                    painter.drawPolygon(QPolygonF([
                        QPointF(center_x - 4, next_top - 7),
                        QPointF(center_x + 4, next_top - 7),
                        QPointF(center_x, next_top - 2),
                    ]))

    def toggle(self):
        """Mở rộng hoặc thu gọn các khối con bên trong."""
        self.prepareGeometryChange()
        self.expanded = not self.expanded

        for index, child in enumerate(self.children):
            child.setVisible(self.expanded)
            child.setPos(14, 68 + index * 86)

        self.update()
        self.geometry_changed.emit()

    def set_expanded(self, expanded: bool):
        if self.expanded != expanded:
            self.toggle()

    def mousePressEvent(self, event):
        self.toggle()
        event.accept()


class DiagramScene(QGraphicsScene):
    """Không gian đồ họa chứa toàn bộ sơ đồ hệ thống viễn thông."""
    node_selected = Signal(str)

    def __init__(self):
        super().__init__()
        self.setBackgroundBrush(QColor("#ffffff"))
        self.groups: list[GroupItem] = []
        self.edges = []

        for model in LEVEL0_GRAPH:
            item = GroupItem(model)
            item.geometry_changed.connect(self.relayout)
            item.child_selected.connect(self.node_selected)
            self.addItem(item)
            self.groups.append(item)

        self.relayout()

    def update_config(self, config: dict, ber_text: str = ""):
        """
        Cập nhật trực tiếp thông số viễn thông lên từng khối:
        - Source: Số bit phát hoặc chuỗi Text
        - Bit framing: Số bit / symbol (1, 2, hoặc 4)
        - M-QAM mapper: Chuẩn điều chế (BPSK, QPSK, 16-QAM)
        - Channel: Mức nhiễu AWGN theo Eb/N0 (dB)
        - Soft detector: Chuẩn giải điều chế tương ứng
        - Metrics: Tỉ lệ lỗi bit BER và số bit lỗi
        """
        source_mode = config.get("sourceMode", "Random bits")
        text_payload = config.get("text", "")
        num_bits = config.get("numBits", 20000)
        modulation = config.get("modulation", "QPSK")
        ebno_db = config.get("ebnoDb", 8.0)
        seed = config.get("seed", 42)

        # Xác định số bit trên mỗi symbol theo lý thuyết thông tin số
        if modulation == "BPSK":
            bits_per_symbol = 1
        elif modulation == "QPSK":
            bits_per_symbol = 2
        elif modulation == "16-QAM":
            bits_per_symbol = 4
        else:
            bits_per_symbol = 2

        # Duyệt qua các khối và cập nhật nội dung
        for group in self.groups:
            for child in group.children:
                node_id = child.model.node_id

                if node_id == "source":
                    if source_mode == "Random bits":
                        child.subtitle = f"{num_bits:,} bits (seed {seed})"
                    else:
                        child.subtitle = f"Text: \"{text_payload}\""

                elif node_id == "group":
                    child.subtitle = f"Framing: {bits_per_symbol} bits/sym ({modulation})"

                elif node_id == "mapper":
                    child.subtitle = f"Modulation: {modulation}"

                elif node_id == "channel":
                    child.subtitle = f"AWGN (Eb/N0 = {ebno_db:.1f} dB)"

                elif node_id == "detector":
                    child.subtitle = f"Demodulator: {modulation}"

                elif node_id == "sink":
                    if ber_text != "":
                        child.subtitle = ber_text

                child.update()

    def relayout(self):
        """Bố trí vị trí các khối và vẽ đường truyền tín hiệu nối giữa các khối."""
        for edge in self.edges:
            self.removeItem(edge)
        self.edges.clear()

        top_groups = self.groups[:-1]
        adaptation = self.groups[-1]
        gap = 62.0
        x = 30.0
        top_y = 35.0

        for item in top_groups:
            item.setPos(x, top_y)
            x += item.width + gap

        top_height = max(item.height for item in top_groups)
        adaptation.setPos(30 + 3.3 * (236 + gap), top_y + top_height + 135)

        # Nhãn loại tín hiệu truyền giữa các tầng
        flow_labels = ["bits", "coded bits", "IQ / grid", "samples", "LLRs", "decoded bits"]
        for index, (left, right) in enumerate(zip(top_groups, top_groups[1:])):
            start = left.pos() + QPointF(left.width, 38)
            end = right.pos() + QPointF(0, 38)
            self._add_edge(start, end, flow_labels[index], "right")

        # Đường phản hồi CSI / CQI từ bên thu về thích nghi
        receiver = self.groups[4]
        tx_coding = self.groups[1]
        start = receiver.pos() + QPointF(receiver.width / 2, receiver.height)
        end = adaptation.pos() + QPointF(adaptation.width / 2, 0)
        self._add_edge(start, end, "CSI / CQI / ACK", "down", curved=True)

        # Đường điều khiển thích nghi MCS về bên phát
        start = adaptation.pos() + QPointF(0, adaptation.height / 2)
        end = tx_coding.pos() + QPointF(tx_coding.width / 2, tx_coding.height)
        self._add_edge(start, end, "MCS / iterations", "up", curved=True)

        scene_height = adaptation.pos().y() + adaptation.height + 70
        self.setSceneRect(0, 0, max(2200.0, x + 20), max(650.0, scene_height))

    def _add_edge(self, start: QPointF, end: QPointF, label: str, direction: str, curved=False):
        """Vẽ đường nối mũi tên kèm nhãn tín hiệu."""
        path = QPainterPath(start)
        if curved:
            mid_y = (start.y() + end.y()) / 2
            path.cubicTo(start.x(), mid_y, end.x(), mid_y, end.x(), end.y())
        else:
            path.lineTo(end)

        edge = QGraphicsPathItem(path)
        edge.setPen(QPen(QColor("#252525"), 1.6))
        edge.setZValue(-2)
        self.addItem(edge)
        self.edges.append(edge)

        # Đầu mũi tên
        if direction == "right":
            points = [end, QPointF(end.x()-10, end.y()-5), QPointF(end.x()-10, end.y()+5)]
        elif direction == "down":
            points = [end, QPointF(end.x()-5, end.y()-10), QPointF(end.x()+5, end.y()-10)]
        else:
            points = [end, QPointF(end.x()-5, end.y()+10), QPointF(end.x()+5, end.y()+10)]

        arrow = self.addPolygon(QPolygonF(points), QPen(QColor("#252525")), QColor("#252525"))
        arrow.setZValue(-1)
        self.edges.append(arrow)

        # Chữ mô tả luồng dữ liệu (bits, samples, LLRs,...)
        text = self.addSimpleText(label, QFont("Arial", 8))
        text.setBrush(QColor("#444444"))
        midpoint = path.pointAtPercent(0.5)
        text.setPos(midpoint.x() - text.boundingRect().width()/2, midpoint.y() - 20)
        text.setZValue(-1)
        self.edges.append(text)


class DiagramView(QGraphicsView):
    """Khung nhìn hỗ trợ tương tác chuột: cuộn phóng to/thu nhỏ và kéo xem sơ đồ."""
    def __init__(self, scene: DiagramScene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.setMinimumHeight(330)

    def wheelEvent(self, event: QWheelEvent):
        """Phóng to hoặc thu nhỏ khi cuộn bánh xe chuột."""
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        current_zoom = self.transform().m11()
        if 0.28 <= current_zoom * factor <= 3.5:
            self.scale(factor, factor)

    def fit_graph(self):
        """Căn chỉnh toàn bộ sơ đồ vừa vặn trong cửa sổ."""
        bounding_rect = self.scene().itemsBoundingRect().adjusted(-30, -30, 30, 30)
        self.fitInView(bounding_rect, Qt.AspectRatioMode.KeepAspectRatio)
