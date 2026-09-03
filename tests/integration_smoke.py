from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QObject, QTimer, Slot
from PySide6.QtWidgets import QApplication

from phy_workbench.main_window import MainWindow


app = QApplication([])
window = MainWindow()
window.show()


class Controller(QObject):
    @Slot(dict)
    def after_run(self, summary):
        window.scene.groups[3].set_expanded(True)
        window.inspect_node("channel")
        window.plot_current_node()

    @Slot(str)
    def after_plot(self, node_id):
        assert node_id == "channel"
        window.grab().save("integration_preview.png")
        window.close()

    @Slot(str)
    def failed(self, message):
        print(message, flush=True)
        app.exit(2)


controller = Controller()
window.worker.run_complete.connect(controller.after_run)
window.worker.native_figure_opened.connect(controller.after_plot)
window.worker.failed.connect(controller.failed)
QTimer.singleShot(180_000, lambda: (window.close(), app.quit()))
raise SystemExit(app.exec())
